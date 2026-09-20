import uuid
import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.integrations.telephony.factory import get_telephony_provider
from app.integrations.sms.factory import get_sms_provider
from app.integrations.telephony.exotel_provider import ExotelTelephonyProvider
from app.integrations.sms.msg91_provider import MSG91SMSProvider
from app.integrations.sms.models import SMSRequest

client = TestClient(app)

class TestPhase11Staging:

    def test_provider_factories_switching(self):
        # 1. Telephony Factory
        dev_telephony = get_telephony_provider("development")
        assert dev_telephony.__class__.__name__ == "DevelopmentTelephonyProvider"

        exotel_telephony = get_telephony_provider("exotel")
        assert exotel_telephony.__class__.__name__ == "ExotelTelephonyProvider"

        # 2. SMS Factory
        dev_sms = get_sms_provider("development")
        assert dev_sms.__class__.__name__ == "DevelopmentSMSProvider"

        msg91_sms = get_sms_provider("msg91")
        assert msg91_sms.__class__.__name__ == "MSG91SMSProvider"

    def test_exotel_telephony_provider_exoml_generation(self):
        provider = ExotelTelephonyProvider()

        # Incoming call parse
        incoming = provider.parse_incoming_call({
            "CallSid": "EXO-CALL-12345",
            "From": "+919876543210",
            "To": "+918000000000"
        })
        assert incoming.provider_call_id == "EXO-CALL-12345"
        assert incoming.from_number == "+919876543210"

        # ExoML XML response build
        ctrl_resp = provider.build_call_control_response(
            action=None,
            prompt_text="Welcome to JanSethu Healthcare Staging",
            gather_digits=True,
            num_digits=1
        )
        assert ctrl_resp.provider_payload["content_type"] == "text/xml"
        xml_text = ctrl_resp.provider_payload["xml_response"]
        assert "<Response>" in xml_text
        assert "<Gather" in xml_text
        assert "Welcome to JanSethu Healthcare Staging" in xml_text

    def test_msg91_sms_provider_and_delivery_report(self):
        provider = MSG91SMSProvider()

        # Dispatch staging SMS
        result = asyncio.run(provider.send_sms(SMSRequest(
            to_number="+919876543210",
            message="JanSethu Staging Appointment Confirmed Ref: JS-STG-001"
        )))
        assert result.provider_message_id.startswith("MSG91-")

        # Delivery report parse
        report = provider.parse_delivery_report({
            "requestId": result.provider_message_id,
            "status": "DELIVRD"
        })
        assert report.provider_message_id == result.provider_message_id
        assert report.status.value == "DELIVERED"

    def test_exotel_exoml_webhooks_integration(self):
        call_sid = f"EXO-TEST-{uuid.uuid4().hex[:6]}"

        # 1. Incoming Call Webhook (Form Data)
        res1 = client.post(
            "/api/v1/telephony/webhooks/exotel/incoming",
            data={
                "CallSid": call_sid,
                "From": "+919876543210",
                "To": "+918000000000"
            }
        )
        assert res1.status_code == 200
        assert "text/xml" in res1.headers["content-type"]
        assert "<Response>" in res1.text
        assert "<Gather" in res1.text

        # 2. DTMF Keypress Webhook (Digit 1 = Hindi)
        res2 = client.post(
            "/api/v1/telephony/webhooks/exotel/dtmf",
            data={
                "CallSid": call_sid,
                "Digits": "1"
            }
        )
        assert res2.status_code == 200
        assert "text/xml" in res2.headers["content-type"]
        assert "<Response>" in res2.text

    def test_msg91_status_webhook_integration(self):
        res = client.post(
            "/api/v1/telephony/webhooks/msg91/status",
            json={
                "requestId": "MSG91-TEST-9999",
                "status": "DELIVRD"
            }
        )
        assert res.status_code == 200
