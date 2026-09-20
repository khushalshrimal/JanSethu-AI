import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from app.integrations.sms.base import SMSProvider
from app.integrations.sms.models import SMSRequest, SMSResult, SMSDeliveryStatus
from app.utils.phone_normalizer import normalize_phone_number

class MSG91SMSProvider(SMSProvider):
    """
    MSG91 SMS Integration Adapter (Indian DLT SMS Route).
    Dispatches SMS notifications via MSG91 Flow API and parses delivery webhooks.
    """

    async def send_sms(self, req: SMSRequest) -> SMSResult:
        norm_recipient = normalize_phone_number(req.to_number)
        msg91_mobile = norm_recipient.replace("+", "")
        msg_id = f"MSG91-{uuid.uuid4().hex[:12].upper()}"
        
        if settings.MSG91_AUTH_KEY:
            api_url = "https://control.msg91.com/api/v5/flow/"
            headers = {
                "authkey": settings.MSG91_AUTH_KEY,
                "content-type": "application/json"
            }
            body = {
                "template_id": settings.MSG91_TEMPLATE_ID or "jansethu_appointment_template",
                "sender": settings.MSG91_SENDER_ID or "JANSTH",
                "recipients": [
                    {
                        "mobiles": msg91_mobile,
                        "message": req.message
                    }
                ]
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(api_url, json=body, headers=headers)
                    if resp.status_code == 200:
                        res_data = resp.json()
                        return SMSResult(
                            provider="msg91",
                            provider_message_id=res_data.get("request_id") or msg_id,
                            status=SMSDeliveryStatus.SENT,
                            sent_at=datetime.utcnow()
                        )
                    else:
                        return SMSResult(
                            provider="msg91",
                            provider_message_id=msg_id,
                            status=SMSDeliveryStatus.FAILED,
                            sent_at=datetime.utcnow()
                        )
            except Exception:
                return SMSResult(
                    provider="msg91",
                    provider_message_id=msg_id,
                    status=SMSDeliveryStatus.FAILED,
                    sent_at=datetime.utcnow()
                )

        # Staging Fallback
        print(f"\n================ [MSG91 STAGING SMS DISPATCH] ================")
        print(f"To: {norm_recipient}")
        print(f"Ref ID: {msg_id}")
        print(f"Message:\n{req.message}")
        print("==============================================================\n")

        return SMSResult(
            provider="msg91",
            provider_message_id=msg_id,
            status=SMSDeliveryStatus.SENT,
            sent_at=datetime.utcnow(),
            is_simulated=True
        )

    async def get_delivery_status(self, provider_message_id: str) -> SMSDeliveryStatus:
        if not provider_message_id or "ERROR" in provider_message_id:
            return SMSDeliveryStatus.FAILED
        return SMSDeliveryStatus.DELIVERED

    def parse_delivery_report(self, payload: Dict[str, Any]) -> SMSResult:
        msg_id = payload.get("requestId") or payload.get("request_id") or payload.get("msgId") or "UNKNOWN"
        raw_status = str(payload.get("status") or payload.get("cause") or "").upper()

        if raw_status in ["1", "DELIVRD", "SUCCESS", "DELIVERED"]:
            delivery_status = SMSDeliveryStatus.DELIVERED
        elif raw_status in ["2", "UNDELIV", "FAILED"]:
            delivery_status = SMSDeliveryStatus.FAILED
        elif raw_status in ["16", "REJECTD", "REJECTED"]:
            delivery_status = SMSDeliveryStatus.REJECTED
        else:
            delivery_status = SMSDeliveryStatus.SENT

        return SMSResult(
            provider="msg91",
            provider_message_id=msg_id,
            status=delivery_status,
            sent_at=datetime.utcnow()
        )
