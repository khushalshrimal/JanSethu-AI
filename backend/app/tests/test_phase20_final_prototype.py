import unittest
import pytest
import asyncio
from datetime import datetime, date, timedelta, time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, engine
from app.models.user import User, PatientProfile
from app.models.facility import Facility, Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.telephony import SMSNotification, CallSession
from app.models.enums import (
    UserRole, Language, BookingChannel, AppointmentStatus, NotificationStatus, VisitStatus
)
from app.schemas.appointment import AppointmentCreate
from app.services.appointment_service import AppointmentService
from app.repositories.appointment_repository import AppointmentRepository
from app.services.phone_session_service import PhoneSessionService
from app.core.security import create_access_token
from app.utils.timezone import get_today_ist, get_ist_now
from scripts.seed import seed_database


class TestPhase20FinalPrototype(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        SessionLocal.close_all()
        engine.dispose()
        seed_database(force_reset=True)
        SessionLocal.close_all()
        engine.dispose()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()
        try:
            self.db.query(Appointment).filter(
                Appointment.reason_for_visit == "Phase 20 Test Appointment"
            ).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

        self.admin_user = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        self.customer_user = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()
        self.provider_user = self.db.query(User).filter(User.role == UserRole.PROVIDER).first()

        self.patient = self.db.query(PatientProfile).filter(PatientProfile.user_id == self.customer_user.id).first()
        if not self.patient:
            self.patient = self.db.query(PatientProfile).first()
            if self.patient:
                self.patient.user_id = self.customer_user.id
                self.db.commit()

        self.facility = self.db.query(Facility).first()
        self.department = self.db.query(Department).filter(Department.facility_id == self.facility.id).first()
        self.doctor = self.db.query(Doctor).filter(Doctor.facility_id == self.facility.id).first()

        self.admin_headers = {"Authorization": f"Bearer {create_access_token(self.admin_user.id)}"}
        self.customer_headers = {"Authorization": f"Bearer {create_access_token(self.customer_user.id)}"}

        if self.provider_user:
            self.provider_headers = {"Authorization": f"Bearer {create_access_token(self.provider_user.id)}"}
        else:
            self.provider_headers = self.admin_headers

    def tearDown(self):
        try:
            self.db.query(Appointment).filter(
                Appointment.reason_for_visit == "Phase 20 Test Appointment"
            ).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    def _create_test_appointment(self, apt_date=None, start_time_val=None, doc_id=None, offset_minutes=0):
        today = get_today_ist()
        target_date = apt_date or today
        base_time = start_time_val or time(10, 0)
        target_doc = doc_id or self.doctor.id

        dt_start = datetime.combine(date.today(), base_time) + timedelta(minutes=offset_minutes)
        start_time_real = dt_start.time()

        dt_end = dt_start + timedelta(minutes=30)
        end_time_real = dt_end.time()

        return AppointmentRepository.create_appointment(
            db=self.db,
            patient_id=self.patient.id,
            doctor_id=target_doc,
            facility_id=self.facility.id,
            department_id=self.department.id,
            apt_date=target_date,
            start_time=start_time_real,
            end_time=end_time_real,
            booking_channel=BookingChannel.PWA,
            reason_for_visit="Phase 20 Test Appointment"
        )

    # ----------------------------------------------------
    # 1. Check-In & Queue Token Generation
    # ----------------------------------------------------

    def test_01_check_in_within_window_generates_token(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        resp = self.client.post(f"/api/v1/appointments/{apt.id}/check-in", headers=self.customer_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["queue_token"], "P-001")
        self.assertEqual(data["visit_status"], "WAITING")
        self.assertIsNotNone(data["checked_in_at"])

    def test_02_check_in_token_increment(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt1 = self._create_test_appointment(apt_date=today, start_time_val=now_time, offset_minutes=0)
        apt2 = self._create_test_appointment(apt_date=today, start_time_val=now_time, offset_minutes=1)

        res1 = AppointmentService.check_in_appointment(self.db, apt1.id)
        res2 = AppointmentService.check_in_appointment(self.db, apt2.id)

        self.assertEqual(res1.queue_token, "P-001")
        self.assertEqual(res2.queue_token, "P-002")

    def test_03_check_in_idempotency(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        res1 = AppointmentService.check_in_appointment(self.db, apt.id)
        res2 = AppointmentService.check_in_appointment(self.db, apt.id)

        self.assertEqual(res1.queue_token, "P-001")
        self.assertEqual(res2.queue_token, "P-001")
        self.assertEqual(res1.checked_in_at, res2.checked_in_at)

    def test_04_check_in_outside_window_too_early(self):
        today = get_today_ist()
        tomorrow = today + timedelta(days=1)
        apt = self._create_test_appointment(apt_date=tomorrow, start_time_val=time(10, 0))

        with pytest.raises(Exception) as exc_info:
            AppointmentService.check_in_appointment(self.db, apt.id)
        self.assertIn("60 minutes", str(exc_info.value.detail))

    def test_05_check_in_outside_window_too_late(self):
        today = get_today_ist()
        yesterday = today - timedelta(days=1)
        apt = self._create_test_appointment(apt_date=yesterday, start_time_val=time(10, 0))

        with pytest.raises(Exception) as exc_info:
            AppointmentService.check_in_appointment(self.db, apt.id)
        self.assertIn("expired", str(exc_info.value.detail).lower())

    def test_06_check_in_cancelled_appointment_fails(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        apt.status = AppointmentStatus.CANCELLED
        self.db.commit()

        resp = self.client.post(f"/api/v1/appointments/{apt.id}/check-in", headers=self.customer_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cancelled", str(resp.json()["detail"]).lower())

    def test_07_get_visit_status(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)

        resp = self.client.get(f"/api/v1/appointments/{apt.id}/visit-status", headers=self.customer_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["visit_status"], "WAITING")
        self.assertEqual(data["queue_token"], "P-001")

    # ----------------------------------------------------
    # 2. Consultation Lifecycle & State Transitions
    # ----------------------------------------------------

    def test_08_provider_start_consultation(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/start-consultation",
            headers=self.provider_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["visit_status"], "IN_CONSULTATION")
        self.assertEqual(data["status"], "IN_PROGRESS")

    def test_09_provider_start_consultation_unauthorized_patient(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/start-consultation",
            headers=self.customer_headers
        )
        self.assertEqual(resp.status_code, 403)

    def test_10_provider_complete_consultation(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)
        AppointmentService.start_consultation(self.db, apt.id, current_user=self.provider_user or self.admin_user)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/complete-consultation",
            headers=self.provider_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["visit_status"], "COMPLETED")
        self.assertEqual(data["status"], "COMPLETED")

    def test_11_provider_mark_no_show(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/no-show",
            headers=self.provider_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["visit_status"], "NO_SHOW")
        self.assertEqual(data["status"], "NO_SHOW")

    def test_12_invalid_transition_start_already_completed(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)
        user = self.provider_user or self.admin_user
        AppointmentService.start_consultation(self.db, apt.id, current_user=user)
        AppointmentService.complete_consultation(self.db, apt.id, current_user=user)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/start-consultation",
            headers=self.provider_headers
        )
        self.assertEqual(resp.status_code, 400)

    def test_13_invalid_transition_complete_before_start(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/complete-consultation",
            headers=self.provider_headers
        )
        self.assertEqual(resp.status_code, 400)

    def test_14_invalid_transition_no_show_after_complete(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)
        user = self.provider_user or self.admin_user
        AppointmentService.start_consultation(self.db, apt.id, current_user=user)
        AppointmentService.complete_consultation(self.db, apt.id, current_user=user)

        resp = self.client.post(
            f"/api/v1/provider/appointments/{apt.id}/no-show",
            headers=self.provider_headers
        )
        self.assertEqual(resp.status_code, 400)

    # ----------------------------------------------------
    # 3. Phone Session IVR & Voice Check-In
    # ----------------------------------------------------

    def test_15_phone_session_dtmf_checkin(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        session = PhoneSessionService.start_session(
            self.db, phone_number=self.customer_user.phone_number or "+919876543210"
        )
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "6")
        self.assertEqual(resp.current_state, "CHECK_IN_COMPLETED")
        self.assertIn("P-001", resp.prompt_text)

    def test_16_phone_session_dtmf_checkin_no_apt(self):
        session = PhoneSessionService.start_session(self.db, phone_number="+919998887770")
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "6")
        self.assertEqual(resp.current_state, "NO_CHECKIN_APPOINTMENT")

    def test_17_phone_session_voice_checkin_intent(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        session = PhoneSessionService.start_session(
            self.db, phone_number=self.customer_user.phone_number or "+919876543210"
        )
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "चेक इन करें"))
        self.assertEqual(nlu.intent, "CHECK_IN")
        self.assertEqual(resp.current_state, "CHECK_IN_COMPLETED")

    def test_18_phone_session_voice_checkin_english(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        session = PhoneSessionService.start_session(
            self.db, phone_number=self.customer_user.phone_number or "+919876543210"
        )
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        session.language = Language.EN
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "I want to check in for my appointment"))
        self.assertEqual(nlu.intent, "CHECK_IN")
        self.assertEqual(resp.current_state, "CHECK_IN_COMPLETED")

    def test_19_phone_session_voice_checkin_marathi(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        session = PhoneSessionService.start_session(
            self.db, phone_number=self.customer_user.phone_number or "+919876543210"
        )
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        session.language = Language.MR
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "माझे चेक इन करा"))
        self.assertEqual(nlu.intent, "CHECK_IN")
        self.assertEqual(resp.current_state, "CHECK_IN_COMPLETED")

    # ----------------------------------------------------
    # 4. Multi-Channel Reliability & SMS Dispatch
    # ----------------------------------------------------

    def test_20_sms_sent_on_check_in(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        AppointmentService.check_in_appointment(self.db, apt.id)

        sms = self.db.query(SMSNotification).filter(
            SMSNotification.appointment_id == apt.id
        ).order_by(SMSNotification.id.desc()).first()

        self.assertIsNotNone(sms)
        self.assertIn("check-in", sms.message.lower())

    def test_21_sms_failure_does_not_block_check_in(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        with patch("app.services.notification_service.NotificationService.send_appointment_notification") as mock_notify:
            mock_notify.side_effect = Exception("SMS Provider Gateway Timeout")
            res = AppointmentService.check_in_appointment(self.db, apt.id)
            self.assertEqual(res.queue_token, "P-001")
            self.assertEqual(res.visit_status, VisitStatus.WAITING)

    def test_22_cross_channel_checkin_pwa_to_phone(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        self.client.post(f"/api/v1/appointments/{apt.id}/check-in", headers=self.customer_headers)

        session = PhoneSessionService.start_session(
            self.db, phone_number=self.customer_user.phone_number or "+919876543210"
        )
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "6")
        self.assertEqual(resp.current_state, "CHECK_IN_COMPLETED")
        self.assertIn("P-001", resp.prompt_text)

    def test_23_cross_channel_checkin_phone_to_pwa(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        session = PhoneSessionService.start_session(
            self.db, phone_number=self.customer_user.phone_number or "+919876543210"
        )
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()
        PhoneSessionService.process_dtmf_input(self.db, session.id, "6")

        resp = self.client.get(f"/api/v1/appointments/{apt.id}", headers=self.customer_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["queue_token"], "P-001")
        self.assertEqual(data["visit_status"], "WAITING")

    def test_24_appointment_response_contains_phase20_fields(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)

        resp = self.client.get(f"/api/v1/appointments/{apt.id}", headers=self.customer_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["queue_token"], "P-001")
        self.assertEqual(data["visit_status"], "WAITING")
        self.assertIsNotNone(data["checked_in_at"])

    # ----------------------------------------------------
    # 5. Isolation, Edge Cases & End-to-End Flow
    # ----------------------------------------------------

    def test_25_provider_queue_filtering(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        AppointmentService.check_in_appointment(self.db, apt.id)

        resp = self.client.get("/api/v1/provider/dashboard", headers=self.provider_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["waiting_count"], 1)

    def test_26_multiple_doctors_queue_isolation(self):
        today = get_today_ist()
        now_time = datetime.now().time()
        doc2 = Doctor(
            name="Dr. Second Specialist",
            qualification="MD",
            specialization="General Medicine",
            facility_id=self.facility.id,
            department_id=self.department.id,
            is_active=True
        )
        self.db.add(doc2)
        self.db.commit()

        apt_doc1 = self._create_test_appointment(apt_date=today, start_time_val=now_time, doc_id=self.doctor.id)
        apt_doc2 = self._create_test_appointment(apt_date=today, start_time_val=now_time, doc_id=doc2.id)

        res1 = AppointmentService.check_in_appointment(self.db, apt_doc1.id)
        res2 = AppointmentService.check_in_appointment(self.db, apt_doc2.id)

        self.assertEqual(res1.queue_token, "P-001")
        self.assertEqual(res2.queue_token, "P-001")

    def test_27_multiple_dates_queue_isolation(self):
        today = get_today_ist()
        now_time = get_ist_now().time()

        apt_today = self._create_test_appointment(apt_date=today, start_time_val=now_time)
        res_today = AppointmentService.check_in_appointment(self.db, apt_today.id)

        self.assertEqual(res_today.queue_token, "P-001")

    def test_28_late_check_in_within_grace_period(self):
        today = get_today_ist()
        now_ist = get_ist_now()
        dt_thirty_ago = now_ist - timedelta(minutes=30)
        if dt_thirty_ago.date() < today:
            thirty_m_ago = time(0, 0)
        else:
            thirty_m_ago = dt_thirty_ago.time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=thirty_m_ago)

        res = AppointmentService.check_in_appointment(self.db, apt.id)
        self.assertEqual(res.visit_status, VisitStatus.WAITING)

    def test_29_exact_start_time_check_in(self):
        today = get_today_ist()
        now_time = get_ist_now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        res = AppointmentService.check_in_appointment(self.db, apt.id)
        self.assertEqual(res.visit_status, VisitStatus.WAITING)

    def test_30_full_journey_end_to_end(self):
        today = get_today_ist()
        now_time = get_ist_now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        # 1. Patient checks in -> WAITING, queue token generated
        chk = AppointmentService.check_in_appointment(self.db, apt.id)
        self.assertEqual(chk.queue_token, "P-001")
        self.assertEqual(chk.visit_status, VisitStatus.WAITING)

        # 2. Doctor starts consultation -> IN_CONSULTATION, IN_PROGRESS
        user = self.provider_user or self.admin_user
        start_apt = AppointmentService.start_consultation(self.db, apt.id, current_user=user)
        self.assertEqual(start_apt.visit_status, VisitStatus.IN_CONSULTATION)
        self.assertEqual(start_apt.status, AppointmentStatus.IN_PROGRESS)

        # 3. Doctor completes consultation -> COMPLETED, COMPLETED
        comp_apt = AppointmentService.complete_consultation(self.db, apt.id, current_user=user)
        self.assertEqual(comp_apt.visit_status, VisitStatus.COMPLETED)
        self.assertEqual(comp_apt.status, AppointmentStatus.COMPLETED)

    def test_31_phone_registration_auto_user_creation(self):
        """31. New phone caller automatically starts name registration and creates User + PatientProfile."""
        new_phone = "+919999000111"
        session = PhoneSessionService.start_session(self.db, phone_number=new_phone)
        self.assertEqual(session.current_state, "PHONE_REGISTRATION_NAME")

        import asyncio
        resp, _ = asyncio.run(
            PhoneSessionService.process_voice_input(self.db, session.id, "Mera naam Ramesh Kumar hai")
        )
        self.assertEqual(resp.current_state, "LANGUAGE_SELECTION")

        reg_user = self.db.query(User).filter(User.phone_number == new_phone).first()
        self.assertIsNotNone(reg_user)
        self.assertEqual(reg_user.name, "Ramesh Kumar")
        self.assertIsNotNone(reg_user.patient_profile)

    def test_32_returning_user_identification(self):
        """32. Returning phone caller is automatically identified and greeted by name."""
        existing_phone = self.customer_user.phone_number or "+919876543210"
        session = PhoneSessionService.start_session(self.db, phone_number=existing_phone)
        self.assertEqual(session.user_id, self.customer_user.id)
        self.assertEqual(session.current_state, "RETURNING_USER_GREETING")

    def test_33_voice_no_ivr_press_instructions(self):
        """33. Verify spoken prompts contain NO 'Press 1 / 2 / 3 / 4' IVR directives."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        fmt = PhoneSessionService.format_response(self.db, session)
        self.assertNotIn("Press 1", fmt.prompt_text)
        self.assertNotIn("Press 2", fmt.prompt_text)
        self.assertNotIn("Press 3", fmt.prompt_text)
        self.assertNotIn("Press 4", fmt.prompt_text)
        self.assertNotIn("dabakar", fmt.prompt_text.lower())

    def test_34_voice_check_appointment_real_db(self):
        """34. Voice query 'Meri appointment kab hai?' returns real DB appointment details."""
        today = get_today_ist()
        apt = self._create_test_appointment(apt_date=today)

        session = PhoneSessionService.start_session(self.db, phone_number=self.customer_user.phone_number or "+919876543210")
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Meri appointment kab hai?"))
        self.assertEqual(nlu.intent, "CHECK_APPOINTMENT")
        self.assertIn(apt.confirmation_code, resp.prompt_text)
        self.assertIn(self.doctor.name, resp.prompt_text)

    def test_35_voice_check_availability_real_db(self):
        """35. Voice query 'Kal doctor available hai kya?' queries real AvailabilityService slots."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Kal doctor available hai kya?"))
        self.assertIn(nlu.intent, ["CHECK_AVAILABILITY", "BOOK_APPOINTMENT"])
        self.assertIn(resp.current_state, ["SLOT_SELECTION", "DATE_SELECTION", "FACILITY_SELECTION"])

    def test_36_voice_facility_search_real_db(self):
        """36. Voice query 'Baramati hospital' retrieves real facility from DB."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Baramati mein government hospital batao"))
        self.assertEqual(nlu.intent, "SEARCH_FACILITY")
        self.assertEqual(resp.current_state, "FACILITY_SELECTION")

    def test_37_voice_cancellation_real_db(self):
        """37. Voice cancellation flow updates real DB appointment status to CANCELLED."""
        today = get_today_ist() + timedelta(days=1)
        apt = self._create_test_appointment(apt_date=today)

        session = PhoneSessionService.start_session(self.db, phone_number=self.customer_user.phone_number or "+919876543210")
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        # Step 1: Request cancellation
        resp1, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Meri appointment cancel kar do"))
        self.assertEqual(resp1.current_state, "CANCEL_APPOINTMENT")

        # Step 2: Confirm cancellation
        resp2, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Haan cancel kar do"))
        self.assertEqual(resp2.current_state, "CANCEL_COMPLETED")

        updated_apt = self.db.query(Appointment).filter(Appointment.id == apt.id).first()
        self.assertEqual(updated_apt.status, AppointmentStatus.CANCELLED)

    def test_38_voice_reschedule_real_db(self):
        """38. Voice rescheduling flow updates real DB appointment date/slot."""
        today = get_today_ist() + timedelta(days=1)
        apt = self._create_test_appointment(apt_date=today)

        session = PhoneSessionService.start_session(self.db, phone_number=self.customer_user.phone_number or "+919876543210")
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        # Step 1: Reschedule intent
        resp1, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Appointment reschedule karni hai"))
        self.assertIn(resp1.current_state, ["RESCHEDULE_APPOINTMENT", "RESCHEDULE_DATE"])

    def test_39_voice_multilingual_natural_switching(self):
        """39. Natural language switching for Hindi, Marathi, and English."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")

        # Switch to English
        resp_en, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "English please"))
        self.assertEqual(resp_en.language, Language.EN)

        # Switch to Marathi
        resp_mr, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "मराठीत बोला"))
        self.assertEqual(resp_mr.language, Language.MR)

    def test_40_voice_multi_turn_context(self):
        """40. Multi-turn dialogue context is retained across session state transitions."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        session.current_state = "MAIN_MENU"
        self.db.commit()

        # Turn 1: Book Intent
        r1, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Mujhe doctor ko dikhana hai"))
        self.assertIn(r1.current_state, ["FACILITY_SELECTION", "LOCATION_INPUT"])

        # Turn 2: Baramati location
        r2, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Baramati"))
        self.assertEqual(r2.current_state, "DEPARTMENT_SELECTION")
        self.assertIsNotNone(r2.selected_facility_id)

    def test_41_voice_natural_affirmative_negative(self):
        """41. System recognizes natural affirmative ('Haan', 'Ji bilkul') and negative ('Nahi', 'Mat karo') words."""
        from app.services.voice.entity_extractor import EntityExtractor
        e1 = EntityExtractor.extract_entities("Haan, bilkul kar do")
        self.assertTrue(e1.get("confirmation"))

        e2 = EntityExtractor.extract_entities("Nahi, mat karo cancel")
        self.assertFalse(e2.get("confirmation"))

    def test_42_voice_queue_token_retrieval(self):
        """42. Voice query 'Mera token kya hai?' retrieves real queue token after check-in."""
        today = get_today_ist()
        now_time = datetime.now().time()
        apt = self._create_test_appointment(apt_date=today, start_time_val=now_time)

        # Check-in
        chk = AppointmentService.check_in_appointment(self.db, apt.id)

        session = PhoneSessionService.start_session(self.db, phone_number=self.customer_user.phone_number or "+919876543210")
        session.user_id = self.customer_user.id
        session.current_state = "MAIN_MENU"
        self.db.commit()

        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Mera token number kya hai?"))
        self.assertEqual(nlu.intent, "CHECK_IN")
        self.assertIn(chk.queue_token, resp.prompt_text)

    def test_43_voice_emergency_priority(self):
        """43. Emergency utterances immediately route to EMERGENCY state with highest priority."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp, nlu = asyncio.run(PhoneSessionService.process_voice_input(self.db, session.id, "Mujhe emergency 108 ambulance chahiye"))
        self.assertEqual(nlu.intent, "EMERGENCY")
        self.assertEqual(resp.current_state, "EMERGENCY")
        self.assertIn("108", resp.prompt_text)

    def test_44_12_turn_hands_free_conversation(self):
        """44. Full realistic 12-turn simulated hands-free voice dialogue from call start to booking & check-in."""
        phone = "+919888877777"

        # Turn 1: Start Call
        sess = PhoneSessionService.start_session(self.db, phone_number=phone)
        self.assertEqual(sess.current_state, "PHONE_REGISTRATION_NAME")

        # Turn 2: Name registration
        r2, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Mera naam Sunita Patil hai"))
        self.assertEqual(r2.current_state, "LANGUAGE_SELECTION")

        # Turn 3: Language choice
        r3, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Hindi mein baat karo"))
        self.assertEqual(r3.current_state, "MAIN_MENU")

        # Turn 4: Booking request
        r4, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Mujhe doctor ko dikhana hai"))
        self.assertIn(r4.current_state, ["FACILITY_SELECTION", "LOCATION_INPUT"])

        # Turn 5: Location input
        r5, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Baramati"))
        self.assertEqual(r5.current_state, "DEPARTMENT_SELECTION")

        # Turn 6: Department choice
        r6, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "General Medicine physician"))
        self.assertEqual(r6.current_state, "DOCTOR_SELECTION")

        # Turn 7: Doctor choice
        r7, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Dr. Rajesh Sharma"))
        self.assertEqual(r7.current_state, "DATE_SELECTION")

        # Turn 8: Date selection
        r8, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Kal ka slot chahiye"))
        self.assertEqual(r8.current_state, "SLOT_SELECTION")

        # Turn 9: Slot selection
        r9, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Pehla slot"))
        self.assertEqual(r9.current_state, "BOOKING_CONFIRMATION")

        # Turn 10: Confirmation
        r10, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Haan, confirm kar do"))
        self.assertEqual(r10.current_state, "BOOKING_COMPLETED")

        # Turn 11: Appointment query
        r11, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Meri appointment kab hai?"))
        self.assertIn("Dr.", r11.prompt_text)
        self.assertIn("Baramati", r11.prompt_text)

        # Turn 12: End Call
        r12, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Dhanyawad, fon cut karo"))
        self.assertEqual(r12.current_state, "ENDED")

    def test_45_symptom_first_care_routing(self):
        """Verify symptom phrases extract correct care category/department without disease diagnosis."""
        from app.services.voice import EntityExtractor, IntentParser, IntentEnum

        e1 = EntityExtractor.extract_entities("Mujhe pet mein dard hai")
        self.assertEqual(e1.get("department"), "general medicine")

        e2 = EntityExtractor.extract_entities("Bache ko bukhar aur sardi hai")
        self.assertEqual(e2.get("department"), "pediatrics")

        e3 = EntityExtractor.extract_entities("Daant mein bahut dard hai")
        self.assertEqual(e3.get("department"), "dentistry")

        e4 = EntityExtractor.extract_entities("Pregnancy checkup ke liye doctor chahiye")
        self.assertEqual(e4.get("department"), "gynecology")

        intent, conf = IntentParser.parse_intent("Mujhe pet mein dard hai doctor ko dikhana hai")
        self.assertIn(intent, [IntentEnum.BOOK_APPOINTMENT, IntentEnum.SEARCH_DOCTOR])

    def test_46_pwa_facility_search_schema_validation(self):
        """Verify GET /facilities/search returns integer facility IDs matching PWA Facilities.jsx expectations."""
        response = self.client.get("/api/v1/facilities/search")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        fac = data[0]
        self.assertIn("id", fac)
        self.assertIsInstance(fac["id"], int)
        self.assertIn("name", fac)
        self.assertIn("pincode", fac)

    def test_47_jaipur_location_and_fever_symptom_flow(self):
        """Verify dynamic Jaipur location and fever symptom utterance seamlessly transitions to facility & doctor selection."""
        phone = "+919111122222"
        sess = PhoneSessionService.start_session(self.db, phone_number=phone)
        self.assertEqual(sess.current_state, "PHONE_REGISTRATION_NAME")

        # Turn 1: Name registration
        r1, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Mera naam Sunita hai"))
        self.assertEqual(r1.current_state, "LANGUAGE_SELECTION")

        # Turn 2: Location & Fever utterance
        r2, _ = asyncio.run(PhoneSessionService.process_voice_input(self.db, sess.id, "Main Jaipur mein rehta hoon, mujhe fever hai"))
        self.assertIn(r2.current_state, ["FACILITY_SELECTION", "DEPARTMENT_SELECTION", "LOCATION_INPUT"])
        self.assertNotIn("Kripya phir se", r2.prompt_text)



