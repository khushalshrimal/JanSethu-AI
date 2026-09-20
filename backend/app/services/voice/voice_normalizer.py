import re

class VoiceNormalizer:
    """
    Normalizes speech-to-text transcriptions across English, Hindi, and Marathi.
    Handles Hinglish, Marathish, noise characters, and standardizes common healthcare phrases.
    """

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        
        # 1. Basic cleaning & lowercasing
        cleaned = text.strip().lower()

        # Remove extra punctuation keeping spaces, letters, numbers, and Devanagari script characters
        # Devanagari Unicode range: \u0900-\u097F
        cleaned = re.sub(r'[^\w\s\u0900-\u097F]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # 2. Common phrase normalizations (Hindi / Hinglish)
        hinglish_replacements = {
            r'\bdoctor ko dikhana hai\b': 'book appointment',
            r'\bdoctor se milna hai\b': 'book appointment',
            r'\bappointment book karni hai\b': 'book appointment',
            r'\bappointment chahiye\b': 'book appointment',
            r'\bopd ticket chahiye\b': 'book appointment',
            r'\bdoctor ke paas jana hai\b': 'book appointment',
            r'\bkal ka slot\b': 'tomorrow slot',
            r'\baaj ka slot\b': 'today slot',
            r'\bhospital batao\b': 'search facility',
            r'\bnearby hospital\b': 'search facility',
            r'\bpas ka hospital\b': 'search facility',
        }

        # 3. Marathi phrase normalizations
        marathi_replacements = {
            r'\bमला डॉक्टरांना भेटायचे आहे\b': 'book appointment',
            r'\bमला अपॉइंटमेंट बुक करायची आहे\b': 'book appointment',
            r'\bमाझ्या जवळचे रुग्णालय शोधा\b': 'search facility',
            r'\bउद्याचा स्लॉट\b': 'tomorrow slot',
            r'\bमाझी अपॉइंटमेंट तपासा\b': 'check appointment',
            r'\bमाझी अपॉइंटमेंट रद्द करा\b': 'cancel appointment',
        }

        normalized = cleaned
        for pattern, replacement in {**hinglish_replacements, **marathi_replacements}.items():
            normalized = re.sub(pattern, replacement, normalized)

        return normalized
