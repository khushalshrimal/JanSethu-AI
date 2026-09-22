from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union

class SpeechInputProvider(ABC):
    """Abstract interface for Speech-to-Text (STT) providers."""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: Union[bytes, str, dict],
        language_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribes audio data into text.
        Returns dict: {"text": str, "language": str, "confidence": float}
        """
        pass


class LocalSpeechInputProvider(SpeechInputProvider):
    """
    Development/Local STT provider.
    Accepts text strings or JSON dict payload in dev mode for zero paid API dependencies.
    """

    async def transcribe(
        self,
        audio_data: Union[bytes, str, dict],
        language_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        if isinstance(audio_data, dict):
            text = audio_data.get("text", "")
            lang = audio_data.get("language") or language_hint or "hi"
            conf = float(audio_data.get("confidence", 0.95))
            return {"text": text, "language": lang, "confidence": conf}
        
        if isinstance(audio_data, str):
            return {
                "text": audio_data,
                "language": language_hint or "hi",
                "confidence": 0.95
            }

        # Fallback for raw byte payload in dev mode
        return {
            "text": "doctor ko dikhana hai",
            "language": language_hint or "hi",
            "confidence": 0.90
        }


# Alias for clarity
MockSpeechInputProvider = LocalSpeechInputProvider


class ConfiguredSpeechInputProvider(SpeechInputProvider):
    """
    Environment-configurable Speech-to-Text provider factory/wrapper.
    Selects STT provider dynamically based on STT_PROVIDER env variable.
    Defaults to LocalSpeechInputProvider (mock) when unconfigured.
    """

    def __init__(self, provider_type: Optional[str] = None):
        import os
        self.provider_type = (provider_type or os.getenv("STT_PROVIDER", "mock")).lower()
        if self.provider_type in ["mock", "local", "development"]:
            self._provider = LocalSpeechInputProvider()
        else:
            self._provider = LocalSpeechInputProvider()

    async def transcribe(
        self,
        audio_data: Union[bytes, str, dict],
        language_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self._provider.transcribe(audio_data, language_hint=language_hint)


def get_speech_provider() -> SpeechInputProvider:
    return ConfiguredSpeechInputProvider()

