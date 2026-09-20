import unittest
import pytest
from datetime import datetime, date, timedelta, time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, engine
from app.models.user import User, PatientProfile
from app.models.facility import Facility, Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.telephony import SMSNotification
from app.models.enums import (
    UserRole, Language, BookingChannel, AppointmentStatus, NotificationStatus
)
from app.integrations.sms.models import SMSDeliveryStatus
from app.schemas.appointment import AppointmentCreate, AppointmentCancelRequest, AppointmentRescheduleRequest, SMSNotificationResponse
from app.services.appointment_service import AppointmentService
from app.services.notification_service import NotificationService
from app.integrations.sms.webhook_service import SMSWebhookService
from app.core.templates import render_notification_template, AppointmentNotificationContext
from app.core.security import create_access_token
from app.utils.timezone import get_today_ist
from scripts.seed import seed_database


class TestPhase19NotificationReliability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine.dispose()
        seed_database(force_reset=True)
        engine.dispose()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()
        self.admin_user = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        self.customer_user = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()
        self.provider_user = self.db.query(User).filter(User.role == UserRole.PROVIDER).first()

        self.patient = self.db.query(PatientProfile).filter(PatientProfile.user_id == self.customer_user.id).first()
        if not self.patient:
            self.patient = self.db.query(PatientProfile).first()

        self.facility = self.db.query(Facility).first()
        self.department = self.db.query(Department).filter(Department.facility_id == self.facility.id).first()
        self.doctor = self.db.query(Doctor).filter(Doctor.facility_id == self.facility.id).first()

        self.admin_headers = {"Authorization": f"Bearer {create_access_token(self.admin_user.id)}"}
        self.customer_headers = {"Authorization": f"Bearer {create_access_token(self.customer_user.id)}"}

    def tearDown(self):
        self.db.close()

    # ----------------------------------------------------
    # 1. Lifecycle & Non-blocking SMS Dispatch
    # ----------------------------------------------------
    def test_01_appointment_created_triggers_queued_notification(self):
        target_date = get_today_ist() + timedelta(days=2)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)
        self.assertIsNotNone(resp)

        # Verify SMS notification record created
        notif = self.db.query(SMSNotification).filter(
            SMSNotification.appointment_id == resp.id
        ).order_by(SMSNotification.id.desc()).first()

        self.assertIsNotNone(notif)
        self.assertIn(notif.status, [NotificationStatus.QUEUED, NotificationStatus.SENDING, NotificationStatus.SENT, NotificationStatus.DELIVERED])
        self.assertIn(notif.event_type, ["BOOKING", "BOOKING_CONFIRMATION"])

    def test_02_appointment_creation_succeeds_when_sms_provider_fails(self):
        target_date = get_today_ist() + timedelta(days=3)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(11, 0),
            end_time=time(11, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )

        with patch.object(NotificationService.provider, "send_sms", side_effect=Exception("SMS Gateway Unreachable 503")):
            resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        self.assertIsNotNone(resp)
        self.assertIn(resp.status, [AppointmentStatus.BOOKED, AppointmentStatus.BOOKED.value, AppointmentStatus.CONFIRMED, AppointmentStatus.CONFIRMED.value])

    def test_03_appointment_cancelled_triggers_cancellation_notification(self):
        target_date = get_today_ist() + timedelta(days=4)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(14, 0),
            end_time=time(14, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        cancel_req = AppointmentCancelRequest(reason="Change of plans")
        cancelled = AppointmentService.cancel_appointment(self.db, resp.id, cancel_req, self.customer_user)
        self.assertEqual(cancelled.status, AppointmentStatus.CANCELLED.value)

        notif = self.db.query(SMSNotification).filter(
            SMSNotification.appointment_id == resp.id,
            SMSNotification.event_type == "CANCELLATION"
        ).first()
        self.assertIsNotNone(notif)

    def test_04_appointment_rescheduled_triggers_updated_notification(self):
        target_date = get_today_ist() + timedelta(days=5)
        new_date = target_date + timedelta(days=1)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(15, 0),
            end_time=time(15, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        resched_req = AppointmentRescheduleRequest(
            new_date=new_date,
            new_start_time=time(16, 0),
            new_end_time=time(16, 30),
            reason="Rescheduling to next day"
        )
        rescheduled = AppointmentService.reschedule_appointment(self.db, resp.id, resched_req, self.customer_user)
        self.assertEqual(rescheduled.appointment_date, new_date)

        notif = self.db.query(SMSNotification).filter(
            SMSNotification.appointment_id == resp.id,
            SMSNotification.event_type == "RESCHEDULE"
        ).first()
        self.assertIsNotNone(notif)

    def test_05_sms_failure_does_not_rollback_reschedule(self):
        target_date = get_today_ist() + timedelta(days=6)
        new_date = target_date + timedelta(days=1)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        resched_req = AppointmentRescheduleRequest(
            new_date=new_date,
            new_start_time=time(10, 0),
            new_end_time=time(10, 30),
            reason="Work conflict"
        )

        with patch.object(NotificationService.provider, "send_sms", side_effect=Exception("Network Timeout")):
            rescheduled = AppointmentService.reschedule_appointment(self.db, resp.id, resched_req, self.customer_user)

        self.assertEqual(rescheduled.appointment_date, new_date)

    def test_06_sms_failure_does_not_rollback_cancellation(self):
        target_date = get_today_ist() + timedelta(days=8)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        cancel_req = AppointmentCancelRequest(reason="Not feeling well")

        with patch.object(NotificationService.provider, "send_sms", side_effect=Exception("SMS Service Outage")):
            cancelled = AppointmentService.cancel_appointment(self.db, resp.id, cancel_req, self.customer_user)

        self.assertEqual(cancelled.status, AppointmentStatus.CANCELLED.value)

    # ----------------------------------------------------
    # 2. Notification Statuses & Data Representation
    # ----------------------------------------------------
    def test_07_notification_status_enum_values(self):
        expected_statuses = {"QUEUED", "PENDING", "SENDING", "SENT", "DELIVERED", "FAILED", "RETRYING"}
        actual_statuses = {s.value for s in NotificationStatus}
        self.assertTrue(expected_statuses.issubset(actual_statuses))

    def test_08_sms_delivery_status_enum_values(self):
        expected_delivery = {"QUEUED", "SENDING", "SENT", "SENT_SIMULATED", "DELIVERED", "FAILED", "RETRYING", "REJECTED"}
        actual_delivery = {s.value for s in SMSDeliveryStatus}
        self.assertTrue(expected_delivery.issubset(actual_delivery))

    def test_09_sms_notification_schema_includes_phase19_fields(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Test message",
            status=NotificationStatus.SENT,
            provider="development",
            event_type="BOOKING",
            attempt_count=1,
            last_attempt_at=datetime.utcnow(),
            delivered_at=None
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        schema = SMSNotificationResponse.model_validate(notif)
        self.assertEqual(schema.event_type, "BOOKING")
        self.assertEqual(schema.attempt_count, 1)
        self.assertIsNotNone(schema.last_attempt_at)
        self.assertIsNone(schema.delivered_at)

    def test_10_attempt_count_increments_on_retry(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Test retry message",
            status=NotificationStatus.FAILED,
            provider="development",
            event_type="BOOKING",
            attempt_count=1,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=10)
        )
        self.db.add(notif)
        self.db.commit()

        restarted = NotificationService.retry_failed_sms(self.db, max_attempts=3)
        self.assertGreaterEqual(len(restarted), 1)

        self.db.refresh(notif)
        self.assertEqual(notif.attempt_count, 2)

    def test_11_delivered_at_set_only_on_delivery(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Delivery test",
            status=NotificationStatus.SENT,
            provider="development",
            provider_message_id="msg_deliv_123",
            event_type="BOOKING",
            attempt_count=1
        )
        self.db.add(notif)
        self.db.commit()

        self.assertIsNone(notif.delivered_at)

        # Process delivery webhook
        SMSWebhookService.process_status_callback(
            self.db,
            provider_message_id="msg_deliv_123",
            status_str="DELIVERED"
        )

        self.db.refresh(notif)
        self.assertEqual(notif.status, NotificationStatus.DELIVERED)
        self.assertIsNotNone(notif.delivered_at)

    # ----------------------------------------------------
    # 3. Multi-Language Template Engine
    # ----------------------------------------------------
    def test_12_template_rendering_hindi(self):
        ctx = AppointmentNotificationContext(
            appointment_id=101,
            patient_name="Rahul Kumar",
            doctor_name="Dr. Sharma",
            facility_name="Civil Hospital Baramati",
            department_name="General Medicine",
            appointment_date="2026-09-25",
            start_time="10:00",
            confirmation_code="CONF1234",
            language=Language.HI
        )
        text = render_notification_template("APPOINTMENT_CONFIRMED", ctx)
        self.assertIn("CONF1234", text)
        self.assertIn("Dr. Sharma", text)
        self.assertIn("Civil Hospital Baramati", text)
        self.assertIn("Appointment Confirmed", text)

    def test_13_template_rendering_marathi(self):
        ctx = AppointmentNotificationContext(
            appointment_id=102,
            patient_name="Rahul Kumar",
            doctor_name="Dr. Sharma",
            facility_name="Civil Hospital Baramati",
            department_name="General Medicine",
            appointment_date="2026-09-25",
            start_time="10:00",
            confirmation_code="CONF1234",
            language=Language.MR
        )
        text = render_notification_template("APPOINTMENT_CONFIRMED", ctx)
        self.assertIn("CONF1234", text)
        self.assertIn("Dr. Sharma", text)

    def test_14_template_rendering_english(self):
        ctx = AppointmentNotificationContext(
            appointment_id=103,
            patient_name="Rahul Kumar",
            doctor_name="Dr. Sharma",
            facility_name="Civil Hospital Baramati",
            department_name="General Medicine",
            appointment_date="2026-09-25",
            start_time="10:00",
            confirmation_code="CONF1234",
            language=Language.EN
        )
        text = render_notification_template("APPOINTMENT_CONFIRMED", ctx)
        self.assertIn("CONF1234", text)
        self.assertIn("Appointment Confirmed", text)

    def test_15_template_rendering_cancellation(self):
        ctx = AppointmentNotificationContext(
            appointment_id=104,
            patient_name="Rahul Kumar",
            doctor_name="Dr. Sharma",
            facility_name="Civil Hospital Baramati",
            department_name="General Medicine",
            appointment_date="2026-09-25",
            start_time="10:00",
            confirmation_code="CONF1234",
            language=Language.HI
        )
        text = render_notification_template("APPOINTMENT_CANCELLED", ctx)
        self.assertIn("CONF1234", text)
        self.assertIn("Cancelled", text)

    def test_16_template_rendering_reschedule(self):
        ctx = AppointmentNotificationContext(
            appointment_id=105,
            patient_name="Rahul Kumar",
            doctor_name="Dr. Sharma",
            facility_name="Civil Hospital Baramati",
            department_name="General Medicine",
            appointment_date="2026-09-26",
            start_time="11:00",
            confirmation_code="CONF1234",
            language=Language.EN
        )
        text = render_notification_template("APPOINTMENT_RESCHEDULED", ctx)
        self.assertIn("CONF1234", text)
        self.assertIn("Rescheduled", text)

    def test_17_template_no_sensitive_data_exposure(self):
        ctx = AppointmentNotificationContext(
            appointment_id=106,
            patient_name="Rahul Kumar",
            doctor_name="Dr. Sharma",
            facility_name="Civil Hospital Baramati",
            department_name="General Medicine",
            appointment_date="2026-09-25",
            start_time="10:00",
            confirmation_code="CONF1234",
            language=Language.HI
        )
        text = render_notification_template("APPOINTMENT_CONFIRMED", ctx)
        self.assertNotIn("password", text.lower())
        self.assertNotIn("token", text.lower())
        self.assertNotIn("secret", text.lower())

    # ----------------------------------------------------
    # 4. 24-Hour Reminder Worker & Idempotency
    # ----------------------------------------------------
    def test_18_reminder_worker_finds_upcoming_appointments(self):
        tomorrow = get_today_ist() + timedelta(days=1)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        reminded_records = NotificationService.process_daily_reminders(self.db)
        self.assertGreaterEqual(len(reminded_records), 1)

        appt = self.db.query(Appointment).filter(Appointment.id == resp.id).first()
        self.assertIsNotNone(appt.reminder_sent_at)

    def test_19_reminder_worker_skips_past_appointments(self):
        past_date = get_today_ist() - timedelta(days=1)
        appt = Appointment(
            patient_id=self.patient.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            doctor_id=self.doctor.id,
            appointment_date=past_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            confirmation_code="PAST123",
            booking_channel=BookingChannel.PWA,
            status=AppointmentStatus.CONFIRMED
        )
        self.db.add(appt)
        self.db.commit()

        NotificationService.process_daily_reminders(self.db)
        self.db.refresh(appt)
        self.assertIsNone(appt.reminder_sent_at)

    def test_20_reminder_worker_skips_cancelled_appointments(self):
        tomorrow = get_today_ist() + timedelta(days=1)
        appt = Appointment(
            patient_id=self.patient.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            doctor_id=self.doctor.id,
            appointment_date=tomorrow,
            start_time=time(11, 0),
            end_time=time(11, 30),
            confirmation_code="CANC123",
            booking_channel=BookingChannel.PWA,
            status=AppointmentStatus.CANCELLED
        )
        self.db.add(appt)
        self.db.commit()

        NotificationService.process_daily_reminders(self.db)
        self.db.refresh(appt)
        self.assertIsNone(appt.reminder_sent_at)

    def test_21_reminder_worker_idempotent_no_duplicates(self):
        tomorrow = get_today_ist() + timedelta(days=1)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=tomorrow,
            start_time=time(12, 0),
            end_time=time(12, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        list1 = NotificationService.process_daily_reminders(self.db)
        self.assertGreaterEqual(len(list1), 1)

        # Second run should send 0 reminders for this appointment
        list2 = NotificationService.process_daily_reminders(self.db)
        rem_appts = [r.appointment_id for r in list2 if r.appointment_id == resp.id]
        self.assertEqual(len(rem_appts), 0)

    def test_22_reminder_worker_handles_sms_failure_gracefully(self):
        tomorrow = get_today_ist() + timedelta(days=1)
        req = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=tomorrow,
            start_time=time(13, 0),
            end_time=time(13, 30),
            booking_channel=BookingChannel.PWA,
            patient_id=self.patient.id
        )
        resp = AppointmentService.book_appointment(self.db, req, self.customer_user)

        with patch.object(NotificationService.provider, "send_sms", side_effect=Exception("Gateway error")):
            res_list = NotificationService.process_daily_reminders(self.db)

        # Should not raise exception
        self.assertIsInstance(res_list, list)

    # ----------------------------------------------------
    # 5. Webhook Processing & Out-of-Order Safety
    # ----------------------------------------------------
    def test_23_webhook_processes_delivery_receipt(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Delivery receipt test",
            status=NotificationStatus.SENT,
            provider="development",
            provider_message_id="msg_receipt_101",
            event_type="BOOKING",
            attempt_count=1
        )
        self.db.add(notif)
        self.db.commit()

        res = SMSWebhookService.process_status_callback(
            self.db,
            provider_message_id="msg_receipt_101",
            status_str="DELIVERED"
        )

        self.assertIsNotNone(res)
        self.db.refresh(notif)
        self.assertEqual(notif.status, NotificationStatus.DELIVERED)

    def test_24_webhook_processes_failure_receipt(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Failure receipt test",
            status=NotificationStatus.SENT,
            provider="development",
            provider_message_id="msg_fail_102",
            event_type="BOOKING",
            attempt_count=1
        )
        self.db.add(notif)
        self.db.commit()

        res = SMSWebhookService.process_status_callback(
            self.db,
            provider_message_id="msg_fail_102",
            status_str="FAILED",
            error_message="Invalid Number"
        )

        self.assertIsNotNone(res)
        self.db.refresh(notif)
        self.assertEqual(notif.status, NotificationStatus.FAILED)

    def test_25_webhook_out_of_order_protection_ignores_sent_after_delivered(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Out of order test",
            status=NotificationStatus.DELIVERED,
            provider="development",
            provider_message_id="msg_ooo_103",
            event_type="BOOKING",
            attempt_count=1,
            delivered_at=datetime.utcnow()
        )
        self.db.add(notif)
        self.db.commit()

        # Delayed SENT webhook received after DELIVERED
        res = SMSWebhookService.process_status_callback(
            self.db,
            provider_message_id="msg_ooo_103",
            status_str="SENT"
        )

        self.assertIsNotNone(res)
        self.db.refresh(notif)
        # Status should stay DELIVERED
        self.assertEqual(notif.status, NotificationStatus.DELIVERED)

    def test_26_webhook_deduplication(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Deduplication test",
            status=NotificationStatus.SENT,
            provider="development",
            provider_message_id="msg_dedup_104",
            event_type="BOOKING",
            attempt_count=1
        )
        self.db.add(notif)
        self.db.commit()

        # First callback
        SMSWebhookService.process_status_callback(self.db, provider_message_id="msg_dedup_104", status_str="DELIVERED")
        # Duplicate callback
        res2 = SMSWebhookService.process_status_callback(self.db, provider_message_id="msg_dedup_104", status_str="DELIVERED")

        self.assertEqual(res2.get("status"), "ALREADY_PROCESSED")
        self.db.refresh(notif)
        self.assertEqual(notif.status, NotificationStatus.DELIVERED)

    def test_27_webhook_unknown_message_id(self):
        # Process status callback with fallback to latest SMS record
        res = SMSWebhookService.process_status_callback(
            self.db,
            provider_message_id="msg_unknown_999",
            status_str="DELIVERED"
        )
        self.assertIsNotNone(res)

    # ----------------------------------------------------
    # 6. Retry Engine
    # ----------------------------------------------------
    def test_28_retry_engine_retries_failed_messages(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Retry test 1",
            status=NotificationStatus.FAILED,
            provider="development",
            event_type="BOOKING",
            attempt_count=1,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=15)
        )
        self.db.add(notif)
        self.db.commit()

        restarted = NotificationService.retry_failed_sms(self.db, max_attempts=3)
        self.assertGreaterEqual(len(restarted), 1)

        self.db.refresh(notif)
        self.assertIn(notif.status, [NotificationStatus.SENDING, NotificationStatus.SENT, NotificationStatus.DELIVERED])
        self.assertEqual(notif.attempt_count, 2)

    def test_29_retry_engine_skips_already_delivered(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Delivered test",
            status=NotificationStatus.DELIVERED,
            provider="development",
            event_type="BOOKING",
            attempt_count=1
        )
        self.db.add(notif)
        self.db.commit()

        # Retry should skip DELIVERED messages
        NotificationService.retry_failed_sms(self.db, max_attempts=3)

        self.db.refresh(notif)
        self.assertEqual(notif.status, NotificationStatus.DELIVERED)
        self.assertEqual(notif.attempt_count, 1)

    def test_30_retry_engine_respects_max_attempts(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Max attempts test",
            status=NotificationStatus.FAILED,
            provider="development",
            event_type="BOOKING",
            attempt_count=3,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=15)
        )
        self.db.add(notif)
        self.db.commit()

        NotificationService.retry_failed_sms(self.db, max_attempts=3)

        self.db.refresh(notif)
        # Should stay at attempt_count 3 and FAILED
        self.assertEqual(notif.attempt_count, 3)
        self.assertEqual(notif.status, NotificationStatus.FAILED)

    def test_31_retry_engine_marks_retrying_then_sent_or_failed(self):
        notif = SMSNotification(
            phone_number="+919876543210",
            message="Status cycle test",
            status=NotificationStatus.FAILED,
            provider="development",
            event_type="BOOKING",
            attempt_count=1,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=15)
        )
        self.db.add(notif)
        self.db.commit()

        NotificationService.retry_failed_sms(self.db, max_attempts=3)

        self.db.refresh(notif)
        # Final status after retry completes
        self.assertIn(notif.status, [NotificationStatus.SENDING, NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.FAILED])

    def test_32_retry_engine_multiple_failed_messages_processed(self):
        n1 = SMSNotification(
            phone_number="+919876543211",
            message="Batch retry 1",
            status=NotificationStatus.FAILED,
            provider="development",
            event_type="BOOKING",
            attempt_count=1,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=20)
        )
        n2 = SMSNotification(
            phone_number="+919876543212",
            message="Batch retry 2",
            status=NotificationStatus.FAILED,
            provider="development",
            event_type="BOOKING",
            attempt_count=2,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=20)
        )
        self.db.add_all([n1, n2])
        self.db.commit()

        restarted = NotificationService.retry_failed_sms(self.db, max_attempts=3)
        self.assertGreaterEqual(len(restarted), 2)
