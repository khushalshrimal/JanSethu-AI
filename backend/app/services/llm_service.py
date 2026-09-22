import re
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import httpx
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.enums import Language
from app.schemas.nlu import NLUIntent, NLUEntities, NLUAnalysisResponse
from app.services.safety_engine import SafetyEngine

logger = logging.getLogger(__name__)

class DeterministicNLUParser:
    """
    Fallback & High-Speed Deterministic Multi-Lingual NLU Parser for JanSethu AI.
    Handles intent classification, multi-entity extraction, date/time normalization,
    name & location parsing, and correction detection across Hindi, Hinglish, Marathi, and English.
    """

    KNOWN_CITIES: Dict[str, str] = {
        "jaipur": "Jaipur", "ajmer": "Ajmer", "pune": "Pune", "mumbai": "Mumbai",
        "delhi": "Delhi", "baramati": "Baramati", "indapur": "Indapur", "malegaon": "Malegaon",
        "satara": "Satara", "solapur": "Solapur", "nashik": "Nashik", "kolhapur": "Kolhapur",
        "sangavi": "Sangavi",
        "जयपुर": "Jaipur", "अजमेर": "Ajmer", "पुणे": "Pune", "मुंबई": "Mumbai", "दिल्ली": "Delhi",
        "बारामती": "Baramati", "इंदापूर": "Indapur", "सातारा": "Satara", "सोलापूर": "Solapur",
        "नाशिक": "Nashik", "कोल्हापूर": "Kolhapur"
    }

    @classmethod
    def parse(
        cls,
        text: str,
        conversation_context: Optional[Dict[str, Any]] = None,
        language_hint: Optional[str] = None
    ) -> NLUAnalysisResponse:
        t = text.strip()
        t_lower = t.lower()

        # 1. Detect Language
        lang = cls._detect_language(t_lower, text, language_hint)

        # 2. Safety / Emergency Check
        level, emerg_type, safety_conf, matched_signals = SafetyEngine.classify_emergency(t)
        is_emergency = (level.value != "NORMAL")

        entities_dict: Dict[str, Any] = {
            "symptoms": []
        }

        # 3. Correction Detection (e.g., "Nahi, Jaipur nahi Ajmer")
        is_correction, corrected_field, corrected_val = cls._detect_correction(t_lower, conversation_context)
        if is_correction:
            entities_dict["is_correction"] = True
            entities_dict["corrected_field"] = corrected_field
            if corrected_field in ["city", "location"]:
                entities_dict["city"] = corrected_val
                entities_dict["location"] = corrected_val

        # 4. Extract Entities
        cls._extract_entities(t_lower, text, entities_dict, conversation_context)

        # 5. Determine Intent
        if is_emergency:
            intent = NLUIntent.EMERGENCY
            confidence = 0.99
            entities_dict["ambulance_requested"] = True if any(w in t_lower for w in ["ambulance", "108", "ॲम्बुलन्स", "एम्बुलेंस", "रुग्णवाहिका"]) else False
        else:
            intent, confidence = cls._classify_intent(t_lower, text, entities_dict, conversation_context)

        # 6. Synchronize Alias Fields in Entities
        if entities_dict.get("doctor_name") and not entities_dict.get("doctor"):
            entities_dict["doctor"] = entities_dict["doctor_name"]
        elif entities_dict.get("doctor") and not entities_dict.get("doctor_name"):
            entities_dict["doctor_name"] = entities_dict["doctor"]

        if entities_dict.get("facility_name") and not entities_dict.get("facility"):
            entities_dict["facility"] = entities_dict["facility_name"]
        elif entities_dict.get("facility") and not entities_dict.get("facility_name"):
            entities_dict["facility_name"] = entities_dict["facility"]

        if entities_dict.get("specialty") and not entities_dict.get("speciality"):
            entities_dict["speciality"] = entities_dict["specialty"]
        elif entities_dict.get("speciality") and not entities_dict.get("specialty"):
            entities_dict["specialty"] = entities_dict["speciality"]

        # Build NLUEntities model
        entities_model = NLUEntities(**entities_dict)

        # Determine Missing Information & Backend Flags
        missing_info = cls._compute_missing_info(intent, entities_model)
        requires_db = intent in [
            NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH, NLUIntent.FIND_DOCTOR,
            NLUIntent.DOCTOR_SEARCH, NLUIntent.FIND_SPECIALIST, NLUIntent.CHECK_AVAILABILITY,
            NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.SLOT_SEARCH, NLUIntent.BOOK_APPOINTMENT,
            NLUIntent.CANCEL_APPOINTMENT, NLUIntent.RESCHEDULE_APPOINTMENT, NLUIntent.MY_APPOINTMENTS,
            NLUIntent.EMERGENCY, NLUIntent.AMBULANCE_REQUEST, NLUIntent.EMERGENCY_FACILITY_SEARCH
        ]
        requires_conf = intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.CANCEL_APPOINTMENT, NLUIntent.RESCHEDULE_APPOINTMENT]

        return NLUAnalysisResponse(
            intent=intent,
            entities=entities_model,
            language=lang,
            emergency=is_emergency,
            emergency_signals=matched_signals,
            missing_information=missing_info,
            requires_database_lookup=requires_db,
            requires_confirmation=requires_conf,
            confidence=confidence,
            raw_text=text,
            normalized_text=t_lower
        )

    @classmethod
    def _detect_language(cls, text_lower: str, raw_text: str, language_hint: Optional[str]) -> Language:
        marathi_markers = ["मला", "पाहिजे", "आरोग्य", "दाखवायचे", "नाही", "होय", "करायची", "उद्या", "माझे", "रुग्णालय", "आहे", "वडिलांना", "नाव", "माझं", "त्वचारोग", "तज्ज्ञ", "श्वास", "हवा"]
        if any(w in text_lower or w in raw_text for w in marathi_markers):
            return Language.MR

        hindi_markers = ["मुझे", "चाहिए", "अस्पताल", "दिखाना", "नहीं", "हाँ", "करना", "कल", "परसों", "है", "हैन", "मेरा", "मेरी", "नाम", "रमेश", "पापा", "सांस", "दिक्कत"]
        if any(w in text_lower or w in raw_text for w in hindi_markers):
            return Language.HI

        if language_hint and language_hint.upper() in Language.__members__:
            return Language(language_hint.upper())

        # Check for Devanagari script characters
        if re.search(r"[\u0900-\u097F]", raw_text):
            return Language.HI

        return Language.HI

    @classmethod
    def _detect_correction(
        cls,
        text_lower: str,
        context: Optional[Dict[str, Any]]
    ) -> tuple[bool, Optional[str], Optional[str]]:
        corr_patterns = [
            r"(?:\bnahi\b|\bnahin\b|\bna\b|\bno\b|नहीं|नको)\s*[,;\-]?\s*(?:not\s+|[a-z\u0900-\u097f]+\s+(?:nahi|nahin|नहीं)\s+)?([a-z\u0900-\u097f]{3,15})",
            r"(?:\bchange\b|\bbadlo\b|बदला)\s+([a-z\u0900-\u097f]{3,15})"
        ]
        for p in corr_patterns:
            m = re.search(p, text_lower, re.IGNORECASE)
            if m:
                raw_val = m.group(1).strip().lower()
                if raw_val not in ["karo", "karna", "batao", "chahiye", "hai", "nahi", "nahin", "maste", "namaste"]:
                    val = cls.KNOWN_CITIES.get(raw_val, raw_val.capitalize())
                    return True, "city", val
        return False, None, None

    @classmethod
    def _extract_entities(
        cls,
        text_lower: str,
        raw_text: str,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ):
        # 1. Patient Name & Relation
        name_map = {
            "ramesh": "Ramesh", "रमेश": "Ramesh",
            "rahul": "Rahul", "राहुल": "Rahul",
            "priya": "Priya", "suresh": "Suresh", "amit": "Amit"
        }
        name_patterns = [
            r"(?:my\s+name\s+is|i\s+am|i'm)\s+([a-zA-Z\u0900-\u097f]+)",
            r"(?:mera\s+naam|meri\s+naam|naam|मेरा\s+नाम|माझं\s+नाव)\s+([a-zA-Z\u0900-\u097f]+)",
            r"^(?:im|i\s+am)\s+([a-zA-Z\u0900-\u097f]+)$"
        ]
        for p in name_patterns:
            m = re.search(p, text_lower, re.IGNORECASE)
            if m:
                raw_cand = m.group(1).strip()
                candidate_name = name_map.get(raw_cand.lower(), raw_cand.title())
                entities["patient_name"] = candidate_name
                break

        # Standalone name match if input is simple name like "Ramesh" / "रमेश"
        if not entities.get("patient_name") and len(raw_text.split()) <= 3:
            clean_word = raw_text.strip().rstrip(".").rstrip("!")
            if clean_word.lower() in name_map:
                entities["patient_name"] = name_map[clean_word.lower()]

        rel_patterns = {
            "father": ["father", "papa", "pita", "dad", "पिता", "पापा", "वडिल", "वडिलांना"],
            "mother": ["mother", "mummy", "maa", "mata", "माता", "आई", "आईला"],
            "child": ["son", "daughter", "child", "baby", "bachha", "bache", "मुलाला", "मूल"],
            "self": ["my", "mera", "meri", "i ", "me ", "माझे", "मला"]
        }
        for rel_k, rel_words in rel_patterns.items():
            if any((w in text_lower if re.search(r"[\u0900-\u097F]", w) else bool(re.search(rf"\b{re.escape(w)}\b", text_lower))) for w in rel_words):
                entities["patient_relation"] = rel_k
                break

        # 2. Locations / Cities / Pincodes
        pincode_match = re.search(r"\b\d{6}\b", text_lower)
        if pincode_match:
            entities["pincode"] = pincode_match.group(0)
            if not entities.get("city") and not entities.get("location"):
                entities["location"] = pincode_match.group(0)

        if not entities.get("city"):
            for k_city, v_city in cls.KNOWN_CITIES.items():
                if k_city in text_lower and not re.search(rf"{re.escape(k_city)}\s+(?:nahi|nahin|नहीं)", text_lower):
                    entities["city"] = v_city
                    entities["location"] = v_city
                    break

        if not entities.get("city"):
            loc_match = re.search(r"\b([a-zA-Z\u0900-\u097f]{3,15})\s+\b(mein|city|area|pincode|paas|me|मध्य)\b", text_lower)
            if loc_match:
                candidate = loc_match.group(1).lower()
                non_city_words = {
                    "namaste", "namaskar", "hello", "hi", "main", "aap", "aapka", "mujhe", "mera", "meri",
                    "koi", "is", "seene", "dard", "fever", "saans", "doctor", "hospital", "kal", "aaj", "parso",
                    "subah", "shaam", "baje", "chahiye", "milna", "jaana", "karte", "karne", "lene", "aane",
                    "dikhane", "samajh", "rahi", "raha", "hote", "batao", "bataiye", "help", "bhejo",
                    "marathi", "hindi", "english", "vel", "badla", "udya", "udyasathi", "उद्या", "उद्यासाठी", "वेळ", "बदला"
                }
                if candidate not in non_city_words:
                    entities["location"] = candidate.capitalize()
                    entities["city"] = candidate.capitalize()

        # Location standalone phrase like "Baramati mein", "Sangavi area"
        if not entities.get("location"):
            if "baramati" in text_lower or "बारामती" in text_lower:
                entities["location"] = "Baramati"
                entities["city"] = "Baramati"
            elif "pune" in text_lower or "पुणे" in text_lower:
                entities["location"] = "Pune"
                entities["city"] = "Pune"

        # 3. Specialty & Department Mapping
        dept_candidates = {
            "Dermatology": ["dermatology", "dermatologist", "skin", "khajli", "skin allergy", "त्वचा", "त्वचारोग", "त्वचारोग तज्ज्ञ"],
            "Pediatrics": ["pediatrics", "pediatrician", "child", "bacho", "bachon", "bache", "bachhe", "bachha", "baby", "बालक", "लहान मुले", "बालरोग", "लहान मुलांचा", "मुलांचा"],
            "Orthopedics": ["orthopedics", "orthopedic", "ortho", "haddi", "bone", "jod", "हाडे", "leg ka operation", "knee", "haddi ka doctor", "अस्थिरोग", "हाडांचा"],
            "Gynecology": ["gynecology", "gynecologist", "maternity", "women", "pregnancy", "pregnant", "garbhvati", "महिला", "स्त्रीरोग"],
            "ENT": ["ent", "e.n.t", "kaaan naak gala", "नाक कान घसा"],
            "Cardiology": ["cardiology", "cardiologist", "heart", "dil", "हृदयरोग", "हृदयरोग तज्ज्ञ"],
            "Ophthalmology": ["ophthalmology", "ophthalmologist", "eye", "aankh", "aankhon", "aankh ke", "डोळे", "डोळ्यांचा"],
            "Dentistry": ["dentistry", "dentist", "dental", "tooth", "teeth", "daant", "dant", "tooth pain", "दांत", "दांतांचा"],
            "General Medicine": ["general medicine", "physician", "general", "fever", "bukhar", "pet dard", "headache", "सामान्य", "ताप", "पोटदुखी"]
        }
        for dept_name, keywords in dept_candidates.items():
            for kw in keywords:
                if re.search(r"[\u0900-\u097F]", kw):
                    matched = kw in text_lower
                else:
                    matched = bool(re.search(rf"\b{re.escape(kw)}\b", text_lower, re.IGNORECASE))
                if matched:
                    entities["department"] = dept_name
                    entities["specialty"] = dept_name
                    entities["speciality"] = dept_name
                    break
            if entities.get("specialty"):
                break

        # 4. Symptoms
        symptom_keywords = [
            "fever", "bukhar", "pet dard", "headache", "sar dard", "khansi", "cough", "cold",
            "body pain", "dard", "saans lene mein dikkat", "breathing trouble", "skin allergy",
            "दुखणे", "ताप", "डोकेदुखी", "पोटदुखी"
        ]
        for sym in symptom_keywords:
            if sym in text_lower or sym in raw_text:
                if sym not in entities["symptoms"]:
                    entities["symptoms"].append(sym)
                if not entities.get("service"):
                    entities["service"] = sym

        # 5. Doctor Search
        doc_match = re.search(r"\b(dr\.?\s+[a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text_lower, re.IGNORECASE)
        if doc_match:
            doc_val = doc_match.group(1).title()
            doc_val = re.sub(r"\s+\b(Available|Hain|Hain\?|Ko|Ka|Ki|Ke|Se|Mein|Me|Batao|Bataiye|Doctor|Doctors)\b.*$", "", doc_val, flags=re.IGNORECASE).strip()
            entities["doctor_name"] = doc_val
            entities["doctor"] = doc_val
        else:
            known_doctors = ["dr lakshya", "dr. lakshya", "lakshya", "dr sharma", "dr. sharma", "dr patel", "dr amit", "dr priya", "dr. rajesh sharma", "डॉ. राजेश शर्मा"]
            for doc_k in known_doctors:
                if doc_k in text_lower:
                    d_title = "Dr. Rajesh Sharma" if "sharma" in doc_k or "rajesh" in doc_k or "शर्मा" in doc_k else doc_k.title()
                    entities["doctor_name"] = d_title
                    entities["doctor"] = d_title
                    break

        # Referral ID extraction
        ref_match = re.search(r"\b(JS-[A-Z0-9\-]{4,20})\b", raw_text, re.IGNORECASE)
        if ref_match:
            entities["referral_id"] = ref_match.group(1).upper()

        # 6. Facility Search & Type
        fac_type_patterns = {
            "PHC": ["phc", "primary health center", "प्राथमिक आरोग्य केंद्र"],
            "CHC": ["chc", "community health center", "ग्रामीण रुग्णालय"],
            "DISTRICT_HOSPITAL": ["district hospital", "sub-district hospital", "government hospital", "उपजिल्हा रुग्णालय", "सरकारी अस्पताल", "सरकारी रुग्णालय"],
            "PRIVATE_HOSPITAL": ["private hospital", "private clinic"]
        }
        for ft_k, ft_words in fac_type_patterns.items():
            if any(w in text_lower for w in ft_words):
                entities["facility_type"] = ft_k
                break

        fac_match = re.search(r"\b(hospital\s+[a-zA-Z0-9]+|[a-zA-Z0-9\.]+(?:\s+[a-zA-Z0-9\.]+){0,2}\s+hospital)\b", text_lower, re.IGNORECASE)
        if fac_match and fac_match.group(1).strip().lower() not in ["hospital", "nearby hospital", "mein hospital", "aas paas hospital"]:
            raw_fac = fac_match.group(1).strip()
            raw_fac = re.sub(r"^(?:show\s+|find\s+|doctors\s+|doctor\s+|in\s+|near\s+|at\s+)+", "", raw_fac, flags=re.IGNORECASE).strip()
            title_fac = "SMS Hospital" if raw_fac.lower() == "sms hospital" else raw_fac.title()
            entities["facility_name"] = title_fac
            entities["facility"] = title_fac
        else:
            known_facilities = ["sms hospital", "hospital a", "baramati hospital", "sub-district hospital", "city hospital", "phc baramati", "government hospital", "chc indapur"]
            for fac_k in known_facilities:
                if fac_k in text_lower:
                    title_fac = "SMS Hospital" if fac_k == "sms hospital" else fac_k.title()
                    entities["facility_name"] = title_fac
                    entities["facility"] = title_fac
                    break

        # 7. Dates & Times Normalization
        if any(w in text_lower for w in ["parso", "day after tomorrow"]):
            entities["date"] = "day_after_tomorrow"
        elif any(w in text_lower for w in ["tomorrow", "kal", "udya", "उद्या", "कल"]):
            entities["date"] = "tomorrow"
        elif any(w in text_lower for w in ["today", "aaj", "aajcha", "आज"]):
            entities["date"] = "today"

        if any(w in text_lower for w in ["morning", "subah", "sakali", "सकाळी", "सुबह"]):
            entities["time_period"] = "morning"
        elif any(w in text_lower for w in ["afternoon", "dopahar", "दुपारी", "दोपहर"]):
            entities["time_period"] = "afternoon"
        elif any(w in text_lower for w in ["evening", "shaam", "sandhyakali", "संध्याकाळी", "शाम"]):
            entities["time_period"] = "evening"

        time_match = re.search(r"(\d{1,2})\s*(::?(\d{2}))?\s*(am|pm|baje|बजे|वाजता)?", text_lower)
        if time_match and any(kw in text_lower for kw in ["baje", "am", "pm", ":", "बजे", "वाजता"]):
            hr = int(time_match.group(1))
            mn = int(time_match.group(3)) if time_match.group(3) else 0
            period = time_match.group(4)
            if period == "pm" and hr < 12:
                hr += 12
            elif period in ["baje", "बजे", "वाजता"] and hr in range(1, 8):
                hr += 12
            entities["time"] = f"{hr:02d}:{mn:02d}"

        # 8. Action Intent Flags
        if any(w in text_lower for w in ["book", "book appointment", "appointment chahiye", "बुक"]):
            entities["appointment_requested"] = True
        if any(w in text_lower for w in ["ambulance", "108", "ॲम्बुलन्स", "एम्बुलेंस", "रुग्णवाहिका"]):
            entities["ambulance_requested"] = True

        # 9. Context Fallbacks
        if context:
            if not entities.get("patient_name") and context.get("patient_name"):
                entities["patient_name"] = context["patient_name"]
            if not entities.get("location") and context.get("location"):
                entities["location"] = context["location"]
                entities["city"] = context["location"]
            if not entities.get("specialty") and context.get("specialty"):
                entities["specialty"] = context["specialty"]
                entities["speciality"] = context["specialty"]

    @classmethod
    def _classify_intent(
        cls,
        text_lower: str,
        raw_text: str,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[NLUIntent, float]:
        # 1. Name & Greetings
        if entities.get("patient_name") and len(raw_text.split()) <= 4 and not any(w in text_lower for w in ["doctor", "hospital", "book", "chahiye"]):
            return NLUIntent.PROVIDE_NAME, 0.98

        greeting_patterns = [r"\bhello\b", r"\bnamaste\b", r"\bhi\b", r"\bnamaskar\b", r"नमस्ते", r"नमस्कार"]
        if any(re.search(p, text_lower, re.IGNORECASE) for p in greeting_patterns) and not any(w in text_lower for w in ["hospital", "doctor", "book", "chahiye", "available"]):
            return NLUIntent.GENERAL_GREETING, 0.95

        # 2. Location Provide
        if entities.get("location") and len(raw_text.split()) <= 3 and not any(w in text_lower for w in ["doctor", "hospital", "book", "chahiye", "badlo", "बदला", "cancel", "reschedule", "radd"]):
            return NLUIntent.PROVIDE_LOCATION, 0.95

        # 3. Emergency / Ambulance
        if entities.get("ambulance_requested") or any(w in text_lower for w in ["ambulance", "108", "ॲम्बुलन्स", "एम्बुलेंस"]):
            return NLUIntent.AMBULANCE_REQUEST, 0.98

        # 4. Referral Lookup
        if entities.get("referral_id") or "referral" in text_lower:
            return NLUIntent.REFERRAL_LOOKUP, 0.96

        # 5. Language Change
        if any(w in text_lower for w in ["english mein", "hindi mein", "marathi mein", "change language", "bhasha badlo", "english", "hindi", "marathi", "इंग्रजी", "हिंदी"]):
            if any(w in text_lower for w in ["switch", "change", "mein", "batao", "bhasha", "भाषा", "करा", "कर"]):
                return NLUIntent.LANGUAGE_CHANGE, 0.95

        # 6. Appointments & Status Queries / Management
        if any(w in text_lower for w in ["my appointment", "meri appointment", "appointment dekho", "status kya hai", "माझी अपॉइंटमेंट", "active appointments", "appointments"]):
            if not any(w in text_lower for w in ["book", "cancel", "radd", "reschedule"]):
                return NLUIntent.MY_APPOINTMENTS, 0.93

        if any(w in text_lower for w in ["cancel", "radd", "रद्द", "कॅन्सल"]):
            return NLUIntent.CANCEL_APPOINTMENT, 0.94

        if any(w in text_lower for w in ["reschedule", "time badlo", "date badlo", "वेळ बदला"]):
            return NLUIntent.RESCHEDULE_APPOINTMENT, 0.93

        # 7. Booking & Confirmations
        if any(w in text_lower for w in ["book kar do", "book it", "book appointment", "book", "बुक"]):
            return NLUIntent.BOOK_APPOINTMENT, 0.96

        if any(w in text_lower for w in ["confirm", "kardo", "kar do", "haan", "yes", "कन्फर्म"]):
            if any(w in text_lower for w in ["book", "appointment"]):
                return NLUIntent.BOOK_APPOINTMENT, 0.92
            return NLUIntent.CONFIRM_APPOINTMENT, 0.90

        # 8. Doctor & Specialist Search & Availability
        if entities.get("doctor") or entities.get("doctor_name") or "dr." in text_lower or "dr " in text_lower:
            if any(w in text_lower for w in ["slot", "timing", "available", "khali", "स्लॉट", "उपलब्ध", "kab", "कधी"]):
                return NLUIntent.CHECK_AVAILABILITY, 0.94
            return NLUIntent.FIND_DOCTOR, 0.92

        if entities.get("specialty") or entities.get("speciality"):
            return NLUIntent.FIND_SPECIALIST, 0.95

        if "doctor" in text_lower or "डॉक्टर" in text_lower:
            return NLUIntent.FIND_DOCTOR, 0.90

        # 9. Facility Search
        if any(w in text_lower for w in ["hospital", "chahiye", "batao", "nearby", "paas", "रुग्णालय", "अस्पताल", "दवाखाना"]):
            return NLUIntent.FIND_FACILITY, 0.93

        # 10. General Help & Thanks
        if any(w in text_lower for w in ["thank you", "thanks", "dhanyawad", "धन्यवाद", "आभारी आहे"]):
            return NLUIntent.THANK_YOU, 0.95

        if any(w in text_lower for w in ["bye", "goodbye", "alvida", "पुन्हा भेटू"]):
            return NLUIntent.GOODBYE, 0.95

        if any(w in text_lower for w in ["help", "madad", "मदत", "kaise karein", "how can"]):
            return NLUIntent.MEDICAL_HELP, 0.90

        # 11. Symptom Report
        if entities.get("symptoms"):
            return NLUIntent.SYMPTOM_REPORT, 0.88

        return NLUIntent.UNKNOWN, 0.40

    @classmethod
    def _compute_missing_info(cls, intent: NLUIntent, entities: NLUEntities) -> List[str]:
        missing: List[str] = []
        if intent in [NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_DOCTOR, NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH, NLUIntent.DOCTOR_SEARCH]:
            if not entities.location and not entities.city and not entities.pincode:
                missing.append("location")
            if intent == NLUIntent.FIND_SPECIALIST and not entities.specialty and not entities.speciality:
                missing.append("specialty")
        elif intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.CHECK_AVAILABILITY, NLUIntent.SLOT_SEARCH]:
            if not entities.location and not entities.city and not entities.facility:
                missing.append("location")
            if not entities.date:
                missing.append("date")
        return missing


class LLMService:
    """
    Unified LLM / NLU Backend Service for JanSethu AI.
    Handles communication with configured LLM Provider (NVIDIA / OpenAI / Gemini / Ollama / Development)
    and validates structured outputs matching NLUAnalysisResponse.
    """

    @classmethod
    async def analyze_nlu(
        cls,
        message: str,
        conversation_context: Optional[Dict[str, Any]] = None,
        language_hint: Optional[str] = None
    ) -> NLUAnalysisResponse:
        """
        Main entry point for NLU message analysis.
        Runs deterministic safety check, attempts configured LLM provider,
        and falls back gracefully to DeterministicNLUParser on any failure or development mode.
        """
        # 1. Deterministic Emergency Safety Layer
        level, emerg_type, conf, matched_signals = SafetyEngine.classify_emergency(message)
        if level.value == "HIGH_CONFIDENCE_EMERGENCY":
            fallback = DeterministicNLUParser.parse(message, conversation_context, language_hint)
            fallback.intent = NLUIntent.EMERGENCY
            fallback.emergency = True
            fallback.emergency_signals = matched_signals
            fallback.confidence = 0.99
            return fallback

        # 2. Check Provider Setup
        provider = settings.LLM_PROVIDER.lower()
        if provider == "development" or not settings.LLM_API_KEY:
            logger.info("Using Local Deterministic NLU Engine (LLM_PROVIDER=%s)", provider)
            return DeterministicNLUParser.parse(message, conversation_context, language_hint)

        # 3. External LLM Provider Call (NVIDIA / OpenAI / Gemini / Ollama / Custom API)
        try:
            return await cls._call_external_llm(message, conversation_context, language_hint)
        except Exception as exc:
            logger.warning("External LLM API call failed (%s). Falling back to Deterministic NLU Parser.", str(exc))
            res = DeterministicNLUParser.parse(message, conversation_context, language_hint)
            res.error = f"LLM provider failed: {str(exc)}"
            return res

    @classmethod
    def _resolve_llm_endpoint_url(cls, provider: str, base_url: str) -> str:
        """
        Resolves provider-aware API endpoint URL and ensures /chat/completions suffix is present.
        """
        target = base_url.strip() if base_url and base_url.strip() else ""

        if not target:
            if provider == "nvidia":
                target = "https://integrate.api.nvidia.com/v1"
            elif provider == "openai":
                target = "https://api.openai.com/v1"
            elif provider == "gemini":
                target = "https://generativelanguage.googleapis.com/v1beta/openai"
            elif provider == "ollama":
                target = "http://localhost:11434/v1"
            else:
                target = "https://integrate.api.nvidia.com/v1"

        target = target.rstrip("/")
        if not target.endswith("/chat/completions"):
            target = f"{target}/chat/completions"

        return target

    @classmethod
    async def _call_external_llm(
        cls,
        message: str,
        conversation_context: Optional[Dict[str, Any]] = None,
        language_hint: Optional[str] = None
    ) -> NLUAnalysisResponse:
        system_prompt = (
            "You are the NLU parser for JanSethu AI healthcare platform. "
            "Examine the user message and return ONLY a raw valid JSON object with NO markdown, NO preamble, NO backticks.\n"
            "Required JSON format:\n"
            "{\n"
            '  "intent": "GENERAL_GREETING" | "PROVIDE_NAME" | "PROVIDE_LOCATION" | "FIND_FACILITY" | "FIND_DOCTOR" | "FIND_SPECIALIST" | "BOOK_APPOINTMENT" | "CHECK_AVAILABILITY" | "MY_APPOINTMENTS" | "CANCEL_APPOINTMENT" | "EMERGENCY" | "AMBULANCE_REQUEST" | "UNKNOWN",\n'
            '  "entities": {\n'
            '     "patient_name": string | null,\n'
            '     "patient_relation": string | null,\n'
            '     "city": string | null,\n'
            '     "location": string | null,\n'
            '     "pincode": string | null,\n'
            '     "facility_name": string | null,\n'
            '     "doctor_name": string | null,\n'
            '     "specialty": string | null,\n'
            '     "symptoms": list[string],\n'
            '     "date": string | null,\n'
            '     "time": string | null,\n'
            '     "is_correction": boolean\n'
            "  },\n"
            '  "language": "HI" | "MR" | "EN",\n'
            '  "emergency": boolean,\n'
            '  "confidence": float\n'
            "}"
        )

        provider = settings.LLM_PROVIDER.lower()
        url = cls._resolve_llm_endpoint_url(provider, settings.LLM_BASE_URL)

        headers = {
            "Content-Type": "application/json"
        }
        if settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

        payload = {
            "model": settings.LLM_MODEL or "meta/llama-3.1-70b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Message: {message}\nContext: {json.dumps(conversation_context or {})}"}
            ],
            "temperature": 0.1,
            "max_tokens": 512
        }

        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        raw_content = data["choices"][0]["message"]["content"].strip()
        
        # Strip markdown fences if LLM surrounds output in ```json ... ```
        clean_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.IGNORECASE)
        clean_content = re.sub(r"\s*```$", "", clean_content)
        clean_content = clean_content.strip()

        try:
            parsed = json.loads(clean_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", clean_content, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                raise ValueError(f"Could not parse valid JSON from LLM response content.")

        intent_str = str(parsed.get("intent", "UNKNOWN")).upper()
        try:
            intent_enum = NLUIntent(intent_str)
        except ValueError:
            intent_enum = NLUIntent.UNKNOWN

        entities_dict = parsed.get("entities", {})
        if not isinstance(entities_dict, dict):
            entities_dict = {}

        entities_obj = NLUEntities(**entities_dict)
        
        lang_str = str(parsed.get("language", "HI")).upper()
        try:
            lang_enum = Language(lang_str)
        except ValueError:
            lang_enum = Language.HI

        return NLUAnalysisResponse(
            intent=intent_enum,
            entities=entities_obj,
            language=lang_enum,
            emergency=bool(parsed.get("emergency", False)),
            confidence=float(parsed.get("confidence", 0.95)),
            raw_text=message,
            normalized_text=message.lower().strip()
        )
