from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.integrations.telephony.models import IncomingCall, CallControlResponse, CallControlAction

class TelephonyProvider(ABC):
    @abstractmethod
    async def start_call(self, from_number: str, to_number: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        """Initialize or process an incoming network call."""
        pass

    @abstractmethod
    async def answer_call(self, provider_call_id: str) -> IncomingCall:
        """Answer the call session."""
        pass

    @abstractmethod
    async def play_prompt(self, provider_call_id: str, prompt_text: str, language: str = "hi") -> CallControlResponse:
        """Play a voice prompt to caller."""
        pass

    @abstractmethod
    async def collect_dtmf(self, provider_call_id: str, prompt_text: str, num_digits: int = 1, timeout_seconds: int = 8) -> CallControlResponse:
        """Collect DTMF keypad presses."""
        pass

    @abstractmethod
    async def collect_speech(self, provider_call_id: str, prompt_text: str, language: str = "hi", timeout_seconds: int = 8) -> CallControlResponse:
        """Collect speech/voice input from caller."""
        pass

    @abstractmethod
    async def transfer_call(self, provider_call_id: str, transfer_number: str) -> CallControlResponse:
        """Transfer call to another phone number (e.g. 108 Emergency)."""
        pass

    @abstractmethod
    async def end_call(self, provider_call_id: str, reason: Optional[str] = None) -> CallControlResponse:
        """Terminate call session."""
        pass

    @abstractmethod
    async def initiate_outbound_call(self, to_number: str, callback_url: str, metadata: Optional[Dict[str, Any]] = None) -> IncomingCall:
        """Initiate an outbound call (e.g. appointment reminder)."""
        pass
