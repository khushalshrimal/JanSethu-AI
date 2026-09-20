import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.logging import MaskingFormatter, mask_phone_number
from app.core.exceptions import ValidationError, NotFoundError

client = TestClient(app)

class TestPhase10Production:

    def test_health_liveness_and_readiness_endpoints(self):
        # 1. Base Health
        resp_health = client.get("/api/v1/health")
        assert resp_health.status_code == 200
        data_health = resp_health.json()
        assert data_health["status"] in ["ok", "degraded"]
        assert data_health["service"] == settings.PROJECT_NAME

        # 2. Liveness Check
        resp_live = client.get("/api/v1/health/live")
        assert resp_live.status_code == 200
        assert resp_live.json()["status"] == "alive"

        # 3. Readiness Check
        resp_ready = client.get("/api/v1/health/ready")
        assert resp_ready.status_code == 200
        assert resp_ready.json()["status"] == "ready"
        assert resp_ready.json()["database"] == "connected"

    def test_request_correlation_id_middleware(self):
        # Request without X-Request-ID should have one generated
        resp1 = client.get("/api/v1/health/live")
        assert "X-Request-ID" in resp1.headers
        assert resp1.headers["X-Request-ID"].startswith("req_")

        # Request with client-supplied X-Request-ID should echo it
        custom_id = "custom_req_123456"
        resp2 = client.get("/api/v1/health/live", headers={"X-Request-ID": custom_id})
        assert resp2.headers["X-Request-ID"] == custom_id

    def test_security_headers_middleware(self):
        resp = client.get("/api/v1/health/live")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert resp.headers["X-XSS-Protection"] == "1; mode=block"

    def test_pii_phone_number_masking(self):
        raw_phone = "+919876543210"
        masked = mask_phone_number(raw_phone)
        assert "987654" not in masked
        assert masked == "+91******3210"

        text_log = "User caller +919876543210 requested appointment"
        masked_log = MaskingFormatter.mask_pii(text_log)
        assert "987654" not in masked_log
        assert "+91******3210" in masked_log

    def test_rate_limiter_protection(self):
        from app.core.rate_limiter import rate_limiter
        # Fire multiple rapid requests to protected route /api/v1/auth/login
        try:
            for _ in range(settings.RATE_LIMIT_PER_MINUTE + 5):
                res = client.post("/api/v1/auth/login", json={"phone": "9999999999", "password": "wrong"})
                if res.status_code == 429:
                    data = res.json()
                    assert data["success"] is False
                    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
                    assert "request_id" in data["error"]
                    break
        finally:
            rate_limiter.requests.clear()


    def test_cross_channel_end_to_end_flow(self):
        # 1. Register new customer
        phone = f"+9198{uuid.uuid4().hex[:8]}"
        reg_resp = client.post("/api/v1/auth/register", json={
            "name": "Phase 10 User",
            "phone_number": phone,
            "password": "Password123!",
            "preferred_language": "HI",
            "village": "Baramati",
            "district": "Pune",
            "pincode": "413102"
        })
        assert reg_resp.status_code == 201

        # 2. Login customer
        login_resp = client.post("/api/v1/auth/login", json={
            "phone_number": phone,
            "password": "Password123!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Search facilities
        fac_resp = client.get("/api/v1/facilities/", headers=headers)
        assert fac_resp.status_code == 200
        facilities = fac_resp.json()
        assert len(facilities) > 0
        fac_id = facilities[0]["id"]

        # 4. Get doctors
        doc_resp = client.get(f"/api/v1/doctors/?facility_id={fac_id}", headers=headers)
        assert doc_resp.status_code == 200
        doctors = doc_resp.json()
        assert len(doctors) > 0
        doc_id = doctors[0]["id"]

        # 5. Check availability
        avail_resp = client.get(f"/api/v1/doctors/{doc_id}/availability?date=2026-11-15", headers=headers)
        assert avail_resp.status_code == 200
        avail_data = avail_resp.json()
        assert "slots" in avail_data
        available_slots = [s["start_time"] for s in avail_data["slots"] if s["status"] == "AVAILABLE"]
        assert len(available_slots) > 0
        selected_slot = available_slots[0]

        # 6. Book appointment
        start_time_val = selected_slot if len(selected_slot) == 8 else f"{selected_slot}:00"
        book_resp = client.post("/api/v1/appointments/", json={
            "doctor_id": doc_id,
            "facility_id": fac_id,
            "appointment_date": "2026-11-15",
            "start_time": start_time_val,
            "booking_channel": "PWA"
        }, headers=headers)
        assert book_resp.status_code == 201
        apt_data = book_resp.json()
        assert apt_data["status"] == "BOOKED"
        assert apt_data["confirmation_code"] is not None

        # 7. Customer views my appointments
        my_apts = client.get("/api/v1/appointments/me", headers=headers)
        assert my_apts.status_code == 200
        assert any(a["id"] == apt_data["id"] for a in my_apts.json())

