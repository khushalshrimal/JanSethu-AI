import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from app.integrations.telephony.base import TelephonyProvider
from app.integrations.telephony.models import (
    IncomingCall, CallDirection, CallStatus, CallControlResponse, CallControlAction
)
from app.utils.phone_normalizer import normalize_phone_number

class DevelopmentTelephonyProvider(TelephonyProvider):
    """
    Zero-cost simulated telephony provider for local dev and testing.
    Generates synthetic provider_call_id values without external network dependencies.
    """
    def __init__(self):
        self.active_calls: Dict[str, IncomingCall] = {}

    async def start_call(self, from_number: str, to_number: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        call_id = f"dev-call-{uuid.uuid4().hex[:12]}"
        norm_from = normalize_phone_number(from_number)
        norm_to = normalize_phone_number(to_number)

        call = IncomingCall(
            provider="development",
            provider_call_id=call_id,
            from_number=norm_from,
            to_number=norm_to,
            direction=CallDirection.INBOUND,
            status=CallStatus.RINGING,
            received_at=datetime.utcnow(),
            metadata_json=metadata or {}
        )
        self.active_calls[call_id] = call
        return call

    async def answer_call(self, provider_call_id: str) -> IncomingCall:
        call = self.active_calls.get(provider_call_id)
        if not call:
            call = IncomingCall(
                provider="development",
                provider_call_id=provider_call_id,
                from_number="+919876543210",
                to_number="+911234567890",
                direction=CallDirection.INBOUND,
                status=CallStatus.IN_PROGRESS
            )
            self.active_calls[provider_call_id] = call
        else:
            call.status = CallStatus.IN_PROGRESS
        return call

    async def play_prompt(self, provider_call_id: str, prompt_text: str, language: str = "hi") -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.PLAY_PROMPT,
            prompt=prompt_text,
            language=language
        )

    async def collect_dtmf(self, provider_call_id: str, prompt_text: str, num_digits: int = 1, timeout_seconds: int = 8) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.COLLECT_DTMF,
            prompt=prompt_text,
            timeout_seconds=timeout_seconds,
            dtmf_fallback=True
        )

    async def collect_speech(self, provider_call_id: str, prompt_text: str, language: str = "hi", timeout_seconds: int = 8) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.COLLECT_SPEECH,
            prompt=prompt_text,
            language=language,
            timeout_seconds=timeout_seconds,
            dtmf_fallback=True
        )

    async def transfer_call(self, provider_call_id: str, transfer_number: str) -> CallControlResponse:
        return CallControlResponse(
            action=CallControlAction.TRANSFER,
            transfer_number=normalize_phone_number(transfer_number)
        )

    async def end_call(self, provider_call_id: str, reason: Optional[str] = None) -> CallControlResponse:
        if provider_call_id in self.active_calls:
            self.active_calls[provider_call_id].status = CallStatus.COMPLETED
        return CallControlResponse(
            action=CallControlAction.END_CALL
        )

    async def initiate_outbound_call(self, to_number: str, callback_url: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        call_id = f"dev-outbound-{uuid.uuid4().hex[:12]}"
        norm_to = normalize_phone_number(to_number)

        call = IncomingCall(
            provider="development",
            provider_call_id=call_id,
            from_number="+911234567890",
            to_number=norm_to,
            direction=CallDirection.OUTBOUND,
            status=CallStatus.RINGING,
            received_at=datetime.utcnow(),
            metadata_json={**(metadata or {}), "simulated": True}
        )
        self.active_calls[call_id] = call
        return call
