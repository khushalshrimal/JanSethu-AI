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
