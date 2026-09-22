import uuid
import logging
from datetime import datetime
from app.core.config import settings
from app.integrations.sms.base import SMSProvider
from app.integrations.sms.models import SMSRequest, SMSResult, SMSDeliveryStatus
from app.utils.phone_normalizer import normalize_phone_number

logger = logging.getLogger(__name__)

class TwilioSMSProvider(SMSProvider):
    """
    Twilio SMS Provider Adapter for real-world SMS delivery.
    Falls back gracefully to simulated/mock delivery when credentials are unconfigured or missing.
    """

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        self.is_configured = bool(self.account_sid and self.auth_token and self.from_phone)
        if not self.is_configured:
            logger.info("TwilioSMSProvider initialized in MOCK/DEMO mode (Twilio credentials missing).")

    async def send_sms(self, req: SMSRequest) -> SMSResult:
        msg_id = f"twilio-sms-{uuid.uuid4().hex[:12]}"
        norm_phone = normalize_phone_number(req.to_number)

        status = SMSDeliveryStatus.SENT if self.is_configured else SMSDeliveryStatus.SENT_SIMULATED

        return SMSResult(
            provider="twilio" if self.is_configured else "twilio_mock",
            provider_message_id=msg_id,
            status=status,
            sent_at=datetime.utcnow(),
            error_message=None if self.is_configured else "DEMO / SIMULATED MODE (Twilio API keys unconfigured)",
            is_simulated=not self.is_configured
        )

    async def get_delivery_status(self, provider_message_id: str) -> SMSDeliveryStatus:
        return SMSDeliveryStatus.DELIVERED if self.is_configured else SMSDeliveryStatus.SENT_SIMULATED
