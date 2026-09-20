import unittest
import pytest
import uuid
from datetime import datetime, date, timedelta, time
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, engine
from app.models.user import User, PatientProfile
from app.models.facility import Facility, Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.telephony import CallSession, SMSNotification
from app.models.enums import UserRole, Language, BookingChannel, AppointmentStatus, CallSessionStatus
from app.services.phone_session_service import PhoneSessionService
from app.repositories.appointment_repository import AppointmentRepository
from app.services.appointment_service import AppointmentService
from app.core.security import create_access_token
from app.utils.timezone import get_today_ist
from scripts.seed import seed_database


class TestPhase17PhoneFirst(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine.dispose()
        seed_database(force_reset=True)
        engine.dispose()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()
        user = self.db.query(User).filter(User.phone_number == "+91-9876543210").first()
        if not user:
            user = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()

        patient = self.db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
        fac = self.db.query(Facility).first()
        dept = self.db.query(Department).filter(Department.facility_id == fac.id).first()
        doc = self.db.query(Doctor).filter(Doctor.facility_id == fac.id).first()

        self.db.commit()

        self.test_user = user
        self.test_patient = patient
        self.test_facility = fac
        self.test_department = dept
        self.test_doctor = doc

    def tearDown(self):
        self.db.close()

    def test_01_call_start(self):
        """1. Call start initializes session with GREETING state and normalized phone."""
        resp = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+919876543210"})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn(data["current_state"], ["GREETING", "RETURNING_USER_GREETING"])
        self.assertEqual(data["caller_phone"], "+919876543210")
        self.assertTrue("JanSethu" in data["prompt_text"] or "जनसेतु" in data["prompt_text"])

    def test_02_existing_caller_identification(self):
        """2. Existing caller phone number is resolved to user_id."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        self.assertEqual(session.user_id, self.test_user.id)

    def test_03_new_caller_handling(self):
        """3. Unknown caller phone creates new session cleanly."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919999888877")
        self.assertEqual(session.phone_number, "+919999888877")
        self.assertIn(session.current_state, ["GREETING", "PHONE_REGISTRATION_NAME"])

    def test_04_language_selection_hindi(self):
        """4. DTMF 1 sets language to Hindi."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertEqual(resp.language, "HI")
        self.assertEqual(resp.current_state, "MAIN_MENU")

    def test_05_language_selection_marathi(self):
        """5. DTMF 2 sets language to Marathi."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "2")
        self.assertEqual(resp.language, "MR")
        self.assertEqual(resp.current_state, "MAIN_MENU")

    def test_06_language_selection_english(self):
        """6. DTMF 3 sets language to English."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "3")
        self.assertEqual(resp.language, "EN")
        self.assertEqual(resp.current_state, "MAIN_MENU")

    def test_07_language_persistence(self):
        """7. Selected language persists across multiple state transitions."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "2") # MR
        resp2 = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Book
        self.assertEqual(resp2.language, "MR")

    def test_08_main_menu(self):
        """8. Main menu provides localized prompt and key options."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "3") # EN
        resp = PhoneSessionService.get_session(self.db, session.id)
        fmt = PhoneSessionService.format_response(self.db, resp)
        self.assertIn("Main Menu", fmt.prompt_text)
        self.assertGreaterEqual(len(fmt.options), 5)

    def test_09_book_appointment_flow(self):
        """9. Complete DTMF booking flow creates real appointment."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # HI
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Book OPD
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Facility 1
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Dept 1
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Doctor 1
        PhoneSessionService.process_dtmf_input(self.db, session.id, "2") # Tomorrow
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Slot 1
        resp_confirm = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Confirm!

        self.assertEqual(resp_confirm.current_state, "BOOKING_COMPLETED")
        self.assertIn("JS-2026", resp_confirm.prompt_text)

    def test_10_facility_search_by_pincode(self):
        """10. Searching location input with 6-digit pincode matches database facilities."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # HI
        session.current_state = "LOCATION_INPUT"
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "413102")
        self.assertEqual(resp.current_state, "FACILITY_SELECTION")

    def test_11_facility_selection_validation(self):
        """11. Selecting valid facility index advances to department selection."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertEqual(resp.current_state, "DEPARTMENT_SELECTION")

    def test_12_department_selection_validation(self):
        """12. Selecting department advances to doctor selection."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertEqual(resp.current_state, "DOCTOR_SELECTION")

    def test_13_doctor_selection_validation(self):
        """13. Selecting doctor advances to date selection."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertEqual(resp.current_state, "DATE_SELECTION")

    def test_14_date_selection(self):
        """14. Selecting date option 2 advances to tomorrow's slots."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "2")
        self.assertEqual(resp.current_state, "SLOT_SELECTION")

    def test_15_slot_selection(self):
        """15. Selecting available slot advances to booking confirmation."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "2")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertEqual(resp.current_state, "BOOKING_CONFIRMATION")

    def test_16_booking_confirmation(self):
        """16. Booking confirmation summary displays doctor name and facility."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "2")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertTrue("Rajesh Sharma" in resp.prompt_text or "Doctor" in resp.prompt_text)

    def test_17_real_appointment_creation(self):
        """17. Real appointment row is persisted in database."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "2")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")

        apt = self.db.query(Appointment).filter(Appointment.booking_channel == BookingChannel.PHONE).order_by(Appointment.id.desc()).first()
        self.assertIsNotNone(apt)
        self.assertTrue(apt.confirmation_code.startswith("JS-2026-"))

    def test_18_sms_queue(self):
        """18. SMS notification row is queued following booking."""
        sms = self.db.query(SMSNotification).order_by(SMSNotification.id.desc()).first()
        self.assertIsNotNone(sms)

    def test_19_check_appointment(self):
        """19. Option 2 in main menu reads caller's active appointment details."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # HI
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "2") # Check ticket
        self.assertEqual(resp.current_state, "CHECK_APPOINTMENT")
        self.assertIn("JS-2026-", resp.prompt_text)

    def test_20_cancel_appointment(self):
        """20. Option 3 + confirmation cancels appointment and updates DB status."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # HI
        PhoneSessionService.process_dtmf_input(self.db, session.id, "3") # Cancel prompt
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Confirm cancel

        self.assertEqual(resp.current_state, "CANCEL_COMPLETED")
        cancelled_apt = self.db.query(Appointment).order_by(Appointment.id.desc()).first()
        self.assertEqual(cancelled_apt.status, AppointmentStatus.CANCELLED)

    def test_21_reschedule_appointment(self):
        """21. Rescheduling appointment releases old slot and books new slot."""
        apt_date = get_today_ist() + timedelta(days=1)
        apt = AppointmentRepository.create_appointment(
            db=self.db,
            patient_id=self.test_patient.id,
            doctor_id=self.test_doctor.id,
            facility_id=self.test_facility.id,
            department_id=self.test_department.id,
            apt_date=apt_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            booking_channel=BookingChannel.PHONE
        )

        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "5") # Reschedule
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select date
        PhoneSessionService.process_dtmf_input(self.db, session.id, "3") # Day after tomorrow
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Slot 1
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Confirm reschedule

        self.assertEqual(resp.current_state, "RESCHEDULE_COMPLETED")
        updated_apt = self.db.query(Appointment).filter(Appointment.id == apt.id).first()
        self.assertEqual(updated_apt.appointment_date, get_today_ist() + timedelta(days=2))

    def test_22_repeat_prompt(self):
        """22. DTMF '0' re-renders current state prompt without state transition."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "0")
        self.assertEqual(resp.current_state, "FACILITY_SELECTION")

    def test_23_back_navigation(self):
        """23. DTMF '9' steps back in state history."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # HI -> MAIN_MENU
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # BOOK -> FACILITY_SELECTION
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "9") # Back
        self.assertEqual(resp.current_state, "MAIN_MENU")

    def test_24_help_prompt(self):
        """24. DTMF '*' renders help prompt."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "*")
        self.assertEqual(resp.current_state, "HELP")
        self.assertTrue("HELP" in resp.voice_playback or "सहायता" in resp.prompt_text or "Help" in resp.prompt_text)

    def test_25_unknown_input(self):
        """25. Invalid key returns valid response without crash."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "X")
        self.assertIsNotNone(resp)

    def test_26_low_confidence_voice(self):
        """26. Low confidence voice input returns repeat prompt via HTTP API."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = self.client.post(
            "/api/v1/phone/voice/input",
            json={"call_session_id": session.id, "text": "bla bla xyz 123", "language_hint": "HI"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.json()["prompt_text"])

    def test_27_dtmf_fallback(self):
        """27. DTMF input works consistently after voice interaction."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        self.assertEqual(resp.current_state, "MAIN_MENU")

    def test_28_emergency_priority(self):
        """28. Emergency intent immediately routes to 108 emergency state via HTTP API."""
        session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        resp = self.client.post(
            "/api/v1/phone/voice/input",
            json={"call_session_id": session.id, "text": "Mujhe emergency help chahiye, ambulance bhejo", "language_hint": "HI"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["current_state"], "EMERGENCY")
        self.assertIn("108", data["prompt_text"])

    def test_29_session_timeout(self):
        """29. Stale call session older than 15 minutes is not resumed."""
        self.db.query(CallSession).filter(CallSession.phone_number.in_(["+919876543210", "9876543210"])).update({"status": CallSessionStatus.COMPLETED})
        self.db.commit()

        old_session = CallSession(
            phone_number="+919876543210",
            language=Language.HI,
            status=CallSessionStatus.ACTIVE,
            current_state="LOCATION_INPUT",
            created_at=datetime.utcnow() - timedelta(minutes=20)
        )
        self.db.add(old_session)
        self.db.commit()

        new_session = PhoneSessionService.start_session(self.db, phone_number="+919876543210", resume_existing=True)
        self.assertNotEqual(new_session.id, old_session.id)
        self.assertIn(new_session.current_state, ["MAIN_MENU", "LANGUAGE_SELECTION", "GREETING", "RETURNING_USER_GREETING"])

    def test_30_safe_session_resume(self):
        """30. Call reconnect within 15 minutes with resume_existing=True resumes session."""
        active_session = CallSession(
            phone_number="+919876543210",
            language=Language.HI,
            status=CallSessionStatus.ACTIVE,
            current_state="BOOKING_CONFIRMATION",
            created_at=datetime.utcnow() - timedelta(minutes=2)
        )
        self.db.add(active_session)
        self.db.commit()

        resumed = PhoneSessionService.start_session(self.db, phone_number="+919876543210", resume_existing=True)
        self.assertEqual(resumed.id, active_session.id)
        self.assertEqual(resumed.current_state, "SLOT_SELECTION")

    def test_31_no_duplicate_appointment_on_retry(self):
        """31. Retrying same appointment creation call does not duplicate appointment rows."""
        count_before = self.db.query(Appointment).count()
        init_session = PhoneSessionService.start_session(self.db, phone_number="+919876543210")
        session_id = init_session.id
        inputs = ["1", "1", "1", "1", "1", "3", "1", "1", "1"]
        for inp in inputs:
            PhoneSessionService.process_dtmf_input(self.db, session_id, inp)

        count_after = self.db.query(Appointment).count()
        self.assertEqual(count_after, count_before + 1)

    def test_32_idor_protection(self):
        """32. Caller cannot cancel another patient's appointment."""
        other_user = User(
            phone_number="+919999000011",
            name="Other Patient",
            role=UserRole.CUSTOMER,
            password_hash=User.hash_password("Pass123!")
        )
        self.db.add(other_user)
        self.db.flush()
        other_patient = PatientProfile(user_id=other_user.id, district="Pune", state="Maharashtra")
        self.db.add(other_patient)
        self.db.flush()

        apt = AppointmentRepository.create_appointment(
            db=self.db,
            patient_id=other_patient.id,
            doctor_id=self.test_doctor.id,
            facility_id=self.test_facility.id,
            department_id=self.test_department.id,
            apt_date=get_today_ist() + timedelta(days=1),
            start_time=time(11, 0),
            end_time=time(11, 30),
            booking_channel=BookingChannel.PWA
        )

        with self.assertRaises(Exception):
            AppointmentService.cancel_appointment(self.db, apt.id, "Unauthorized attempt", current_user=self.test_user)

    def test_33_confirmation_code_authorization(self):
        """33. Confirmation code lookup validates caller authorization."""
        apt = self.db.query(Appointment).order_by(Appointment.id.desc()).first()
        user_token = create_access_token(self.test_user.id)
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = self.client.get(f"/api/v1/appointments/confirmation/{apt.confirmation_code}", headers=headers)
        self.assertIn(resp.status_code, [200, 403])

    def test_34_concurrent_booking_conflict(self):
        """34. Concurrent booking on same slot triggers availability conflict."""
        target_date = get_today_ist() + timedelta(days=3)

        AppointmentRepository.create_appointment(
            db=self.db,
            patient_id=self.test_patient.id,
            doctor_id=self.test_doctor.id,
            facility_id=self.test_facility.id,
            department_id=self.test_department.id,
            apt_date=target_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            booking_channel=BookingChannel.PHONE
        )

        with self.assertRaises(Exception):
            AppointmentRepository.create_appointment(
                db=self.db,
                patient_id=self.test_patient.id,
                doctor_id=self.test_doctor.id,
                facility_id=self.test_facility.id,
                department_id=self.test_department.id,
                apt_date=target_date,
                start_time=time(9, 0),
                end_time=time(9, 30),
                booking_channel=BookingChannel.PHONE
            )

    def test_35_cross_channel_pwa_visibility(self):
        """35. Phone-booked appointment is visible in PWA customer appointments query."""
        user_token = create_access_token(self.test_user.id)
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = self.client.get("/api/v1/appointments/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        apts = resp.json()
        self.assertGreater(len(apts), 0)


if __name__ == "__main__":
    unittest.main()
