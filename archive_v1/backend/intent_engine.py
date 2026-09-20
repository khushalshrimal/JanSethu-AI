import re
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
import models, crud, schemas

# Known Locations in seed DB & Demo Locations
LOCATIONS = {
    "baramati": "Baramati",
    "बारामती": "Baramati",
    "sanganer": "Sanganer",
    "सांगानेर": "Sanganer",
    "malviya nagar": "Malviya Nagar",
    "मालवीय नगर": "Malviya Nagar",
    "sitapura": "Sitapura",
    "सीतापुरा": "Sitapura",
    "pratap nagar": "Pratap Nagar",
    "प्रताप नगर": "Pratap Nagar",
    "jaipur": "Jaipur",
    "जयपुर": "Jaipur",
    "pune": "Pune",
    "पुणे": "Pune",
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "दिल्ली": "New Delhi",
    "mehrauli": "Mehrauli",
    "महरौली": "Mehrauli"
}

# Known Services & Symptoms
SERVICES = {
    "fever": "Fever Clinic",
    "bukhar": "Fever Clinic",
    "बुखार": "Fever Clinic",
    "ताप": "Fever Clinic",
    "maternity": "Maternity",
    "pregnancy": "Maternity",
    "प्रसूति": "Maternity",
    "गरोदरपण": "Maternity",
    "बच्चा": "Pediatrics",
    "child": "Pediatrics",
    "बाळ": "Pediatrics",
    "vaccine": "Vaccination",
    "vaccination": "Vaccination",
    "टीका": "Vaccination",
    "लस": "Vaccination",
    "dental": "Dental OPD",
    "दांत": "Dental OPD",
    "दात": "Dental OPD",
    "opd": "General OPD",
    "general": "General OPD",
    "सामान्य": "General OPD"
}

EMERGENCY_TRIGGERS = [
    # Breathing & Respiratory Distress
    "breathing difficulty", "shortness of breath", "saans lene", "saans lene me", "saans lene mein", "dikkat ho rahi", "saans lene mein bahut dikkat", "सांस लेने", "श्वास घेण्यास", "सांस फूलना", "सांस", "श्वास", "परेशानी", "तकलीफ",
    # Chest pain
    "chest pain", "heart attack", "chhati me dard", "छाती में", "छातीत", "दर्द", "दुखणे",
    # Unconsciousness
    "unconscious", "unconsciousness", "fainted", "behoshi", "बेहोशी", "बेशुद्ध", "चक्कर",
    # Bleeding
    "severe bleeding", "major bleeding", "khoon beh", "खून बहना", "रक्तस्राव", "खून",
    # Accident / Injury
    "serious injury", "severe injury", "serious accident", "गंभीर चोट", "अपघात", "दुर्घटना"
]

