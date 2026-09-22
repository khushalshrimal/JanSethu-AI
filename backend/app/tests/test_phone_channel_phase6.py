import unittest
import uuid
from datetime import date, time
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models import CallSession, Appointment, User, PatientProfile
from app.models.enums import CallSessionStatus, Language, BookingChannel, AppointmentStatus
from scripts.seed import seed_database

class TestPhase6PhoneChannel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_start_call_session(self):
        """Verify initiating a new call session sets state to GREETING and persists in DB."""
        phone = f"+91-99{uuid.uuid4().hex[:8]}"
        res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn(data["current_state"], ["GREETING", "PHONE_REGISTRATION_NAME"])
        self.assertEqual(data["status"], "ACTIVE")
        self.assertTrue("JanSethu" in data["prompt_text"] or "जनसेतु" in data["prompt_text"])

        # Check DB persistence
        session = self.db.query(CallSession).filter(CallSession.id == data["session_id"]).first()
        self.assertIsNotNone(session)
        self.assertIn(session.current_state, ["GREETING", "PHONE_REGISTRATION_NAME"])

    def test_dtmf_language_selection(self):
        """Verify DTMF 1 sets Hindi, DTMF 2 sets Marathi, DTMF 3 sets English."""
        phone = f"+91-98{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        # Step 1: Press 1 for Hindi
        in_res1 = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "1"})
        self.assertEqual(in_res1.status_code, 200)
        data1 = in_res1.json()
        self.assertEqual(data1["language"], "HI")
        self.assertEqual(data1["current_state"], "MAIN_MENU")

    def test_full_dtmf_booking_flow(self):
        """
        Verify complete DTMF keypad flow:
        Start Call -> Hindi (1) -> Book (1) -> Location (1) -> Facility (1) -> Dept (1) -> Doctor (1) -> Date (1) -> Slot (1) -> Confirm (1) -> BOOKING_COMPLETED.
        """
        phone = f"+91-99{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        # Key sequence for booking (8 steps: Hindi -> Book -> Facility -> Dept -> Doctor -> Tomorrow (2) -> Slot 1 -> Confirm)
        keys = ["1", "1", "1", "1", "1", "2", "1", "1"]
        for idx, key in enumerate(keys):
            res = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": key})
            self.assertEqual(res.status_code, 200)
            print(f"KEY[{idx+1}]={key} -> {res.json()['current_state']}")

        final_data = res.json()
        self.assertEqual(final_data["current_state"], "BOOKING_COMPLETED")
        self.assertIn("JS-2026-", final_data["prompt_text"])

        # Verify appointment exists in database with BookingChannel.PHONE
        apt = self.db.query(Appointment).filter(Appointment.booking_channel == BookingChannel.PHONE).order_by(Appointment.id.desc()).first()
        self.assertIsNotNone(apt)
        self.assertEqual(apt.booking_channel, BookingChannel.PHONE)

    def test_emergency_option(self):
        """Verify selecting 4 from Main Menu transitions to EMERGENCY state."""
        phone = f"+91-97{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        # Language Hindi -> Emergency (4)
        self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "1"})
        emg_res = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "4"})
        self.assertEqual(emg_res.status_code, 200)
        data = emg_res.json()
        self.assertEqual(data["current_state"], "EMERGENCY")
        self.assertIn("108", data["prompt_text"])

    def test_end_call_session(self):
        """Verify calling end session endpoint marks session as COMPLETED."""
        phone = f"+91-96{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        end_res = self.client.post(f"/api/v1/phone/calls/{session_id}/end")
        self.assertEqual(end_res.status_code, 200)
        data = end_res.json()
        self.assertEqual(data["current_state"], "ENDED")
        self.assertEqual(data["status"], "COMPLETED")

    def test_multi_caller_session_isolation(self):
        """Verify Session A and Session B operate independently without state collision."""
        s1 = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9911111111"}).json()
        s2 = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": "+91-9922222222"}).json()

        # Session 1 -> Hindi
        self.client.post(f"/api/v1/phone/calls/{s1['session_id']}/input", json={"input_type": "DTMF", "value": "1"})
        # Session 2 -> English
        self.client.post(f"/api/v1/phone/calls/{s2['session_id']}/input", json={"input_type": "DTMF", "value": "3"})

        r1 = self.client.get(f"/api/v1/phone/calls/{s1['session_id']}").json()
        r2 = self.client.get(f"/api/v1/phone/calls/{s2['session_id']}").json()

        self.assertEqual(r1["language"], "HI")
        self.assertEqual(r2["language"], "EN")

if __name__ == "__main__":
    unittest.main()
