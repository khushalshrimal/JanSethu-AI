import re
from typing import Optional
from app.models.enums import Language

class LanguageDetector:
    """
    Detects language (HI, MR, EN) from spoken or written text.
    Uses Devanagari script detection and vocabulary heuristics.
    """

    @staticmethod
    def detect_language(text: str, default_language: Language = Language.HI) -> Language:
        if not text or not text.strip():
            return default_language

        text_lower = text.strip().lower()

        # Check explicit Devanagari characters
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text_lower))

        if has_devanagari:
            # Specific Marathi Devanagari indicators
            marathi_devanagari = ["मला", "आहे", "करू", "पाहिजे", "नाही", "रुग्णालय", "तपासा", "रद्द", "भेटायचे", "उद्या", "माझ्या", "जवळचे", "आपत्कालीन", "मराठी", "मराठीत"]
            for w in marathi_devanagari:
                if w in text_lower:
                    return Language.MR
            return Language.HI

        # Check Hinglish / Marathish / English vocabulary
        marathi_latin = ["mala", "ahe", "pahije", "bhetayche", "udya", "tapas", "radd", "apratkalin", "rugnalay", "majhya", "marathi"]
        for w in marathi_latin:
            if re.search(rf'\b{w}\b', text_lower):
                return Language.MR

        hindi_latin = ["mujhe", "dikhana", "milna", "chahiye", "karo", "karni", "batao", "kal", "aaj", "mere", "paas", "karna", "haan", "ji", "nahin", "raha"]
        for w in hindi_latin:
            if re.search(rf'\b{w}\b', text_lower):
                return Language.HI

        english_words = ["appointment", "book", "doctor", "hospital", "facility", "cancel", "check", "emergency", "help", "slot", "today", "tomorrow", "yes", "confirm", "english"]
        eng_match_count = sum(1 for w in english_words if re.search(rf'\b{w}\b', text_lower))
        if eng_match_count > 0:
            return Language.EN

        return default_language
