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


# Alias for clarity
MockTTSProvider = LocalTTSProvider


class ConfiguredTTSProvider(TTSProvider):
    """
    Environment-configurable Text-to-Speech provider factory/wrapper.
    Selects TTS provider dynamically based on TTS_PROVIDER env variable.
    Defaults to LocalTTSProvider (mock) when unconfigured.
    """

    def __init__(self, provider_type: Optional[str] = None):
        import os
        self.provider_type = (provider_type or os.getenv("TTS_PROVIDER", "mock")).lower()
        if self.provider_type in ["mock", "local", "development"]:
            self._provider = LocalTTSProvider()
        else:
            self._provider = LocalTTSProvider()

    async def synthesize(
        self,
        text: str,
        language: str = "hi"
    ) -> Dict[str, Any]:
        return await self._provider.synthesize(text, language=language)


def get_tts_provider() -> TTSProvider:
    return ConfiguredTTSProvider()

