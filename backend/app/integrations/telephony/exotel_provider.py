import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from app.core.config import settings
from app.integrations.telephony.base import TelephonyProvider
from app.integrations.telephony.models import (
    IncomingCall, CallControlResponse, CallControlAction,
    CallDirection, CallStatus
)
from app.utils.phone_normalizer import normalize_phone_number

class ExotelTelephonyProvider(TelephonyProvider):
    """
    Exotel Cloud Telephony Integration Adapter (India Telecom IVR/ExoML).
    Maps Exotel HTTP webhooks to canonical domain models and generates ExoML responses.
    """

    def parse_incoming_call(self, request_data: Dict[str, Any]) -> IncomingCall:
        call_sid = request_data.get("CallSid") or request_data.get("call_id") or f"exo-{uuid.uuid4().hex[:8]}"
        from_phone = request_data.get("From") or request_data.get("Caller") or "+919876543210"
        to_phone = request_data.get("To") or request_data.get("CallTo") or "+911234567890"

        return IncomingCall(
            provider="exotel",
            provider_call_id=call_sid,
            from_number=normalize_phone_number(from_phone),
            to_number=normalize_phone_number(to_phone),
            direction=CallDirection.INBOUND,
            status=CallStatus.RINGING,
            received_at=datetime.utcnow(),
            metadata_json=request_data
        )

    def build_call_control_response(
        self,
        action: CallControlAction,
        prompt_text: str,
        gather_digits: bool = True,
        num_digits: int = 1,
        timeout_seconds: int = 10
    ) -> CallControlResponse:
        response_elem = ET.Element("Response")
        
        if action == CallControlAction.END_CALL:
            say_elem = ET.SubElement(response_elem, "Say")
            say_elem.text = prompt_text
            ET.SubElement(response_elem, "Hangup")
            xml_str = ET.tostring(response_elem, encoding="utf-8").decode("utf-8")
            return CallControlResponse(
                action=action,
                prompt=prompt_text,
                provider_payload={"content_type": "text/xml", "xml_response": xml_str}
            )

        if gather_digits:
            gather_elem = ET.SubElement(
                response_elem, 
                "Gather", 
                action=f"{settings.PUBLIC_BASE_URL}{settings.API_V1_STR}/telephony/webhooks/exotel/dtmf", 
                method="POST", 
                numDigits=str(num_digits), 
                timeout=str(timeout_seconds)
            )
            say_elem = ET.SubElement(gather_elem, "Say")
            say_elem.text = prompt_text
        else:
            say_elem = ET.SubElement(response_elem, "Say")
            say_elem.text = prompt_text

        xml_str = ET.tostring(response_elem, encoding="utf-8").decode("utf-8")
        return CallControlResponse(
            action=action or CallControlAction.PLAY_PROMPT,
            prompt=prompt_text,
            provider_payload={"content_type": "text/xml", "xml_response": xml_str}
        )

    async def start_call(self, from_number: str, to_number: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        call_id = f"exotel-call-{uuid.uuid4().hex[:12]}"
        return IncomingCall(
            provider="exotel",
            provider_call_id=call_id,
            from_number=normalize_phone_number(from_number),
            to_number=normalize_phone_number(to_number),
            direction=CallDirection.INBOUND,
            status=CallStatus.RINGING,
            received_at=datetime.utcnow(),
            metadata_json=metadata or {}
        )

    async def answer_call(self, provider_call_id: str) -> IncomingCall:
        return IncomingCall(
            provider="exotel",
            provider_call_id=provider_call_id,
            from_number="+919876543210",
            to_number="+911234567890",
            direction=CallDirection.INBOUND,
            status=CallStatus.IN_PROGRESS
        )

    async def play_prompt(self, provider_call_id: str, prompt_text: str, language: str = "hi") -> CallControlResponse:
        return self.build_call_control_response(
            action=CallControlAction.PLAY_PROMPT,
            prompt_text=prompt_text,
            gather_digits=False
        )

    async def collect_dtmf(self, provider_call_id: str, prompt_text: str, num_digits: int = 1, timeout_seconds: int = 8) -> CallControlResponse:
        return self.build_call_control_response(
            action=CallControlAction.COLLECT_DTMF,
            prompt_text=prompt_text,
            gather_digits=True,
            num_digits=num_digits,
            timeout_seconds=timeout_seconds
        )

    async def collect_speech(self, provider_call_id: str, prompt_text: str, language: str = "hi", timeout_seconds: int = 8) -> CallControlResponse:
        return self.build_call_control_response(
            action=CallControlAction.COLLECT_SPEECH,
            prompt_text=prompt_text,
            gather_digits=True,
            num_digits=1,
            timeout_seconds=timeout_seconds
        )

    async def transfer_call(self, provider_call_id: str, transfer_number: str) -> CallControlResponse:
        response_elem = ET.Element("Response")
        dial_elem = ET.SubElement(response_elem, "Dial")
        dial_elem.text = normalize_phone_number(transfer_number)
        xml_str = ET.tostring(response_elem, encoding="utf-8").decode("utf-8")
        return CallControlResponse(
            action=CallControlAction.TRANSFER,
            prompt=f"Transferring to {transfer_number}",
            xml_response=xml_str,
            meta={"content_type": "text/xml"}
        )

    async def end_call(self, provider_call_id: str, reason: Optional[str] = None) -> CallControlResponse:
        return self.build_call_control_response(
            action=CallControlAction.END_CALL,
            prompt_text="Thank you for using JanSethu Healthcare. Goodbye.",
            gather_digits=False
        )

    async def initiate_outbound_call(
        self,
        to_number: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IncomingCall:
        norm_to = normalize_phone_number(to_number)
        call_id = f"EXO-OUTBOUND-{uuid.uuid4().hex[:10]}"
        return IncomingCall(
            provider="exotel",
            provider_call_id=call_id,
            from_number=settings.EXOTEL_CALLER_ID or "+911234567890",
            to_number=norm_to,
            direction=CallDirection.OUTBOUND,
            status=CallStatus.RINGING,
            received_at=datetime.utcnow(),
            metadata_json=metadata or {}
        )
