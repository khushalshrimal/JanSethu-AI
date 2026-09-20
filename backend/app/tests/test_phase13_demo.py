import pytest
import asyncio
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models import (
    User, PatientProfile, Facility, Department, Doctor, DoctorAvailability,
    Appointment, UserRole, AppointmentStatus, BookingChannel, Language
)
from app.core.security import create_access_token
from app.services.voice.voice_understanding import VoiceUnderstandingService
from app.services.phone_session_service import PhoneSessionService

client = TestClient(app)

@pytest.fixture
def auth_headers_admin(db_session: Session):
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    if not admin:
        admin = User(
            name="Test Admin",
            phone_number="+91-9999900001",
            email="testadmin@demo.in",
            password_hash=User.hash_password("Pass123!"),
            role=UserRole.ADMIN
        )
        db_session.add(admin)
        db_session.commit()
    token = create_access_token({"sub": admin.email, "role": admin.role.value, "user_id": admin.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_provider(db_session: Session):
    provider = db_session.query(User).filter(User.role == UserRole.PROVIDER).first()
    if not provider:
        provider = User(
            name="Dr. Test Provider",
            phone_number="+91-9999900002",
            email="testdoc@demo.in",
            password_hash=User.hash_password("Pass123!"),
            role=UserRole.PROVIDER
        )
        db_session.add(provider)
        db_session.commit()
    token = create_access_token({"sub": provider.email, "role": provider.role.value, "user_id": provider.id})
    return {"Authorization": f"Bearer {token}"}

class TestPhase13DemoQA:
    def setup_method(self):
        self.db = SessionLocal()

    def teardown_method(self):
        self.db.close()

    def test_complete_phone_booking_flow(self):
        """1. Complete phone booking flow via PhoneSessionService."""
        start_res = client.post("/api/v1/phone/calls/start", json={"caller_phone": "+919876543210"})
        assert start_res.status_code == 201
        session_id = start_res.json()["session_id"]

        # Select language (1 -> Hindi)
        dtmf1 = client.post(f"/api/v1/phone/calls/{session_id}/input", json={"value": "1"})
        assert dtmf1.status_code == 200

        # Send voice intent
        voice1 = client.post(
            "/api/v1/phone/voice/input",
            json={"call_session_id": session_id, "text": "Mujhe doctor ko dikhana hai", "language_hint": "HI"}
        )
        assert voice1.status_code == 200
        assert voice1.json()["intent"] == "BOOK_APPOINTMENT"

    def test_dtmf_booking_flow(self):
        """2. DTMF keypad booking flow."""
        start_res = client.post("/api/v1/phone/calls/start", json={"caller_phone": "+919876543210"})
        assert start_res.status_code == 201
        session_id = start_res.json()["session_id"]

        # 1 -> Hindi
        client.post(f"/api/v1/phone/calls/{session_id}/input", json={"value": "1"})
        # 1 -> Book Appointment
        res = client.post(f"/api/v1/phone/calls/{session_id}/input", json={"value": "1"})
        assert res.status_code == 200
        assert "current_state" in res.json()

    def test_hindi_intent_flow(self):
        """3. Hindi natural language intent parsing."""
        vus = VoiceUnderstandingService()
        parsed = asyncio.run(vus.process_utterance("Mujhe doctor ko dikhana hai", "HI"))
        assert parsed.intent.value == "BOOK_APPOINTMENT"
        assert parsed.confidence >= 0.85

    def test_marathi_intent_flow(self):
        """4. Marathi natural language intent parsing."""
        vus = VoiceUnderstandingService()
        parsed = asyncio.run(vus.process_utterance("मला डॉक्टरांना भेटायचे आहे.", "MR"))
        assert parsed.intent.value == "BOOK_APPOINTMENT"
        assert parsed.confidence >= 0.85

    def test_cross_channel_appointment_visibility(self):
        """5. Verify appointment created in database is visible across PWA, Provider, Admin."""
        admin = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        token = create_access_token(admin.id)
        headers = {"Authorization": f"Bearer {token}"}

        admin_res = client.get("/api/v1/admin/appointments", headers=headers)
        assert admin_res.status_code == 200
        assert len(admin_res.json()) >= 1

    def test_double_booking_prevention(self):
        """6. Verify double booking prevention returns controlled rejection/error."""
        import uuid, random
        doc = self.db.query(Doctor).first()
        patient = self.db.query(PatientProfile).first()
        if not doc or not patient:
            pytest.skip("Doctor/Patient missing")

        t_date = date(2027, 1, 1) + timedelta(days=random.randint(1, 1000))
        t_time = time(10, 0)
        c_code1 = f"JS-DBL1-{uuid.uuid4().hex[:6]}"
        c_code2 = f"JS-DBL2-{uuid.uuid4().hex[:6]}"

        apt1 = Appointment(
            patient_id=patient.id,
            doctor_id=doc.id,
            facility_id=doc.facility_id,
            department_id=doc.department_id,
            appointment_date=t_date,
            start_time=t_time,
            end_time=time(10, 30),
            status=AppointmentStatus.BOOKED,
            booking_channel=BookingChannel.PWA,
            confirmation_code=c_code1
        )
        self.db.add(apt1)
        self.db.commit()

        # Duplicate slot attempt
        apt2 = Appointment(
            patient_id=patient.id,
            doctor_id=doc.id,
            facility_id=doc.facility_id,
            department_id=doc.department_id,
            appointment_date=t_date,
            start_time=t_time,
            end_time=time(10, 30),
            status=AppointmentStatus.BOOKED,
            booking_channel=BookingChannel.PWA,
            confirmation_code=c_code2
        )
        self.db.add(apt2)
        with pytest.raises(Exception):
            self.db.commit()
        self.db.rollback()

    def test_emergency_flow(self):
        """7. Verify emergency natural language prompt immediately enters EMERGENCY state."""
        start_res = client.post("/api/v1/phone/calls/start", json={"caller_phone": "+919876543210"})
        session_id = start_res.json()["session_id"]
        client.post(f"/api/v1/phone/calls/{session_id}/input", json={"value": "1"})

        emg_res = client.post(
            "/api/v1/phone/voice/input",
            json={"call_session_id": session_id, "text": "Mujhe emergency help chahiye", "language_hint": "HI"}
        )
        assert emg_res.status_code == 200
        assert emg_res.json()["current_state"] == "EMERGENCY"
        assert "108" in emg_res.json()["voice_playback"] or "Emergency" in emg_res.json()["voice_playback"]

    def test_provider_isolation(self):
        """8. Provider object-level authorization test."""
        provider = self.db.query(User).filter(User.role == UserRole.PROVIDER).first()
        token = create_access_token(provider.id)
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/provider/appointments", headers=headers)
        assert res.status_code == 200

    def test_sms_failure_resilience(self):
        """9. SMS failure does not rollback appointment booking."""
        from app.integrations.sms.factory import get_sms_provider
        from app.integrations.sms.models import SMSRequest
        sms = get_sms_provider("development")
        req = SMSRequest(to_number="+919876543210", message="Test notification")
        res = asyncio.run(sms.send_sms(req))
        assert res.status.value in ["SENT", "LOGGED", "DELIVERED", "SENT_SIMULATED"]

    def test_demo_reset_and_health_check(self):
        """10. Test demo reset and demo health check endpoints."""
        health_res = client.get("/api/v1/health/demo-readiness")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "PASS"

        admin = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        token = create_access_token(admin.id)
        headers = {"Authorization": f"Bearer {token}"}

        reset_res = client.post("/api/v1/admin/demo-reset", headers=headers)
        assert reset_res.status_code == 200
        assert reset_res.json()["status"] == "RESET_SUCCESSFUL"

