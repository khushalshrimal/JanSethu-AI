import unittest
from datetime import date, time, timedelta, datetime
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models import (
    User, PatientProfile, Facility, Department, Doctor, DoctorAvailability,
    DoctorScheduleException, Appointment, SMSNotification, AppointmentAuditLog,
    UserRole, FacilityType, Language, AppointmentStatus, BookingChannel, NotificationStatus
)
from app.services.appointment_service import AppointmentService
from app.services.notification_service import NotificationService
from app.schemas.appointment import (
    AppointmentCreate, AppointmentCancelRequest, AppointmentRescheduleRequest
)
from app.utils.timezone import get_ist_now
from fastapi import HTTPException, status

from scripts.seed import seed_database

class TestPhase4Appointments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.db: Session = SessionLocal()
        # Clean test-specific entities using explicit ID filtering to preserve main seed database
        test_user_ids = [u.id for u in self.db.query(User).filter(User.email.like("%@test.com")).all()]
        if test_user_ids:
            self.db.query(SMSNotification).filter(SMSNotification.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            self.db.query(AppointmentAuditLog).filter(AppointmentAuditLog.actor_id.in_(test_user_ids)).delete(synchronize_session=False)
            self.db.query(PatientProfile).filter(PatientProfile.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            self.db.query(User).filter(User.id.in_(test_user_ids)).delete(synchronize_session=False)

        test_fac_ids = [f.id for f in self.db.query(Facility).filter(Facility.name == "Test City Hospital").all()]
        if test_fac_ids:
            self.db.query(Appointment).filter(Appointment.facility_id.in_(test_fac_ids)).delete(synchronize_session=False)
            test_doc_ids = [d.id for d in self.db.query(Doctor).filter(Doctor.facility_id.in_(test_fac_ids)).all()]
            if test_doc_ids:
                self.db.query(DoctorScheduleException).filter(DoctorScheduleException.doctor_id.in_(test_doc_ids)).delete(synchronize_session=False)
                self.db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id.in_(test_doc_ids)).delete(synchronize_session=False)
                self.db.query(Doctor).filter(Doctor.id.in_(test_doc_ids)).delete(synchronize_session=False)
            self.db.query(Department).filter(Department.facility_id.in_(test_fac_ids)).delete(synchronize_session=False)
            self.db.query(Facility).filter(Facility.id.in_(test_fac_ids)).delete(synchronize_session=False)
        self.db.commit()

        # Seed Test Core Entities
        self.admin = User(
            name="Admin User", phone_number="+91-9999900001", email="admin@test.com",
            password_hash=User.hash_password("Pass123!"), role=UserRole.ADMIN
        )
        self.db.add(self.admin)

        self.provider = User(
            name="Dr. Test Doctor", phone_number="+91-9999900002", email="doc@test.com",
            password_hash=User.hash_password("Pass123!"), role=UserRole.PROVIDER
        )
        self.db.add(self.provider)

        self.customer1 = User(
            name="Patient One", phone_number="+91-9888800001", email="p1@test.com",
            password_hash=User.hash_password("Pass123!"), role=UserRole.CUSTOMER
        )
        self.db.add(self.customer1)

        self.customer2 = User(
            name="Patient Two", phone_number="+91-9888800002", email="p2@test.com",
            password_hash=User.hash_password("Pass123!"), role=UserRole.CUSTOMER
        )
        self.db.add(self.customer2)
        self.db.flush()

        self.profile1 = PatientProfile(user_id=self.customer1.id, pincode="413106")
        self.profile2 = PatientProfile(user_id=self.customer2.id, pincode="413106")
        self.db.add_all([self.profile1, self.profile2])

        self.facility = Facility(
            name="Test City Hospital", facility_type=FacilityType.GOVERNMENT_HOSPITAL,
            description="Test Hospital", address="123 Street", village="Test Village",
            district="Test District", state="Maharashtra", pincode="413106",
            latitude=18.5, longitude=73.8, phone_number="+91-20-12345678", emergency_available=True, is_active=True
        )
        self.db.add(self.facility)
        self.db.flush()

        self.department = Department(facility_id=self.facility.id, name="General Medicine", description="Gen OPD")
        self.db.add(self.department)
        self.db.flush()

        self.doctor = Doctor(
            user_id=self.provider.id, facility_id=self.facility.id, department_id=self.department.id,
            name="Dr. Test Doctor", qualification="MBBS", specialization="Physician", is_active=True
        )
        self.db.add(self.doctor)
        self.db.flush()

        # Add 7-day schedule (09:00 - 13:00)
        for d in range(7):
            self.db.add(DoctorAvailability(
                doctor_id=self.doctor.id, day_of_week=d, start_time=time(9, 0), end_time=time(13, 0), slot_duration_minutes=30
            ))
        self.db.commit()

        # Target valid future test date
        self.valid_future_date = get_ist_now().date() + timedelta(days=15)

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    # --- 1. BOOKING SUCCESS & DB RECORDS ---
    def test_customer_books_available_slot_success(self):
        apt_in = AppointmentCreate(
            doctor_id=self.doctor.id,
            appointment_date=self.valid_future_date,
            start_time=time(10, 0),
            booking_channel=BookingChannel.PWA,
            reason_for_visit="Fever checkup"
        )
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(res.status, AppointmentStatus.BOOKED)
        self.assertTrue(res.confirmation_code.startswith("JS-2026-"))
        self.assertEqual(res.doctor.name, "Dr. Test Doctor")
        self.assertEqual(res.facility.name, "Test City Hospital")

        # Verify DB record
        db_apt = self.db.query(Appointment).filter(Appointment.id == res.id).first()
        self.assertIsNotNone(db_apt)
        self.assertEqual(db_apt.patient_id, self.profile1.id)

        # Verify Notification record
        sms = self.db.query(SMSNotification).filter(SMSNotification.appointment_id == res.id).first()
        self.assertIsNotNone(sms)
        self.assertEqual(sms.status, NotificationStatus.SENT)
        self.assertIn("JS-2026-", sms.message)

        # Verify Audit Log
        audit = self.db.query(AppointmentAuditLog).filter(
            AppointmentAuditLog.appointment_id == res.id,
            AppointmentAuditLog.event_type == "APPOINTMENT_CREATED"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.event_type, "APPOINTMENT_CREATED")

    # --- 2. DOUBLE BOOKING & TRANSACTION SAFETY ---
    def test_double_booking_returns_409_conflict(self):
        apt_in = AppointmentCreate(
            doctor_id=self.doctor.id,
            appointment_date=self.valid_future_date,
            start_time=time(10, 0)
        )
        res1 = AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(res1.status, AppointmentStatus.BOOKED)

        # Second booking attempt for same slot
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.book_appointment(self.db, apt_in, self.customer2)
        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ctx.exception.detail["code"], "SLOT_ALREADY_BOOKED")

    # --- 3. VALIDATION GUARDS ---
    def test_reject_past_date_booking(self):
        past_date = date(2020, 1, 1)
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=past_date, start_time=time(10, 0))
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "INVALID_APPOINTMENT_TIME")

    def test_reject_past_time_today(self):
        today_ist = get_ist_now().date()
        past_time = time(0, 1) # 00:01 AM is guaranteed past if tested during day
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=today_ist, start_time=past_time)
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "INVALID_APPOINTMENT_TIME")

    def test_reject_doctor_leave_exception(self):
        # Add Doctor Leave Exception
        self.db.add(DoctorScheduleException(
            doctor_id=self.doctor.id, date=self.valid_future_date, start_time=time(10, 0), end_time=time(12, 0),
            reason="Medical Conference Leave"
        ))
        self.db.commit()

        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 30))
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "DOCTOR_ON_LEAVE")

    def test_reject_inactive_doctor(self):
        self.doctor.is_active = False
        self.db.commit()
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "DOCTOR_INACTIVE")

    def test_reject_inactive_facility(self):
        self.facility.is_active = False
        self.db.commit()
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "FACILITY_INACTIVE")

    # --- 4. AUTHORIZATION CHECKS ---
    def test_customer_cannot_access_another_customer_appointment(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        # Customer 2 attempts to get Customer 1's appointment
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.get_appointment_by_id(self.db, res.id, self.customer2)
        self.assertEqual(ctx.exception.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ctx.exception.detail["code"], "UNAUTHORIZED_APPOINTMENT_ACCESS")

    def test_admin_can_access_any_appointment(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        admin_res = AppointmentService.get_appointment_by_id(self.db, res.id, self.admin)
        self.assertEqual(admin_res.id, res.id)

    # --- 5. CANCELLATION ENGINE & TRANSITION RULES ---
    def test_cancel_appointment_success(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        cancel_req = AppointmentCancelRequest(reason="Travel plans changed")
        cancel_res = AppointmentService.cancel_appointment(self.db, res.id, cancel_req, self.customer1)

        self.assertEqual(cancel_res.status, AppointmentStatus.CANCELLED)
        self.assertEqual(cancel_res.cancellation_reason, "Travel plans changed")

        # Verify audit log recorded
        audits = self.db.query(AppointmentAuditLog).filter(
            AppointmentAuditLog.appointment_id == res.id, AppointmentAuditLog.event_type == "APPOINTMENT_CANCELLED"
        ).all()
        self.assertTrue(len(audits) > 0)

    def test_cannot_cancel_appointment_twice(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(), self.customer1)
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(), self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "APPOINTMENT_ALREADY_CANCELLED")

    def test_cannot_cancel_completed_appointment(self):
        db_apt = Appointment(
            patient_id=self.profile1.id, doctor_id=self.doctor.id, facility_id=self.facility.id,
            department_id=self.department.id, appointment_date=self.valid_future_date,
            start_time=time(9, 0), end_time=time(9, 30), status=AppointmentStatus.COMPLETED,
            confirmation_code="JS-2026-COMP1"
        )
        self.db.add(db_apt)
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.cancel_appointment(self.db, db_apt.id, AppointmentCancelRequest(), self.customer1)
        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.detail["code"], "APPOINTMENT_ALREADY_COMPLETED")

    # --- 6. RESCHEDULING ENGINE ---
    def test_reschedule_appointment_success(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        new_date = self.valid_future_date + timedelta(days=1)
        reschedule_req = AppointmentRescheduleRequest(new_date=new_date, new_start_time=time(11, 0), reason="Rescheduling to next day")

        resched_res = AppointmentService.reschedule_appointment(self.db, res.id, reschedule_req, self.customer1)
        self.assertEqual(resched_res.appointment_date, new_date)
        self.assertEqual(resched_res.start_time, time(11, 0))

        # Check Audit Log
        audits = self.db.query(AppointmentAuditLog).filter(
            AppointmentAuditLog.appointment_id == res.id, AppointmentAuditLog.event_type == "APPOINTMENT_RESCHEDULED"
        ).all()
        self.assertTrue(len(audits) > 0)
        self.assertIn("10:00:00", str(audits[0].metadata_json))

    def test_reschedule_to_booked_slot_fails(self):
        # Book slot A at 10:00
        res1 = AppointmentService.book_appointment(self.db, AppointmentCreate(
            doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0)
        ), self.customer1)

        # Book slot B at 10:30
        res2 = AppointmentService.book_appointment(self.db, AppointmentCreate(
            doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 30)
        ), self.customer2)

        # Attempt to reschedule res2 to occupied 10:00 slot
        resched_req = AppointmentRescheduleRequest(new_date=self.valid_future_date, new_start_time=time(10, 0))
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.reschedule_appointment(self.db, res2.id, resched_req, self.customer2)
        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ctx.exception.detail["code"], "SLOT_ALREADY_BOOKED")

    # --- 7. NOTIFICATION RESILIENCE ---
    def test_notification_failure_does_not_rollback_appointment(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))

        # Mock notification provider failure
        class FailingProvider(NotificationService.provider.__class__):
            def send_sms(self, phone_number: str, message: str):
                return False, "", "SMS Gateway Unavailable"

        original_provider = NotificationService.provider
        NotificationService.provider = FailingProvider()
        try:
            res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)
            self.assertEqual(res.status, AppointmentStatus.BOOKED)

            sms = self.db.query(SMSNotification).filter(SMSNotification.appointment_id == res.id).first()
            self.assertIsNotNone(sms)
            self.assertEqual(sms.status, NotificationStatus.FAILED)
            self.assertEqual(sms.failure_reason, "SMS Gateway Unavailable")
        finally:
            NotificationService.provider = original_provider

    # --- 8. CONFIRMATION LOOKUP & VIEWS ---
    def test_get_by_confirmation_code_success(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        code_res = AppointmentService.get_by_confirmation_code(self.db, res.confirmation_code, self.customer1)
        self.assertEqual(code_res.id, res.id)

    def test_get_by_confirmation_code_variations(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(11, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)
        raw_code = res.confirmation_code

        # Test lowercase & whitespace trimming
        res_lower = AppointmentService.get_by_confirmation_code(self.db, f"  {raw_code.lower()}  ")
        self.assertEqual(res_lower.id, res.id)

        # Test prefix variation JAN-REF-
        code_without_prefix = raw_code.replace("JS-", "")
        res_prefix = AppointmentService.get_by_confirmation_code(self.db, f"JAN-REF-{code_without_prefix}")
        self.assertEqual(res_prefix.id, res.id)

        # Test guest/unauthenticated lookup (current_user=None)
        res_guest = AppointmentService.get_by_confirmation_code(self.db, raw_code, current_user=None)
        self.assertEqual(res_guest.id, res.id)

    def test_provider_appointments_view(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        prov_queue = AppointmentService.get_provider_appointments(self.db, self.provider)
        self.assertEqual(len(prov_queue), 1)

    def test_admin_appointments_view_filters(self):
        apt_in = AppointmentCreate(doctor_id=self.doctor.id, appointment_date=self.valid_future_date, start_time=time(10, 0))
        res = AppointmentService.book_appointment(self.db, apt_in, self.customer1)

        admin_list = AppointmentService.get_admin_appointments(
            self.db, self.admin, confirmation_code=res.confirmation_code
        )
        self.assertEqual(len(admin_list), 1)
        self.assertEqual(admin_list[0].id, res.id)

if __name__ == "__main__":
    unittest.main()
