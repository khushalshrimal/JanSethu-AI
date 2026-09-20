import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.integrations.telephony.factory import get_telephony_provider
from app.integrations.sms.factory import get_sms_provider
from app.models.appointment import Appointment
from app.models.enums import UserRole

client = TestClient(app)

class TestPhase12Cloud:

    def test_environment_configuration_separation(self):
        assert settings.APP_ENV in ["development", "staging", "production", "test"]
        assert hasattr(settings, "EXOTEL_ACCOUNT_SID")
        assert hasattr(settings, "MSG91_AUTH_KEY")

    def test_dual_telephony_provider_coexistence(self):
        # Dev Provider (used by Phone Simulator)
        dev_p = get_telephony_provider("development")
        assert dev_p.__class__.__name__ == "DevelopmentTelephonyProvider"

        # Exotel Provider (used by Exotel ExoML)
        exo_p = get_telephony_provider("exotel")
        assert exo_p.__class__.__name__ == "ExotelTelephonyProvider"

    def test_database_double_booking_unique_constraint(self):
        # Inspect Appointment model table args for unique constraint
        table_args = getattr(Appointment, "__table_args__", ())
        has_unique_constraint = any(
            hasattr(arg, "name") and "uq_doctor_date_time" in str(arg.name)
            for arg in table_args
        ) or any(
            "doctor_id" in [c.name for c in getattr(arg, "columns", [])]
            for arg in table_args
        )
        assert has_unique_constraint is True

    def test_cross_channel_phone_simulator_to_pwa_and_admin(self):
        # 1. Start call session via Phone Simulator endpoint
        phone = f"+9199{uuid.uuid4().hex[:8]}"
        start_res = client.post("/api/v1/phone/calls/start", json={"caller_phone": phone})
        assert start_res.status_code == 201
        sess_data = start_res.json()
        session_id = sess_data["session_id"]
        assert sess_data["status"] == "ACTIVE"

        # 2. Keypress 1 -> Select Hindi
        lang_res = client.post(f"/api/v1/phone/calls/{session_id}/input", json={"input_type": "DTMF", "value": "1"})
        assert lang_res.status_code == 200
        assert lang_res.json()["language"] == "HI"

        # 3. Register customer to view PWA appointments
        reg_res = client.post("/api/v1/auth/register", json={
            "name": "Cloud Staging User",
            "phone_number": phone,
            "password": "StagingPassword123!",
            "preferred_language": "HI"
        })
        assert reg_res.status_code == 201

        # 4. Login customer
        login_res = client.post("/api/v1/auth/login", json={
            "phone_number": phone,
            "password": "StagingPassword123!"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 5. Customer queries my appointments over PWA API
        my_apts = client.get("/api/v1/appointments/me", headers=headers)
        assert my_apts.status_code == 200

    def test_webhook_security_rejection_for_invalid_secret(self):
        res = client.post(
            "/api/v1/telephony/webhooks/incoming",
            json={
                "provider": "development",
                "from_number": "+919876543210",
                "to_number": "+911234567890"
            },
            headers={"X-Webhook-Secret": "invalid-secret-key-9999"}
        )
        assert res.status_code == 401
        assert "Invalid or missing webhook authorization secret" in str(res.json())

