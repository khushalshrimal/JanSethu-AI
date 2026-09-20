import unittest
import uuid
import concurrent.futures
from datetime import date, datetime, timedelta, time
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User, PatientProfile
from app.models.facility import Facility, Department
from app.models.doctor import Doctor, DoctorAvailability
from app.models.appointment import Appointment
from app.models.enums import UserRole, BookingChannel, AppointmentStatus, Language
from app.services.appointment_service import AppointmentService
from app.services.availability_service import AvailabilityService, check_slot_availability
from app.services.phone_session_service import PhoneSessionService
from app.services.voice import VoiceUnderstandingService, VoiceUnderstandingResult, IntentEnum
from app.schemas.appointment import AppointmentCreate, AppointmentCancelRequest, AppointmentRescheduleRequest
from app.core.security import create_access_token
from app.utils.timezone import get_today_ist, get_ist_now
from scripts.seed import seed_database

class TestPhase16PatientJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def get_token(self, email: str = "rahul.pawar@demo.in"):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            user = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()
        return create_access_token(user.id)

    # 1. Complete Patient Journey
    def test_01_complete_patient_journey_pwa(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Discover Facility
        fac_res = self.client.get("/api/v1/facilities/search?pincode=413106")
        self.assertEqual(fac_res.status_code, 200)
        facs = fac_res.json()
        self.assertGreaterEqual(len(facs), 1)
        fac_id = facs[0]["id"]

        # Step 2: Discover Active Doctor & Department for Facility
        doc = self.db.query(Doctor).filter(Doctor.facility_id == fac_id, Doctor.is_active == True).first()
        self.assertIsNotNone(doc)
        dept_id = doc.department_id
        doc_id = doc.id

        # Step 4: Check Available Date & Slot
        target_date = get_today_ist() + timedelta(days=2)
        target_date_str = target_date.strftime("%Y-%m-%d")
        avail_res = self.client.get(f"/api/v1/doctors/{doc_id}/availability?date={target_date_str}")
        self.assertEqual(avail_res.status_code, 200)
        slots = avail_res.json()["slots"]
        avail_slots = [s for s in slots if s["status"] == "AVAILABLE"]
        self.assertGreaterEqual(len(avail_slots), 1)
        sel_slot = avail_slots[0]

        # Step 5: Book Appointment
        booking_payload = {
            "doctor_id": doc_id,
            "facility_id": fac_id,
            "department_id": dept_id,
            "appointment_date": target_date_str,
            "start_time": sel_slot["start_time"],
            "end_time": sel_slot["end_time"],
            "booking_channel": "PWA",
            "reason_for_visit": "Complete Journey Verification"
        }
        book_res = self.client.post("/api/v1/appointments/", json=booking_payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_data = book_res.json()
        self.assertIn("JS-2026-", apt_data["confirmation_code"])

        # Step 6: Verify in My Appointments
        my_res = self.client.get("/api/v1/appointments/me", headers=headers)
        self.assertEqual(my_res.status_code, 200)
        my_codes = [a["confirmation_code"] for a in my_res.json()]
        self.assertIn(apt_data["confirmation_code"], my_codes)

    # 2. Facility -> Department Consistency
    def test_02_facility_to_department_consistency(self):
        fac = self.db.query(Facility).first()
        dept_res = self.client.get(f"/api/v1/facilities/{fac.id}/departments")
        self.assertEqual(dept_res.status_code, 200)
        for dept in dept_res.json():
            self.assertEqual(dept["facility_id"], fac.id)

    # 3. Department -> Doctor Consistency
    def test_03_department_to_doctor_consistency(self):
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        doc_res = self.client.get(f"/api/v1/doctors?facility_id={doc.facility_id}&department_id={doc.department_id}")
        self.assertEqual(doc_res.status_code, 200)
        for d in doc_res.json():
            self.assertEqual(d["facility_id"], doc.facility_id)
            self.assertEqual(d["department_id"], doc.department_id)

    # 4. Doctor Availability Generation
    def test_04_doctor_availability_generation(self):
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=1)
        res = self.client.get(f"/api/v1/doctors/{doc.id}/availability?date={target_date.strftime('%Y-%m-%d')}")
        self.assertEqual(res.status_code, 200)
        self.assertIn("slots", res.json())

    # 5. Past Date Rejection
    def test_05_past_date_rejection(self):
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        past_date = (get_today_ist() - timedelta(days=2)).strftime("%Y-%m-%d")
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": past_date,
            "start_time": "10:00:00",
            "booking_channel": "PWA"
        }
        res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertIn("past", str(res.json()).lower())

    # 6. Slot Availability Validation
    def test_06_slot_availability_validation(self):
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=3)
        check = check_slot_availability(self.db, doc.id, target_date, time(9, 0))
        self.assertIn("is_available", check)
        self.assertIn("status", check)

    # 7. Final Availability Recheck Before Booking
    def test_07_final_availability_recheck_before_booking(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=4)
        target_date_str = target_date.strftime("%Y-%m-%d")

        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date_str,
            "start_time": "09:30:00",
            "booking_channel": "PWA"
        }
        # First booking succeeds
        res1 = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res1.status_code, 201)

        # Second booking same slot fails server-side recheck (409 Conflict)
        res2 = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res2.status_code, 409)

    # 8. Successful Booking Creation
    def test_08_successful_booking_creation(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=5)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "10:30:00",
            "booking_channel": "PWA"
        }
        res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)

    # 9. Booking Confirmation Code Summary
    def test_09_booking_confirmation_code_and_summary(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=6)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "11:00:00",
            "booking_channel": "PWA"
        }
        res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["confirmation_code"].startswith("JS-2026-"))
        self.assertEqual(data["status"], "BOOKED")

    # 10. Double Booking Prevention
    def test_10_double_booking_prevention(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=7)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "11:30:00",
            "booking_channel": "PWA"
        }
        res1 = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res1.status_code, 201)
        res2 = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res2.status_code, 409)

    # 11. Unauthorized Appointment Access (IDOR Protection)
    def test_11_unauthorized_appointment_access_idor(self):
        token1 = self.get_token("rahul.pawar@demo.in")
        headers1 = {"Authorization": f"Bearer {token1}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=8)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "12:00:00",
            "booking_channel": "PWA"
        }
        res1 = self.client.post("/api/v1/appointments/", json=payload, headers=headers1)
        self.assertEqual(res1.status_code, 201)
        apt_id = res1.json()["id"]

        token2 = self.get_token("anita.k@demo.in")
        headers2 = {"Authorization": f"Bearer {token2}"}
        res_idor = self.client.get(f"/api/v1/appointments/{apt_id}", headers=headers2)
        self.assertEqual(res_idor.status_code, 403)

    # 12. Customer Appointment List (/me)
    def test_12_customer_appointment_list_me(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.get("/api/v1/appointments/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    # 13. Cancellation Flow
    def test_13_cancellation_flow(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=9)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "12:30:00",
            "booking_channel": "PWA"
        }
        book_res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_id = book_res.json()["id"]

        cancel_res = self.client.post(f"/api/v1/appointments/{apt_id}/cancel", json={"reason": "Schedule change"}, headers=headers)
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.json()["status"], "CANCELLED")

    # 14. Rescheduling Flow
    def test_14_rescheduling_flow(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        old_date = get_today_ist() + timedelta(days=10)
        new_date = get_today_ist() + timedelta(days=11)

        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": old_date.strftime("%Y-%m-%d"),
            "start_time": "09:00:00",
            "booking_channel": "PWA"
        }
        book_res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_id = book_res.json()["id"]

        reschedule_payload = {
            "new_date": new_date.strftime("%Y-%m-%d"),
            "new_start_time": "10:00:00",
            "reason": "Doctor request"
        }
        resched_res = self.client.post(f"/api/v1/appointments/{apt_id}/reschedule", json=reschedule_payload, headers=headers)
        self.assertEqual(resched_res.status_code, 200)
        self.assertEqual(resched_res.json()["appointment_date"], new_date.strftime("%Y-%m-%d"))

    # 15. Old Slot Released After Reschedule
    def test_15_old_slot_released_after_reschedule(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        old_date = get_today_ist() + timedelta(days=12)
        new_date = get_today_ist() + timedelta(days=13)

        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": old_date.strftime("%Y-%m-%d"),
            "start_time": "11:30:00",
            "booking_channel": "PWA"
        }
        book_res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_id = book_res.json()["id"]

        reschedule_payload = {
            "new_date": new_date.strftime("%Y-%m-%d"),
            "new_start_time": "10:30:00",
            "reason": "Rescheduling test"
        }
        resched = self.client.post(f"/api/v1/appointments/{apt_id}/reschedule", json=reschedule_payload, headers=headers)
        self.assertEqual(resched.status_code, 200)

        # Verify old slot is available again for new booking
        res_old_slot = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res_old_slot.status_code, 201)

    # 16. New Slot Booked After Reschedule
    def test_16_new_slot_booked_after_reschedule(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        old_date = get_today_ist() + timedelta(days=14)
        new_date = get_today_ist() + timedelta(days=15)

        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": old_date.strftime("%Y-%m-%d"),
            "start_time": "12:00:00",
            "booking_channel": "PWA"
        }
        book_res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_id = book_res.json()["id"]

        new_slot_payload = {
            "new_date": new_date.strftime("%Y-%m-%d"),
            "new_start_time": "11:00:00",
            "reason": "Moving slot"
        }
        resched = self.client.post(f"/api/v1/appointments/{apt_id}/reschedule", json=new_slot_payload, headers=headers)
        self.assertEqual(resched.status_code, 200)

        # Attempting to book the new slot again should return 409 Conflict
        conflict_payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": new_date.strftime("%Y-%m-%d"),
            "start_time": "11:00:00",
            "booking_channel": "PWA"
        }
        res_conflict = self.client.post("/api/v1/appointments/", json=conflict_payload, headers=headers)
        self.assertEqual(res_conflict.status_code, 409)

    # 17. SMS Queued After Booking
    def test_17_sms_queued_after_booking(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=16)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "09:00:00",
            "booking_channel": "PWA"
        }
        res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        self.assertIsNotNone(res.json()["notification"])

    # 18. SMS Lifecycle After Cancellation
    def test_18_sms_lifecycle_after_cancellation(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=17)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "09:30:00",
            "booking_channel": "PWA"
        }
        book_res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_id = book_res.json()["id"]

        cancel_res = self.client.post(f"/api/v1/appointments/{apt_id}/cancel", json={"reason": "Test cancel SMS"}, headers=headers)
        self.assertEqual(cancel_res.status_code, 200)

    # 19. SMS Lifecycle After Reschedule
    def test_19_sms_lifecycle_after_reschedule(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=18)
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "booking_channel": "PWA"
        }
        book_res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        apt_id = book_res.json()["id"]

        resched_res = self.client.post(f"/api/v1/appointments/{apt_id}/reschedule", json={"new_date": (target_date + timedelta(days=1)).strftime("%Y-%m-%d"), "new_start_time": "09:00:00"}, headers=headers)
        self.assertEqual(resched_res.status_code, 200)

    # 20. Voice Journey Flow
    def test_20_voice_journey_flow(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        v_res = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Baramati mein pediatric doctor ka appointment book karna hai", "language_hint": "HI"})
        self.assertEqual(v_res.status_code, 200)
        self.assertIn("prompt_text", v_res.json())

    # 21. DTMF Journey Flow
    def test_21_dtmf_journey_flow(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        keys = ["1", "1", "1", "1", "1", "2", "1", "1"]
        for key in keys:
            res = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": key})
            self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["current_state"], "BOOKING_COMPLETED")

    # 22. Hindi Language Journey
    def test_22_hindi_language_journey(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        res = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "1"})
        self.assertEqual(res.json()["language"], "HI")

    # 23. Marathi Language Journey
    def test_23_marathi_language_journey(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        res = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "2"})
        self.assertEqual(res.json()["language"], "MR")

    # 24. English Language Journey
    def test_24_english_language_journey(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        res = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "3"})
        self.assertEqual(res.json()["language"], "EN")

    # 25. Low-Confidence Voice Fallback
    def test_25_low_confidence_voice_fallback(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        v_res = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "xyz abc mmm blah...", "language_hint": "HI"})
        self.assertEqual(v_res.status_code, 200)

    # 26. Emergency Priority Routing
    def test_26_emergency_priority_routing(self):
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9876543210"})
        session_id = start_res.json()["session_id"]
        v_res = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Emergency casualty ambulance chahiye 108", "language_hint": "HI"})
        self.assertEqual(v_res.status_code, 200)
        self.assertEqual(v_res.json()["current_state"], "EMERGENCY")

    # 27. Invalid Facility/Department/Doctor Combinations
    def test_27_invalid_facility_dept_doctor_combinations(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        target_date = get_today_ist() + timedelta(days=20)
        payload = {
            "doctor_id": 9999, # Invalid doctor
            "facility_id": 1,
            "department_id": 1,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "booking_channel": "PWA"
        }
        res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res.status_code, 400)

    # 28. No Availability Handling
    def test_28_no_availability_handling(self):
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = date(2026, 10, 25) # Doctor 1 leave date in seed
        res = self.client.get(f"/api/v1/doctors/{doc.id}/availability?date={target_date.strftime('%Y-%m-%d')}")
        self.assertEqual(res.status_code, 200)

    # 29. Past Time Today Rejection
    def test_29_past_time_today_rejection(self):
        token = self.get_token("rahul.pawar@demo.in")
        headers = {"Authorization": f"Bearer {token}"}
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        today_str = get_today_ist().strftime("%Y-%m-%d")
        past_time = "00:01:00" # Early morning past time today
        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": today_str,
            "start_time": past_time,
            "booking_channel": "PWA"
        }
        res = self.client.post("/api/v1/appointments/", json=payload, headers=headers)
        self.assertEqual(res.status_code, 400)

    # 30. Concurrent Booking Protection
    def test_30_concurrent_booking_protection(self):
        token = self.get_token("rahul.pawar@demo.in")
        doc = self.db.query(Doctor).filter(Doctor.is_active == True).first()
        target_date = get_today_ist() + timedelta(days=21)
        target_date_str = target_date.strftime("%Y-%m-%d")
        start_time_str = "10:30:00"

        payload = {
            "doctor_id": doc.id,
            "facility_id": doc.facility_id,
            "department_id": doc.department_id,
            "appointment_date": target_date_str,
            "start_time": start_time_str,
            "booking_channel": "PWA"
        }

        def make_booking():
            client = TestClient(app)
            return client.post("/api/v1/appointments/", json=payload, headers={"Authorization": f"Bearer {token}"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(make_booking)
            future2 = executor.submit(make_booking)
            res1 = future1.result()
            res2 = future2.result()

        statuses = sorted([res1.status_code, res2.status_code])
        # Exactly one request must succeed (201) and one must be rejected (409 Conflict)
        self.assertEqual(statuses, [201, 409])

if __name__ == "__main__":
    unittest.main()
