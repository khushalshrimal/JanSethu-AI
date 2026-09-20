from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class TTSProvider(ABC):
    """Abstract interface for Text-to-Speech (TTS) providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Synthesizes text into spoken audio.
        Returns dict: {"text": str, "language": str, "audio_available": bool, "audio_url": Optional[str]}
        """
        pass


class LocalTTSProvider(TTSProvider):
    """
    Development/Local Text-to-Speech provider.
    Returns structured text response for simulated audio playback without paid cloud dependencies.
    """

    async def synthesize(
        self,
        text: str,
        language: str = "hi"
    ) -> Dict[str, Any]:
        return {
            "text": text,
            "language": language,
            "audio_available": False,
            "audio_url": None
        }
