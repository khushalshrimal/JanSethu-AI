import unittest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.enums import UserRole, NotificationStatus
from app.models.user import User
from app.models.telephony import CallSession, SMSNotification
from app.models.appointment import Appointment
from app.core.security import create_access_token
from app.utils.phone_normalizer import normalize_phone_number
from app.services.notification_service import NotificationService
from app.utils.timezone import get_today_ist

client = TestClient(app)

class TestPhase9TelephonySMS(unittest.TestCase):
    def setUp(self):
        self.db: Session = SessionLocal()
        self.today = get_today_ist()
        self.tomorrow = self.today + timedelta(days=1)

        self.customer = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()
        self.admin = self.db.query(User).filter(User.role == UserRole.ADMIN).first()

        self.customer_headers = {"Authorization": f"Bearer {create_access_token(self.customer.id)}"}
        self.admin_headers = {"Authorization": f"Bearer {create_access_token(self.admin.id)}"}
        self.secret_headers = {"X-Webhook-Secret": "development-secret-key-2026"}

    def tearDown(self):
        self.db.close()

    def test_phone_number_normalization(self):
        self.assertEqual(normalize_phone_number("+919876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("919876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("09876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("9876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("+91 98765-43210"), "+919876543210")

    def test_dev_incoming_call_simulation(self):
        res = client.post(
            "/api/v1/telephony/dev/incoming-call",
            json={"from_number": "9876543210", "to_number": "+911234567890"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("provider_call_id", data)
        self.assertIn("call_session_id", data)
        self.assertIn(data["state"], ["GREETING", "RETURNING_USER_GREETING", "PHONE_REGISTRATION_NAME"])

    def test_webhook_security_rejection(self):
        res_missing = client.post(
            "/api/v1/telephony/webhooks/incoming",
            json={"from_number": "9876543210", "to_number": "+911234567890"}
        )
        self.assertEqual(res_missing.status_code, 401)

        res_invalid = client.post(
            "/api/v1/telephony/webhooks/incoming",
            headers={"X-Webhook-Secret": "wrong-secret-key"},
            json={"from_number": "9876543210", "to_number": "+911234567890"}
        )
        self.assertEqual(res_invalid.status_code, 401)

    def test_webhook_incoming_call_and_idempotency(self):
        headers = {**self.secret_headers}
        payload = {
            "provider": "development",
            "provider_call_id": "test-call-evt-100",
            "from_number": "+919876543210",
            "to_number": "+911234567890",
            "provider_event_id": "evt-idempotent-001"
        }

        res1 = client.post("/api/v1/telephony/webhooks/incoming", headers=headers, json=payload)
        self.assertEqual(res1.status_code, 200)
        self.assertIn("call_session_id", res1.json())

        res2 = client.post("/api/v1/telephony/webhooks/incoming", headers=headers, json=payload)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["status"], "ALREADY_PROCESSED")

    def test_webhook_dtmf_input(self):
        start_res = client.post(
            "/api/v1/telephony/dev/incoming-call",
            json={"from_number": "9876543210"}
        )
        call_id = start_res.json()["provider_call_id"]

        dtmf_res = client.post(
            "/api/v1/telephony/webhooks/dtmf",
            headers=self.secret_headers,
            json={"provider_call_id": call_id, "digits": "1"}
        )
        self.assertEqual(dtmf_res.status_code, 200)
        self.assertIn("language", dtmf_res.json())

    def test_webhook_voice_input(self):
        start_res = client.post(
            "/api/v1/telephony/dev/incoming-call",
            json={"from_number": "9876543210"}
        )
        call_id = start_res.json()["provider_call_id"]

        voice_res = client.post(
            "/api/v1/telephony/webhooks/voice",
            headers=self.secret_headers,
            json={"provider_call_id": call_id, "text": "Mujhe doctor ko dikhana hai", "language": "hi"}
        )
        self.assertEqual(voice_res.status_code, 200)

    def test_sms_status_webhook(self):
        apt = self.db.query(Appointment).first()
        if not apt:
            self.skipTest("No appointment found")

        sms = NotificationService.send_appointment_notification(self.db, apt, event_type="BOOKING")
        self.assertIsNotNone(sms)
        self.db.commit()
        msg_id = sms.provider_message_id

        res = client.post(
            "/api/v1/sms/webhooks/status",
            headers=self.secret_headers,
            json={
                "provider_message_id": msg_id,
                "status": "DELIVERED"
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(res.json()["status"], ["DELIVERED", "SENT"])

    def test_appointment_reminder_trigger(self):
        apt = self.db.query(Appointment).first()
        if not apt:
            self.skipTest("No appointment for reminder test")

        sms = NotificationService.send_appointment_reminder(self.db, apt.id)
        self.assertIsNotNone(sms)
        self.assertIn("Reminder", sms.message)

    def test_outbound_call_simulation(self):
        res = client.post(
            "/api/v1/telephony/webhooks/outbound",
            headers=self.admin_headers,
            json={"to_number": "9876543210"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["simulated"])
        self.assertEqual(data["direction"], "OUTBOUND")

    def test_admin_telephony_monitoring_rbac(self):
        res_cust = client.get("/api/v1/telephony/sessions", headers=self.customer_headers)
        self.assertEqual(res_cust.status_code, 403)

        res_admin = client.get("/api/v1/telephony/sessions", headers=self.admin_headers)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIsInstance(res_admin.json(), list)
