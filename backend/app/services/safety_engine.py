import re
from typing import Tuple, List, Optional
from enum import Enum

class EmergencyLevel(str, Enum):
    NORMAL = "NORMAL"
    POTENTIAL_EMERGENCY = "POTENTIAL_EMERGENCY"
    HIGH_CONFIDENCE_EMERGENCY = "HIGH_CONFIDENCE_EMERGENCY"

class SafetyEngine:
    """
    Deterministic Safety & Emergency Classification Engine for JanSethu AI.
    Scans user messages for high-confidence emergency signals (Hindi, Hinglish, Marathi, English)
    BEFORE LLM processing. Does NOT diagnose medical conditions.
    """

    # General / Query patterns that should NOT trigger a high-confidence personal emergency
    GENERAL_QUERY_PATTERNS: List[str] = [
        r"kab\s+(open|khulta|chalu)\s+hai",
        r"ward\s+ke\s+baare\s+mein",
        r"department\s+kab",
        r"number\s+kya\s+hai",
        r"address\s+batao",
        r"kahan\s+hai",
        r"hote\s+hain\s+kya",
        r"hai\s+kya",
        r"kaha\s+par\s+hai",
        r"timing\s+kya\s+hai",
    ]

    # Specific Emergency Category Patterns
    BREATHING_PATTERNS: List[str] = [
        r"saa[n]?s?\s+(lene?\s+)?(mein\s+)?(bahut\s+)?dikkat",
        r"saa[n]?s?\s+na?hi?\s+aa\s+rahi",
        r"saa[n]?s?\s+phul\s+rahi",
        r"saans\s+nahi\s+aa",
        r"can'?t\s+breathe",
        r"difficulty\s+breathing",
        r"shortness\s+of\s+breath",
        r"trouble\s+breathing",
        r"श्वास.*घेण्यास.*त्रास",
        r"श्वास.*त्रास",
        r"सांस\s+नहीं\s+आ\s+रही",
        r"सांस\s+लेने\s+में\s+तकलीफ",
        r"श्वासोच्छवास",
    ]

    CHEST_PAIN_PATTERNS: List[str] = [
        r"chest\s+pain",
        r"seene?\s+mein\s+(bahut\s+)?tez\s+dard",
        r"seene?\s+mein\s+dard",
        r"heart\s+attack",
        r"dil\s+ka\s+dora",
        r"छातीत.*दुखणे",
        r"छातीत\s+दुखणे",
        r"सीने\s+में\s+दर्द",
        r"हृदयविकार",
    ]

    ACCIDENT_PATTERNS: List[str] = [
        r"accident\s+ho\s+gaya",
        r"major\s+accident",
        r"serious\s+accident",
        r"accident",
        r"दुर्घटना",
        r"अपघात",
        r"हादसा",
    ]

    BLEEDING_PATTERNS: List[str] = [
        r"bahut\s+(zyada\s+)?khoon",
        r"heavy\s+bleeding",
        r"khun\s+beh\s+raha",
        r"khoon\s+nikal\s+raha",
        r"रक्तस्राव",
        r"खून\s+बह\s+रहा",
    ]

    UNCONSCIOUS_PATTERNS: List[str] = [
        r"unconscious",
        r"behosh",
        r"chakkar\s+aake\s+gir",
        r"बेहोश",
        r"जाणीव\s+नसणे",
    ]

    EXPLICIT_EMERGENCY_PATTERNS: List[str] = [
        r"108",
        r"ambulance\s+chahiye",
        r"ambulance\s+bhejo",
        r"ambulance",
        r"emergency\s+hai",
        r"mujhe\s+emergency\s+hai",
        r"life\s+threatening",
        r"serious\s+problem",
        r"इमरजेंसी\s+है",
        r"इमरजन्सी",
        r"आपत्कालीन",
        r"आणीबाणी",
        r"गंभीर\s+अवस्था",
        r"ॲम्बुलन्स",
        r"रुग्णवाहिका",
        r"एम्बुलेंस",
    ]

    @classmethod
    def classify_emergency(cls, text: str) -> Tuple[EmergencyLevel, Optional[str], float, List[str]]:
        """
        Returns (emergency_level, emergency_type, confidence, matched_keywords)
        """
        if not text or not text.strip():
            return EmergencyLevel.NORMAL, None, 0.0, []

        t = text.lower().strip()

        # Check for general information / non-personal query patterns first
        is_general_query = any(re.search(pat, t, re.IGNORECASE) for pat in cls.GENERAL_QUERY_PATTERNS)
        has_explicit_personal_emergency = any(w in t for w in ["mujhe", "meri", "my", "me", "i ", "i'm", "patient", "papa", "पिता", "वडिल", "माझ्या"])

        matched: List[str] = []
        emergency_type: Optional[str] = None

        # Category checks
        for pat in cls.BREATHING_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                matched.append(pat)
                emergency_type = "BREATHING"

        for pat in cls.CHEST_PAIN_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                matched.append(pat)
                if not emergency_type:
                    emergency_type = "CHEST_PAIN"

        for pat in cls.ACCIDENT_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                matched.append(pat)
                if not emergency_type:
                    emergency_type = "ACCIDENT"

        for pat in cls.BLEEDING_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                matched.append(pat)
                if not emergency_type:
                    emergency_type = "BLEEDING"

        for pat in cls.UNCONSCIOUS_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                matched.append(pat)
                if not emergency_type:
                    emergency_type = "UNCONSCIOUS"

        for pat in cls.EXPLICIT_EMERGENCY_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                matched.append(pat)
                if not emergency_type:
                    emergency_type = "GENERAL_EMERGENCY"

        if not matched:
            return EmergencyLevel.NORMAL, None, 0.0, []

        # If phrase matches a general query pattern AND lacks explicit personal emergency context, flag as POTENTIAL_EMERGENCY
        if is_general_query and not has_explicit_personal_emergency and "department" in t:
            return EmergencyLevel.POTENTIAL_EMERGENCY, emergency_type, 0.50, matched

        return EmergencyLevel.HIGH_CONFIDENCE_EMERGENCY, emergency_type or "GENERAL_EMERGENCY", 0.99, matched

    @classmethod
    def check_emergency(cls, text: str) -> Tuple[bool, float, List[str]]:
        """
        Backwards compatibility method.
        Returns (is_emergency, confidence, matched_keywords)
        """
        level, _, conf, matched = cls.classify_emergency(text)
        is_emerg = (level == EmergencyLevel.HIGH_CONFIDENCE_EMERGENCY)
        return is_emerg, conf, matched
