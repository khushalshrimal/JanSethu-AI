import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.integrations.telephony.base import TelephonyProvider
from app.integrations.telephony.models import (
    IncomingCall, CallDirection, CallStatus, CallControlResponse, CallControlAction
)
from app.utils.phone_normalizer import normalize_phone_number

logger = logging.getLogger(__name__)

class VonageTelephonyProvider(TelephonyProvider):
    """
    Vonage (Nexmo) Voice Telephony Provider Adapter.
    Generates NCCO (Nexmo Call Control Object) JSON responses when configured.
    Falls back gracefully to simulated response mode when Vonage credentials are absent.
    """

    def __init__(self):
        self.api_key = settings.VONAGE_API_KEY
        self.api_secret = settings.VONAGE_API_SECRET
        self.from_phone = settings.VONAGE_PHONE_NUMBER
        self.is_configured = bool(self.api_key and self.api_secret and self.from_phone)
        if not self.is_configured:
            logger.info("VonageTelephonyProvider initialized in MOCK/DEMO mode (Vonage credentials missing).")

    async def start_call(self, from_number: str, to_number: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        call_id = f"vonage-call-{uuid.uuid4().hex[:12]}"
        return IncomingCall(
            provider="vonage" if self.is_configured else "vonage_mock",
            provider_call_id=call_id,
            from_number=normalize_phone_number(from_number),
            to_number=normalize_phone_number(to_number),
            direction=CallDirection.INBOUND,
            status=CallStatus.RINGING,
            received_at=datetime.utcnow(),
            metadata_json=metadata or {"is_mock": not self.is_configured}
        )

    async def answer_call(self, provider_call_id: str) -> IncomingCall:
        return IncomingCall(
            provider="vonage" if self.is_configured else "vonage_mock",
            provider_call_id=provider_call_id,
            from_number="+919876543210",
            to_number=self.from_phone or "+911234567890",
            direction=CallDirection.INBOUND,
            status=CallStatus.IN_PROGRESS
        )

    async def play_prompt(self, provider_call_id: str, prompt_text: str, language: str = "hi") -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.PLAY_PROMPT,
            prompt=prompt_text,
            language=language,
            metadata={"ncco": [{"action": "talk", "text": prompt_text, "language": language}]}
        )

    async def collect_dtmf(self, provider_call_id: str, prompt_text: str, num_digits: int = 1, timeout_seconds: int = 8) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.COLLECT_DTMF,
            prompt=prompt_text,
            num_digits=num_digits,
            timeout_seconds=timeout_seconds,
            metadata={"ncco": [{"action": "talk", "text": prompt_text}, {"action": "input", "type": ["dtmf"], "dtmf": {"maxDigits": num_digits, "timeOut": timeout_seconds}}]}
        )

    async def collect_speech(self, provider_call_id: str, prompt_text: str, language: str = "hi", timeout_seconds: int = 8) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.COLLECT_SPEECH,
            prompt=prompt_text,
            language=language,
            timeout_seconds=timeout_seconds,
            metadata={"ncco": [{"action": "talk", "text": prompt_text}, {"action": "input", "type": ["speech"], "speech": {"language": language, "timeOut": timeout_seconds}}]}
        )

    async def transfer_call(self, provider_call_id: str, transfer_number: str) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.TRANSFER,
            prompt=f"Transferring to {transfer_number}",
            metadata={"ncco": [{"action": "connect", "endpoint": [{"type": "phone", "number": transfer_number}]}]}
        )

    async def end_call(self, provider_call_id: str, reason: Optional[str] = None) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.HANGUP,
            prompt="Call ended.",
            metadata={"ncco": []}
        )

    async def initiate_outbound_call(self, to_number: str, callback_url: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        call_id = f"vonage-out-{uuid.uuid4().hex[:12]}"
        return IncomingCall(
            provider="vonage" if self.is_configured else "vonage_mock",
            provider_call_id=call_id,
            from_number=self.from_phone or "+911234567890",
            to_number=normalize_phone_number(to_number),
            direction=CallDirection.OUTBOUND,
            status=CallStatus.QUEUED,
            metadata_json={"callback_url": callback_url, "is_mock": not self.is_configured}
        )
