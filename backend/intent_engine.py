import re
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
import models, crud, schemas

# Known Locations in seed DB
LOCATIONS = {
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
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "दिल्ली": "New Delhi",
    "mehrauli": "Mehrauli",
    "महरौली": "Mehrauli"
}

# Known Services in seed DB
SERVICES = {
    "fever": "Fever Clinic",
    "बुखार": "Fever Clinic",
    "maternity": "Maternity",
    "pregnancy": "Maternity",
    "प्रसूति": "Maternity",
    "बच्चा": "Pediatrics",
    "child": "Pediatrics",
    "vaccine": "Vaccination",
    "vaccination": "Vaccination",
    "टीका": "Vaccination",
    "dental": "Dental OPD",
    "दांत": "Dental OPD",
    "opd": "General OPD",
    "general": "General OPD",
    "सामान्य": "General OPD"
}

def extract_entities(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
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
            
    dt = "Tomorrow"
    if "today" in text_lower or "आज" in text_lower:
        dt = "Today"
    elif "day after" in text_lower or "परसों" in text_lower:
        dt = "Day After"
    elif "tomorrow" in text_lower or "कल" in text_lower:
        dt = "Tomorrow"

    return loc, srv, dt

def process_voice_intent(req: schemas.VoiceRequest, db: Session) -> schemas.VoiceResponse:
    text = req.transcript.strip()
    text_lower = text.lower()

    # Extract location, service, date
    extracted_loc, extracted_srv, extracted_dt = extract_entities(text)
    
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

    # 1. EMERGENCY HELP INTENT
    emergency_keywords = ["emergency", "ambulance", "108", "104", "181", "1098", "urgent", "आपातकाल", "एम्बुलेंस", "गंभीर", "तत्काल"]
    if any(k in text_lower for k in emergency_keywords):
        return schemas.VoiceResponse(
            intent="emergency_help",
            response_text="For medical emergencies, please dial Ambulance 108 immediately. JanSethu AI provides immediate helpline routing.",
            response_text_hi="गंभीर चिकित्सा आपात स्थिति के लिए कृपया तुरंत एम्बुलेंस 108 पर कॉल करें।",
            action="navigate_emergency"
        )

    # 2. FACILITY INFORMATION INTENT (Phone, Address, Contact details)
    info_keywords = ["address", "phone number", "contact phone", "contact", "phone", "where is", "पता", "फोन", "संपर्क", "कहाँ"]
    if any(k in text_lower for k in info_keywords):
        facs = find_matching_facilities()
        if facs:
            f = facs[0]
            return schemas.VoiceResponse(
                intent="facility_information",
                response_text=f"{f.name} is located at {f.address}. Contact Phone: {f.contact_phone}.",
                response_text_hi=f"{f.name_hi or f.name} {f.area}, {f.city} में स्थित है। संपर्क नंबर: {f.contact_phone}।",
                matched_facility_id=f.id,
                facilities=[schemas.FacilityResponse.from_orm(f)],
                action="navigate_facilities"
            )

    # 3. APPOINTMENT REQUEST INTENT
    appointment_keywords = ["appointment", "book", "doctor", "see a doctor", "consult", "अपॉइंटमेंट", "बुक", "डॉक्टर", "दिखाना"]
    if any(k in text_lower for k in appointment_keywords):
        # Missing location check
        if not loc:
            return schemas.VoiceResponse(
                intent="appointment_request",
                response_text="Sure! I can help you request an appointment. Which city or area are you looking for?",
                response_text_hi="जी! मैं आपका अपॉइंटमेंट बुक करने में मदद कर सकता हूँ। आप किस शहर या क्षेत्र (उदा. सांगानेर, मालवीय नगर) में अस्पताल ढूंढ रहे हैं?",
                missing_field="location",
                action="prompt_missing"
            )

        # Missing service check
        if not srv:
            return schemas.VoiceResponse(
                intent="appointment_request",
                response_text=f"Got it for {loc}. What service or doctor department do you need (e.g. General OPD, Fever Clinic, Maternity, Child Vaccine)?",
                response_text_hi=f"ठीक है, {loc} के लिए। आपको किस प्रकार की सेवा (उदा. सामान्य ओपीडी, बुखार क्लिनिक, प्रसूति, बाल टीका) चाहिए?",
                missing_field="service",
                action="prompt_missing"
            )

        facs = find_matching_facilities()
        if facs:
            top_fac = facs[0]
            slots = crud.get_slots(db, facility_id=top_fac.id, only_available=True, date=dt)
            fac_schemas = [schemas.FacilityResponse.from_orm(f) for f in facs]
            slot_schemas = [schemas.SlotResponse.from_orm(s) for s in slots]
            slot_times = ", ".join([s.time for s in slots[:3]]) if slots else "morning slots"

            return schemas.VoiceResponse(
                intent="appointment_request",
                response_text=f"Found {top_fac.name} in {loc}. Available {srv} slots for {dt}: {slot_times}. Select a slot to confirm.",
                response_text_hi=f"{loc} में {top_fac.name_hi or top_fac.name} उपलब्ध है। {dt} के लिए {srv} में समय: {slot_times}।",
                matched_facility_id=top_fac.id,
                facilities=fac_schemas,
                slots=slot_schemas,
                action="navigate_slots"
            )

    # 4. CHECK AVAILABILITY INTENT
    availability_keywords = ["available", "slot", "free", "timing", "open", "समय", "खाली", "कब"]
    if any(k in text_lower for k in availability_keywords):
        facs = find_matching_facilities()
        if facs:
            top_fac = facs[0]
            slots = crud.get_slots(db, facility_id=top_fac.id, only_available=True, date=dt)
            fac_schemas = [schemas.FacilityResponse.from_orm(f) for f in facs]
            slot_schemas = [schemas.SlotResponse.from_orm(s) for s in slots]

            return schemas.VoiceResponse(
                intent="check_availability",
                response_text=f"{top_fac.name} has {len(slots)} open slots for {dt}.",
                response_text_hi=f"{top_fac.name_hi or top_fac.name} में {dt} के लिए {len(slots)} स्लॉट उपलब्ध हैं।",
                matched_facility_id=top_fac.id,
                facilities=fac_schemas,
                slots=slot_schemas,
                action="navigate_slots"
            )

    # 5. FIND FACILITY INTENT
    facility_keywords = ["find", "hospital", "phc", "chc", "centre", "clinic", "अस्पताल", "केंद्र", "क्लीनिक"]
    if any(k in text_lower for k in facility_keywords):
        facs = find_matching_facilities()
        fac_schemas = [schemas.FacilityResponse.from_orm(f) for f in facs]
        
        return schemas.VoiceResponse(
            intent="find_facility",
            response_text=f"I found {len(facs)} healthcare facilities matching your request.",
            response_text_hi=f"आपके अनुरोध से मेल खाते {len(facs)} स्वास्थ्य केंद्र पाए गए।",
            facilities=fac_schemas,
            action="navigate_facilities"
        )

    # 6. FALLBACK INTENT
    return schemas.VoiceResponse(
        intent="fallback",
        response_text="I couldn't quite understand. Try saying 'I need to see a doctor tomorrow' or 'Show hospitals near Sanganer'.",
        response_text_hi="मैं समझ नहीं पाया। कृपया 'मुझे कल डॉक्टर को दिखाना है' या 'सांगानेर में अस्पताल दिखाओ' जैसा बोलें।",
        action="prompt_retry"
    )
