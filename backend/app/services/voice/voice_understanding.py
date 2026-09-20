from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
from app.models.enums import Language
from app.services.voice.speech_provider import SpeechInputProvider, LocalSpeechInputProvider
from app.services.voice.language_detector import LanguageDetector
from app.services.voice.voice_normalizer import VoiceNormalizer
from app.services.voice.intent_parser import IntentParser, IntentEnum
from app.services.voice.entity_extractor import EntityExtractor

class VoiceUnderstandingResult(BaseModel):
    raw_text: str
    normalized_text: str
    language: Language
    intent: IntentEnum
    confidence: float
    entities: Dict[str, Any] = {}

class VoiceUnderstandingService:
    """
    Unified Natural Language Understanding (NLU) pipeline for Voice IVR.
    Combines transcription, language detection, text normalization, intent classification, and entity extraction.
    """

    def __init__(self, speech_provider: Optional[SpeechInputProvider] = None):
        self.speech_provider = speech_provider or LocalSpeechInputProvider()

    async def process_utterance(
        self,
        audio_or_text: Union[bytes, str, dict],
        language_hint: Optional[str] = None
    ) -> VoiceUnderstandingResult:
        # 1. Transcribe speech
        transcription = await self.speech_provider.transcribe(audio_or_text, language_hint=language_hint)
        raw_text = transcription.get("text", "")
        base_confidence = transcription.get("confidence", 0.90)

        if not raw_text.strip():
            return VoiceUnderstandingResult(
                raw_text="",
                normalized_text="",
                language=Language.HI if not language_hint else Language(language_hint.upper()),
                intent=IntentEnum.UNKNOWN,
                confidence=0.0,
                entities={}
            )

        # 2. Language Detection
        detected_lang = LanguageDetector.detect_language(
            raw_text,
            default_language=Language(language_hint.upper()) if language_hint else Language.HI
        )

        # 3. Text Normalization
        normalized_text = VoiceNormalizer.normalize(raw_text)

        # 4. Intent Classification
        intent, intent_confidence = IntentParser.parse_intent(raw_text)

        # 5. Entity Extraction
        entities = EntityExtractor.extract_entities(raw_text)

        # 6. Overall Confidence Calculation
        final_confidence = round(min(1.0, base_confidence * intent_confidence), 2)

        return VoiceUnderstandingResult(
            raw_text=raw_text,
            normalized_text=normalized_text,
            language=detected_lang,
            intent=intent,
            confidence=final_confidence,
            entities=entities
        )
