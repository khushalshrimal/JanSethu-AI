import re
from typing import Dict, Any, Optional

class EntityExtractor:
    """
    Extracts entities (facility search string, department, doctor, date, time, confirmation, pincode)
    from natural language text in English, Hindi, Hinglish, and Marathi.
    Does NOT invent DB IDs — returns search strings for real DB querying.
    """

    @staticmethod
    def extract_entities(text: str) -> Dict[str, Any]:
        if not text:
            return {}

        entities: Dict[str, Any] = {}
        t = text.lower().strip()

        no_keywords = ["nahi", "nahin", "no", "don't book", "don't cancel", "mat karo", "nayi", "नाही", "नको"]
        yes_keywords = ["haan", "ji haan", "yes", "confirm", "kar do", "kardo", "radd", "confirm karo", "book it", "okay", "ok", "हो", "होय", "करा", "कन्फर्म करा"]

        for nk in no_keywords:
            if re.search(rf'\b{re.escape(nk)}\b', t) or t == nk:
                entities["confirmation"] = False
                break

        if "confirmation" not in entities:
            for yk in yes_keywords:
                if re.search(rf'\b{re.escape(yk)}\b', t) or t == yk:
                    entities["confirmation"] = True
                    break

        # 2. Date Extraction
        if any(w in t for w in ["tomorrow", "kal", "udya", "उद्या", "कल"]):
            entities["date"] = "tomorrow"
        elif any(w in t for w in ["today", "aaj", "aajcha", "आज"]):
            entities["date"] = "today"
        elif any(w in t for w in ["parso", "day after tomorrow"]):
            entities["date"] = "day_after_tomorrow"

        # 3. Facility Location Keywords
        facility_candidates = [
            "jaipur", "pune", "mumbai", "delhi", "bangalore", "baramati", "indapur", "malegaon",
            "sub-district", "phc", "chc", "government hospital", "city hospital", "hospital"
        ]
        for fc in facility_candidates:
            if fc in t:
                entities["facility_search"] = fc
                break

        if "facility_search" not in entities:
            # Dynamic location extraction (e.g. "Main Jaipur mein rehta hoon" -> "jaipur")
            loc_match = re.search(r'\b([a-zA-Z]{3,15})\s+\b(mein|city|area|pincode|paas|me)\b', t)
            if loc_match:
                cand = loc_match.group(1).lower()
                non_city_words = {
                    "namaste", "namaskar", "hello", "hi", "main", "aap", "aapka", "mujhe", "mera", "meri",
                    "koi", "is", "seene", "dard", "fever", "saans", "doctor", "hospital", "kal", "aaj", "parso",
                    "subah", "shaam", "baje", "chahiye", "milna", "jaana", "karte", "karne", "lene", "aane",
                    "dikhane", "samajh", "rahi", "raha", "hote", "batao", "bataiye", "help", "bhejo"
                }
                if cand not in non_city_words:
                    entities["facility_search"] = cand

        # 4. Department & Service Keywords
        dept_candidates = {
            "orthopedics": ["orthopedics", "ortho", "haddi", "bone", "jod", "हाडे", "leg ka operation", "operation", "leg operation", "knee", "surgery", "haddi ka doctor"],
            "pediatrics": ["pediatrics", "pediatrician", "child", "bacho", "bache", "bachhe", "bachha", "baby", "बालक", "लहान मुले"],
            "gynecology": ["gynecology", "maternity", "women", "pregnancy", "pregnant", "garbhvati", "महिला", "स्त्रीरोग"],
            "dentistry": ["dentistry", "dental", "daant", "teeth", "दांत"],
            "dermatology": ["dermatology", "skin", "khajli", "skin allergy", "त्वचा"],
            "ophthalmology": ["ophthalmology", "eye", "aankh", "drishti", "डोळे"],
            "general medicine": ["general medicine", "physician", "general", "fever", "bukhar", "pet dard", "pet mein dard", "pet", "sar dard", "dard", "headache", "सामान्य"],
            "emergency": ["emergency", "casualty", "आपत्कालीन", "saans lene mein dikkat", "saans nahi aara", "saas lene"]
        }
        for d_key, d_words in dept_candidates.items():
            if any(re.search(rf'\b{re.escape(dw)}\b', t) or dw in t for dw in d_words):
                entities["department"] = d_key
                break

        # 5. Doctor Name Keywords
        doctor_candidates = ["lakshya", "amit", "priya", "rajesh", "sharma", "patel", "deshmukh", "kulkarni", "patil"]
        for doc_c in doctor_candidates:
            if doc_c in t:
                entities["doctor_search"] = doc_c
                break

        # 6. Pincode Extraction (6 digits)
        pincode_match = re.search(r'\b\d{6}\b', t)
        if pincode_match:
            entities["pincode"] = pincode_match.group(0)
            if "facility_search" not in entities:
                entities["facility_search"] = pincode_match.group(0)


        # 7. Confirmation Code Extraction (JS-2026-XXXXXX or 6-char hex)
        code_match = re.search(r'js-\d{4}-[a-z0-9]{6}', t, re.IGNORECASE)
        if code_match:
            entities["confirmation_code"] = code_match.group(0).upper()

        # 8. Time Extraction (e.g. 9 baje, 11 am, 09:00, 10:30)
        time_match = re.search(r'(\d{1,2})(:(\d{2}))?\s*(am|pm|baje|बजे)?', t)
        if time_match and any(kw in t for kw in ["baje", "am", "pm", ":", "बजे"]):
            hr = int(time_match.group(1))
            mn = int(time_match.group(3)) if time_match.group(3) else 0
            period = time_match.group(4)
            if period == "pm" and hr < 12:
                hr += 12
            entities["time"] = f"{hr:02d}:{mn:02d}"

        return entities