def extract_entities(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    text_lower = text.lower()
    
    loc = None
    for k, v in LOCATIONS.items():
        if k in text_lower:
            loc = v
            break
            
    srv = None
    for k, v in SERVICES.items():
        if k in text_lower:
            srv = v
            break

    symptom = None
    if "fever" in text_lower or "bukhar" in text_lower or "बुखार" in text_lower or "ताप" in text_lower:
        symptom = "Fever"
    elif "cough" in text_lower or "cold" in text_lower or "खांसी" in text_lower or "खोकला" in text_lower:
        symptom = "Cold & Cough"
    elif "breathing" in text_lower or "सांस" in text_lower or "श्वास" in text_lower:
        symptom = "Breathing Difficulty"
    elif srv:
        symptom = srv

    duration = "Not specified"
    if "3 days" in text_lower or "3 din" in text_lower or "तीन दिन" in text_lower or "३ दिवस" in text_lower:
        duration = "3 days"
    elif "2 days" in text_lower or "2 din" in text_lower or "दो दिन" in text_lower or "२ दिवस" in text_lower:
        duration = "2 days"
    elif "week" in text_lower or "हफ्ते" in text_lower or "आठवडा" in text_lower:
        duration = "1 week"
    elif "today" in text_lower or "आज" in text_lower:
        duration = "Today"

    dt = "Tomorrow"
    if "today" in text_lower or "आज" in text_lower:
        dt = "Today"
    elif "day after" in text_lower or "परसों" in text_lower:
        dt = "Day After"
    elif "tomorrow" in text_lower or "कल" in text_lower or "उद्या" in text_lower:
        dt = "Tomorrow"

    return loc, srv, dt, symptom, duration

def process_voice_intent(req: schemas.VoiceRequest, db: Session) -> schemas.VoiceResponse:
    text = req.transcript.strip()
    text_lower = text.lower()

    # Extract location, service, date, symptom, duration
    extracted_loc, extracted_srv, extracted_dt, symptom, duration = extract_entities(text)
    
    loc = req.context_location or extracted_loc
    srv = req.context_service or extracted_srv
    dt = req.context_date or extracted_dt

    # Helper to find facilities matching loc & srv
    def find_matching_facilities():
        if loc:
            res = crud.get_facilities(db, search=loc)
            if res:
                return res
        if srv:
            res = crud.get_facilities(db, service=srv)
            if res:
                return res
        return crud.get_facilities(db)

    # 1. DETERMINISTIC SAFETY ENGINE (EMERGENCY SCREENING)
    if any(k in text_lower for k in EMERGENCY_TRIGGERS) or any(k in text_lower for k in ["emergency", "ambulance", "108", "104", "आपातकाल", "एम्बुलेंस", "आणीबाणी"]):
        return schemas.VoiceResponse(
            intent="emergency_help",
            response_text="POTENTIAL EMERGENCY DETECTED. Emergency medical assistance is strongly recommended. Please dial 108 immediately.",
            response_text_hi="गंभीर आपात स्थिति पाई गई। आपातकालीन चिकित्सा सहायता की सलाह दी जाती है। कृपया तुरंत 108 पर कॉल करें।",
            response_text_mr="गंभीर आणीबाणी आढळली. तात्काळ वैद्यकीय मदतीची शिफारस केली जाते. कृपया त्वरित १०८ वर कॉल करा.",
            action="navigate_emergency",
            symptoms=symptom or "Severe Respiratory Distress / Critical Symptoms",
            duration=duration,
            location=loc or "Current Location",
            urgency="CRITICAL EMERGENCY",
            next_action="Emergency 108 Dispatch / Urgent Care",
            is_emergency=True
        )

    # 2. FACILITY INFORMATION INTENT
    info_keywords = ["address", "phone number", "contact phone", "contact", "phone", "where is", "पता", "फोन", "संपर्क", "कहाँ", "पत्ता"]
    if any(k in text_lower for k in info_keywords):
        facs = find_matching_facilities()
        if facs:
            f = facs[0]
            return schemas.VoiceResponse(
                intent="facility_information",
                response_text=f"{f.name} is located at {f.address}. Contact Phone: {f.contact_phone}.",
                response_text_hi=f"{f.name_hi or f.name} {f.area}, {f.city} में स्थित है। संपर्क नंबर: {f.contact_phone}।",
                response_text_mr=f"{f.name} {f.area}, {f.city} येथे आहे. संपर्क क्रमांक: {f.contact_phone}.",
                matched_facility_id=f.id,
                facilities=[schemas.FacilityResponse.from_orm(f)],
                action="navigate_facilities",
                symptoms=symptom or "General Inquiry",
                duration=duration,
                location=loc or f.city,
                urgency="Low",
                next_action="Facility Contact Details Provided"
            )

    # 3. APPOINTMENT REQUEST INTENT
    appointment_keywords = ["appointment", "book", "doctor", "see a doctor", "consult", "fever", "bukhar", "ताप", "बुखार", "अपॉइंटमेंट", "बुक", "डॉक्टर", "दिखाना", "भेटायचे"]
    if any(k in text_lower for k in appointment_keywords):
        # If location missing
        if not loc:
            return schemas.VoiceResponse(
                intent="appointment_request",
                response_text="I can help book a doctor slot. Please tell me your city, area, or PIN code (e.g. Baramati, Sanganer).",
                response_text_hi="जी! मैं आपका अपॉइंटमेंट बुक कर सकता हूँ। कृपया अपना गाँव, शहर या क्षेत्र (उदा. बारामती, सांगानेर) बताएं।",
                response_text_mr="हो! मी तुमची अपॉइंटमेंट बुक करू शकतो. कृपया तुमचे शहर किंवा परिसर सांगा (उदा. बारामती, सांगानेर).",
                missing_field="location",
                action="prompt_missing",
                symptoms=symptom or "General Consultation",
                duration=duration,
                location="Awaiting Input",
                urgency="Medium",
                next_action="Prompting Location Entity"
            )

        facs = find_matching_facilities()
        if facs:
            top_fac = facs[0]
            slots = crud.get_slots(db, facility_id=top_fac.id, only_available=True, date=dt)
            fac_schemas = [schemas.FacilityResponse.from_orm(f) for f in facs]
            slot_schemas = [schemas.SlotResponse.from_orm(s) for s in slots]
            slot_times = ", ".join([s.time for s in slots[:3]]) if slots else "09:00 AM, 10:30 AM"

            return schemas.VoiceResponse(
                intent="appointment_request",
                response_text=f"Found {top_fac.name} in {loc}. Slots available for {dt}: {slot_times}. Booking appointment slot...",
                response_text_hi=f"{loc} में {top_fac.name_hi or top_fac.name} उपलब्ध है। {dt} के लिए उपलब्ध समय: {slot_times}। अपॉइंटमेंट अनुरोध दर्ज किया जा रहा है...",
                response_text_mr=f"{loc} मध्ये {top_fac.name} उपलब्ध आहे. {dt} साठी उपलब्ध वेळा: {slot_times}. अपॉइंटमेंट नोंदवली जात आहे...",
                matched_facility_id=top_fac.id,
                facilities=fac_schemas,
                slots=slot_schemas,
                action="navigate_slots",
                symptoms=symptom or "Fever / General OPD",
                duration=duration,
                location=loc,
                urgency="Medium",
                next_action="Slot Reservation & SMS Dispatch"
            )

    # 4. FIND FACILITY INTENT
    facility_keywords = ["find", "hospital", "phc", "chc", "centre", "clinic", "अस्पताल", "केंद्र", "क्लीनिक", "रुग्णालय"]
    if any(k in text_lower for k in facility_keywords):
        facs = find_matching_facilities()
        fac_schemas = [schemas.FacilityResponse.from_orm(f) for f in facs]
        
        return schemas.VoiceResponse(
            intent="find_facility",
            response_text=f"I found {len(facs)} verified healthcare facilities in {loc or 'your area'}.",
            response_text_hi=f"{loc or 'आपके क्षेत्र'} में {len(facs)} सत्यापित स्वास्थ्य केंद्र पाए गए।",
            response_text_mr=f"{loc or 'तुमच्या भागात'} {len(facs)} नोंदणीकृत रुग्णालये सापडली.",
            facilities=fac_schemas,
            action="navigate_facilities",
            symptoms=symptom or "Facility Search",
            duration=duration,
            location=loc or "Detected Area",
            urgency="Low",
            next_action="Display Verified Facilities"
        )

    # 5. FALLBACK INTENT
    return schemas.VoiceResponse(
        intent="fallback",
        response_text="I could not quite understand. Try saying 'I have fever for 3 days in Baramati' or 'Breathing difficulty'.",
        response_text_hi="मैं समझ नहीं पाया। कृपया 'मुझे तीन दिन से बारामती में बुखार है' या 'सांस लेने में तकलीफ' जैसा बोलें।",
        response_text_mr="मला समजले नाही. कृपया 'मला तीन दिवसांपासून बारामतीमध्ये ताप आहे' किंवा 'श्वास घेण्यास त्रास' असे बोला.",
        action="prompt_retry",
        symptoms="Unclear Input",
        duration="Unclear",
        location=loc or "Not specified",
        urgency="Low",
        next_action="Voice Fallback Prompt"
    )
