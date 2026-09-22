import unittest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models import CallSession, Appointment, SMSNotification
from app.models.enums import CallSessionStatus, Language, BookingChannel, AppointmentStatus
from app.services.voice import LanguageDetector, IntentParser, IntentEnum, EntityExtractor, VoiceUnderstandingService
from scripts.seed import seed_database

class TestPhase7VoiceInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_language_detection(self):
        """Verify LanguageDetector correctly classifies EN, HI, and MR."""
        self.assertEqual(LanguageDetector.detect_language("I want to book an appointment"), Language.EN)
        self.assertEqual(LanguageDetector.detect_language("Mujhe doctor ko dikhana hai"), Language.HI)
        self.assertEqual(LanguageDetector.detect_language("मला डॉक्टरांना भेटायचे आहे"), Language.MR)

    def test_intent_parsing(self):
        """Verify IntentParser accuracy across core intent enum values."""
        intent_hi, conf1 = IntentParser.parse_intent("Mujhe doctor ko dikhana hai")
        self.assertEqual(intent_hi, IntentEnum.BOOK_APPOINTMENT)
        self.assertGreaterEqual(conf1, 0.80)

        intent_chk, conf2 = IntentParser.parse_intent("Meri appointment status check karo")
        self.assertEqual(intent_chk, IntentEnum.CHECK_APPOINTMENT)

        intent_cncl, conf3 = IntentParser.parse_intent("Appointment cancel karo")
        self.assertEqual(intent_cncl, IntentEnum.CANCEL_APPOINTMENT)

        intent_emg, conf4 = IntentParser.parse_intent("Mujhe emergency ambulance chahiye 108")
        self.assertEqual(intent_emg, IntentEnum.EMERGENCY)

    def test_entity_extraction(self):
        """Verify EntityExtractor correctly parses locations, dates, and confirmations."""
        entities_hi = EntityExtractor.extract_entities("Kal Baramati hospital mein doctor ko dikhana hai")
        self.assertEqual(entities_hi.get("facility_search"), "baramati")
        self.assertEqual(entities_hi.get("date"), "tomorrow")

        entities_conf = EntityExtractor.extract_entities("Haan, confirm kar do")
        self.assertEqual(entities_conf.get("confirmation"), True)

        entities_no = EntityExtractor.extract_entities("Nahi cancel karo")
        self.assertEqual(entities_no.get("confirmation"), False)

    def test_full_voice_booking_flow_hindi(self):
        """
        Verify end-to-end Hindi voice booking:
        Start Call -> "Mujhe doctor ko dikhana hai" -> "Baramati" -> "Pediatrics" -> "Kal" -> "Haan, confirm karo" -> BOOKING_COMPLETED.
        """
        phone = f"+91-98{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        self.assertEqual(start_res.status_code, 201)
        session_id = start_res.json()["session_id"]

        # Step 1: Voice Utterance - Book Appointment
        v1 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Mujhe doctor ko dikhana hai", "language_hint": "HI"})
        self.assertEqual(v1.status_code, 200)
        self.assertIn(v1.json()["current_state"], ["FACILITY_SELECTION", "LOCATION_INPUT"])

        # Step 2: Voice Utterance - Facility Search "Baramati"
        v2 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Baramati government hospital", "language_hint": "HI"})
        self.assertEqual(v2.status_code, 200)
        self.assertEqual(v2.json()["current_state"], "DEPARTMENT_SELECTION")

        # Step 3: Voice Utterance - Department "Pediatrics"
        v3 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Pediatrics child doctor", "language_hint": "HI"})
        self.assertEqual(v3.status_code, 200)
        self.assertEqual(v3.json()["current_state"], "DOCTOR_SELECTION")

        # Step 4: Voice Utterance - Doctor Selection
        v4 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Dr. Rajesh Sharma", "language_hint": "HI"})
        self.assertEqual(v4.status_code, 200)
        self.assertEqual(v4.json()["current_state"], "DATE_SELECTION")

        # Step 5: Voice Utterance - Date "Kal" (Tomorrow)
        v5 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Kal ka slot chahiye", "language_hint": "HI"})
        self.assertEqual(v5.status_code, 200)
        self.assertEqual(v5.json()["current_state"], "SLOT_SELECTION")

        # Step 6: Voice Utterance - Slot Selection
        v6 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Pehla slot", "language_hint": "HI"})
        self.assertEqual(v6.status_code, 200)
        self.assertEqual(v6.json()["current_state"], "BOOKING_CONFIRMATION")

        # Step 7: Voice Utterance - Explicit Confirmation "Haan confirm karo"
        v7 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Haan, confirm kar do", "language_hint": "HI"})
        self.assertEqual(v7.status_code, 200)
        data = v7.json()
        self.assertEqual(data["current_state"], "BOOKING_COMPLETED")
        self.assertIn("JS-2026-", data["prompt_text"])

        # Verify DB appointment creation
        apt = self.db.query(Appointment).filter(Appointment.booking_channel == BookingChannel.PHONE).order_by(Appointment.id.desc()).first()
        self.assertIsNotNone(apt)
        self.assertEqual(apt.booking_channel, BookingChannel.PHONE)

    def test_voice_booking_flow_marathi(self):
        """Verify Marathi voice booking flow ("मला डॉक्टरांना भेटायचे आहे")."""
        phone = f"+91-95{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        # Step 1: Marathi voice utterance
        v1 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "मला डॉक्टरांना भेटायचे आहे", "language_hint": "MR"})
        self.assertEqual(v1.status_code, 200)
        self.assertEqual(v1.json()["detected_language"], "MR")

    def test_voice_emergency_flow(self):
        """Verify voice emergency utterance immediately transitions to EMERGENCY state."""
        phone = f"+91-94{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        emg_res = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Mujhe emergency help chahiye", "language_hint": "HI"})
        self.assertEqual(emg_res.status_code, 200)
        data = emg_res.json()
        self.assertEqual(data["current_state"], "EMERGENCY")
        self.assertEqual(data["intent"], "EMERGENCY")

    def test_voice_and_dtmf_interoperability(self):
        """Verify seamless switching between Voice input and DTMF keypad input within the same call session."""
        phone = f"+91-93{uuid.uuid4().hex[:8]}"
        start_res = self.client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        session_id = start_res.json()["session_id"]

        # Voice input: Book appointment -> transitions to FACILITY_SELECTION
        v1 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Mujhe doctor ko dikhana hai"})
        self.assertEqual(v1.json()["current_state"], "FACILITY_SELECTION")

        # DTMF key input: Press 1 for Facility 1 -> transitions to DEPARTMENT_SELECTION
        d1 = self.client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "1"})
        self.assertEqual(d1.json()["current_state"], "DEPARTMENT_SELECTION")

        # Voice input: "Pediatrics" -> transitions to DOCTOR_SELECTION
        v2 = self.client.post("/api/v1/phone/voice/input", json={"call_session_id": session_id, "text": "Pediatrics"})
        self.assertEqual(v2.json()["current_state"], "DOCTOR_SELECTION")

if __name__ == "__main__":
    unittest.main()
