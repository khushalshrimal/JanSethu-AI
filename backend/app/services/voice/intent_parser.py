import re
from enum import Enum
from typing import Tuple

class IntentEnum(str, Enum):
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    CHECK_APPOINTMENT = "CHECK_APPOINTMENT"
    CHECK_IN = "CHECK_IN"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    RESCHEDULE_APPOINTMENT = "RESCHEDULE_APPOINTMENT"
    SEARCH_FACILITY = "SEARCH_FACILITY"
    SEARCH_DOCTOR = "SEARCH_DOCTOR"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    EMERGENCY = "EMERGENCY"
    HELP = "HELP"
    REPEAT = "REPEAT"
    BACK = "BACK"
    CHANGE_LANGUAGE = "CHANGE_LANGUAGE"
    END_CALL = "END_CALL"
    UNKNOWN = "UNKNOWN"


class IntentParser:
    """
    Classifies natural language text into a controlled intent enum with confidence score.
    Supports English, Hindi, Hinglish, and Marathi.
    """

    @staticmethod
    def parse_intent(text: str) -> Tuple[IntentEnum, float]:
        if not text or not text.strip():
            return IntentEnum.UNKNOWN, 0.0

        t = text.lower().strip()

        # 1. EMERGENCY (highest priority)
        emergency_keywords = [
            "emergency", "ambulance", "casualty", "critical", "108", "accidental", "heart attack",
            "आपत्कालीन", "इमरजेंसी", "इमरजन्सी", "गंभीर", "ambulance chahiye", "saans lene", "saas lene",
            "accident", "bleeding", "chest pain", "छातीत दुखणे"
        ]
        for kw in emergency_keywords:
            if kw in t:
                return IntentEnum.EMERGENCY, 0.98

        # CHECK IN & QUEUE
        checkin_keywords = [
            "check in", "checkin", "check-in", "चेक इन", "चेक-इन",
            "check in karna", "check in kar do", "check in करायचे", "चेक इन करायचे आहे", "चेक इन करा",
            "hospital pahunch", "hospital me hoon", "hospital aagaya", "token number", "token kya hai",
            "queue mein kitne", "queue status", "mera number kab"
        ]
        for kw in checkin_keywords:
            if kw in t:
                return IntentEnum.CHECK_IN, 0.95

        # 2. END CALL
        end_keywords = [
            "bye", "end call", "cut call", "disconnect", "fon rakho", "bas ho gaya", "फोन बंद करा",
            "fon cut", "phone cut", "call cut", "cut karo", "fon kat", "call kat", "band karo", "kat do", "cut do"
        ]
        for kw in end_keywords:
            if kw in t:
                return IntentEnum.END_CALL, 0.95

        # 3. CHANGE LANGUAGE
        lang_keywords = ["english mein", "hindi mein", "marathi mein", "change language", "bhasha badlo", "इंग्रजीत", "हिंदीत", "मराठीत"]
        for kw in lang_keywords:
            if kw in t:
                return IntentEnum.CHANGE_LANGUAGE, 0.92

        # 4. CANCEL APPOINTMENT
        cancel_keywords = [
            "cancel", "radd", "रद्द", "रद्द करा", "cancel appointment", "nayi chahiye", "nahi chahiye",
            "cancel kar do", "mujhe nahi jaana", "appointment hata do", "isko cancel"
        ]
        for kw in cancel_keywords:
            if kw in t:
                return IntentEnum.CANCEL_APPOINTMENT, 0.92

        # 5. RESCHEDULE APPOINTMENT
        reschedule_keywords = [
            "reschedule", "time badlo", "date badlo", "change time", "change date", "वेळ बदला",
            "parso kar do", "kal ki jagah", "reschedule karni"
        ]
        for kw in reschedule_keywords:
            if kw in t:
                return IntentEnum.RESCHEDULE_APPOINTMENT, 0.90

        # 6. CHECK APPOINTMENT
        check_keywords = [
            "check appointment", "my appointment", "appointment status", "kab hai", "status kya hai",
            "meri appointment", "तपासा", "माझी अपॉइंटमेंट", "status dekho", "code", "book ki thi",
            "doctor ka naam", "hospital mein hai", "kitne baje hai", "kis doctor"
        ]
        for kw in check_keywords:
            if kw in t:
                return IntentEnum.CHECK_APPOINTMENT, 0.91

        # 7. CHECK AVAILABILITY
        avail_keywords = [
            "available hai", "available hain", "available hai kya", "kaun doctor available",
            "kaun available hai", "mil jaayega", "mil jayega", "slot khali", "11 baje koi",
            "slot", "available", "khali", "timing", "time", "स्लॉट", "उपलब्ध"
        ]
        for kw in avail_keywords:
            if kw in t:
                return IntentEnum.CHECK_AVAILABILITY, 0.93

        # 8. BOOK APPOINTMENT
        book_keywords = [
            "book appointment", "book", "dikhana", "milna", "doctor ko dikhana", "appointment chahiye",
            "dikhana hai", "milna hai", "भेटायचे", "बुक करायची", "slot chahiye", "opd ticket", "doctor ke paas"
        ]
        for kw in book_keywords:
            if kw in t:
                return IntentEnum.BOOK_APPOINTMENT, 0.94

        # 9. SEARCH FACILITY / HOSPITAL
        facility_keywords = [
            "search facility", "hospital", "phc", "chc", "sub-district", "baramati", "indapur", "malegaon",
            "jaipur", "pune", "mumbai", "delhi", "rehta", "rehti", "city", "area", "paas",
            "rujnalay", "hospital batao", "paas ka hospital", "nearby hospital", "रुग्णालय", "अस्पताल", "दवाखाना",
            "government hospital", "hospital ka address", "address batao"
        ]
        for kw in facility_keywords:
            if kw in t:
                return IntentEnum.SEARCH_FACILITY, 0.88

        # 9. SEARCH DOCTOR
        doctor_keywords = ["pediatrics", "pediatrician", "physician", "general medicine", "child doctor", "bacho ka doctor", "डॉक्टर", "वैद्यकीय"]
        for kw in doctor_keywords:
            if kw in t:
                return IntentEnum.SEARCH_DOCTOR, 0.87

        # 10. CHECK AVAILABILITY
        avail_keywords = ["slot", "available", "khali", "timing", "time", "स्लॉट", "उपलब्ध", "timing kya hai"]
        for kw in avail_keywords:
            if kw in t:
                return IntentEnum.CHECK_AVAILABILITY, 0.85

        # 11. REPEAT
        repeat_keywords = ["repeat", "dobara", "phir se", "phirse", "dobara suniye", "phir se bolo", "पुन्हा", "पुन्हा सांगा"]
        if t in ["0", "0.", "[0]", "0 "] or any(kw in t for kw in repeat_keywords):
            return IntentEnum.REPEAT, 0.95

        # 12. BACK
        back_keywords = ["back", "pichhe", "piche", "maage", "मागे", "wapas"]
        if t in ["9", "9.", "[9]", "9 "] or any(kw in t for kw in back_keywords):
            return IntentEnum.BACK, 0.95

        # 13. HELP
        help_keywords = ["help", "madad", "मदत", "kaise karna hai", "what can you do"]
        for kw in help_keywords:
            if kw in t:
                return IntentEnum.HELP, 0.85

        # Heuristic fallback for conversational sentences
        if len(t) > 2:
            return IntentEnum.BOOK_APPOINTMENT, 0.85

        return IntentEnum.UNKNOWN, 0.30
