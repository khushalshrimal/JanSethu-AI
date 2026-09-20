import uuid
from datetime import datetime
from typing import Dict
from app.integrations.sms.base import SMSProvider
from app.integrations.sms.models import SMSRequest, SMSResult, SMSDeliveryStatus
from app.utils.phone_normalizer import normalize_phone_number

class DevelopmentSMSProvider(SMSProvider):
    """
    Simulated SMS provider for local testing and zero-cost dev.
    Stores messages in memory with status SENT_SIMULATED and exposes sent message log.
    """
    def __init__(self):
        self.sent_messages: Dict[str, Dict] = {}

    async def send_sms(self, req: SMSRequest) -> SMSResult:
        msg_id = f"dev-sms-{uuid.uuid4().hex[:12]}"
        norm_phone = normalize_phone_number(req.to_number)

        record = {
            "provider": "development",
            "provider_message_id": msg_id,
            "to_number": norm_phone,
            "message": req.message,
            "status": SMSDeliveryStatus.SENT_SIMULATED,
            "sent_at": datetime.utcnow(),
            "is_simulated": True
        }
        self.sent_messages[msg_id] = record

        print(f"\n================ DEVELOPMENT SMS DISPATCH ================\nTo: {norm_phone}\nMessage:\n{req.message}\nProvider ID: {msg_id}\nStatus: SENT_SIMULATED\n==========================================================\n")

        return SMSResult(
            provider="development",
            provider_message_id=msg_id,
            status=SMSDeliveryStatus.SENT_SIMULATED,
            sent_at=record["sent_at"],
            is_simulated=True
        )

    async def get_delivery_status(self, provider_message_id: str) -> SMSDeliveryStatus:
        if provider_message_id in self.sent_messages:
            return self.sent_messages[provider_message_id]["status"]
        return SMSDeliveryStatus.SENT_SIMULATED
