import os
from typing import Optional
from sqlalchemy.orm import Session
import schemas, crud, intent_engine

# Telephony credentials configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", None)
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", None)
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", None)

EXOTEL_SID = os.getenv("EXOTEL_SID", None)
EXOTEL_TOKEN = os.getenv("EXOTEL_TOKEN", None)

def generate_twiml(say_text: str, gather_action: str = "/telephony/gather") -> str:
    """Generates standard TwiML Voice XML for Telephony Providers (Twilio/Plivo/Exotel)."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech dtmf" timeout="5" numDigits="1" action="{gather_action}">
        <Say voice="Polly.Aditi">{say_text}</Say>
    </Gather>
    <Say>We did not receive any input. Goodbye.</Say>
</Response>"""

def send_sms_confirmation(phone: str, text: str) -> bool:
    """Sends real SMS if provider credentials exist; otherwise logs mock SMS."""
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(body=text, from_=TWILIO_PHONE_NUMBER, to=phone)
            print(f"[REAL SMS SENT via Twilio] To: {phone} | Body: {text}")
            return True
        except Exception as e:
            print(f"[Twilio SMS Error] {e}")

    # Fallback / Mock Mode SMS Logger
    print(f"[MOCK TELEPHONY SMS] To: {phone} | Body: {text}")
    return True

def handle_telephony_call(payload: schemas.TelephonyCallPayload, db: Session) -> schemas.TelephonyResponse:
    call_sid = payload.CallSid or "CALL_MOCK_1001"
    caller_phone = payload.Caller or "+91-9876543210"
    digits = payload.Digits
    speech = payload.SpeechResult
    step = payload.Step or "welcome"
    lang = payload.Language or "hi"

    # STEP 1: INITIAL INCOMING CALL WELCOME
    if step == "welcome" and not digits and not speech:
        welcome_en = "Welcome to JanSethu AI. Press 1 for Hindi, Press 2 for Marathi, Press 3 for English, or speak naturally after the tone."
        welcome_hi = "जनसेतु AI में आपका स्वागत है। हिंदी के लिए 1 दबाएं, मराठी के लिए 2 दबाएं, अंग्रेजी के लिए 3 दबाएं, या अपनी बात बोलें।"
        welcome_mr = "जनसेतु AI मध्ये आपले स्वागत आहे. हिंदीसाठी 1 दाबा, मराठीसाठी 2 दाबा, इंग्रजीसाठी 3 दाबा, किंवा नैसर्गिकपणे बोला."
        
        say_msg = welcome_mr if lang == "mr" else (welcome_hi if lang == "hi" else welcome_en)
        xml = generate_twiml(say_msg)
        
        return schemas.TelephonyResponse(
            call_sid=call_sid,
            speech_text=welcome_en,
            speech_text_hi=welcome_hi,
            speech_text_mr=welcome_mr,
            twiml_xml=xml,
            sms_sent=False,
            next_step="gather_language",
            symptoms="Language Selection",
            duration="Initial Call",
            location="System IVR",
            urgency="Low",
            next_action="Language Selection Prompt"
        )

    # STEP 2: LANGUAGE SELECTION VIA KEYPAD (DTMF)
    if digits:
        if digits == "1":
            lang = "hi"
            msg_en = "You selected Hindi. How can JanSethu AI help you today? Please speak."
            msg_hi = "आपने हिंदी चुना है। जनसेतु AI आपकी क्या सहायता कर सकता है? बोलें।"
            msg_mr = "आपण हिंदी निवडले आहे."
        elif digits == "2":
            lang = "mr"
            msg_en = "You selected Marathi. How can JanSethu AI help you today? Please speak."
            msg_hi = "आपने मराठी चुना है।"
            msg_mr = "आपण मराठी निवडले आहे. जनसेतु AI आपल्याला कशी मदत करू शकते? बोला."
        elif digits == "3":
            lang = "en"
            msg_en = "You selected English. How can JanSethu AI help you today? Please speak."
            msg_hi = "आपने अंग्रेजी चुना है।"
            msg_mr = "आपण इंग्रजी निवडले आहे."
        else:
            msg_en = "Invalid key. Please speak your healthcare request."
            msg_hi = "अमान्य बटन। कृपया अपनी स्वास्थ्य सेवा समस्या बोलें।"
            msg_mr = "अवैध कीपॅड इनपुट. कृपया आपली समस्या बोला."

        chosen_msg = msg_mr if lang == "mr" else (msg_hi if lang == "hi" else msg_en)
        xml = generate_twiml(chosen_msg)
        return schemas.TelephonyResponse(
            call_sid=call_sid,
            speech_text=msg_en,
            speech_text_hi=msg_hi,
            speech_text_mr=msg_mr,
            twiml_xml=xml,
            sms_sent=False,
            next_step="gather_intent",
            symptoms="Language Set to " + lang.upper(),
            duration="In Progress",
            location="Awaiting Query",
            urgency="Low",
            next_action="Awaiting Natural Speech Query"
        )

    # STEP 3: SPEECH RECOGNITION & VOICE INTENT ENGINE PROCESS
    voice_input = speech or "Fever for 3 days in Baramati"
    
    # Delegate to voice intent engine
    intent_res = intent_engine.process_voice_intent(
        schemas.VoiceRequest(transcript=voice_input, lang=lang),
        db
    )

    resp_text = intent_res.response_text
    resp_text_hi = intent_res.response_text_hi or resp_text
    resp_text_mr = intent_res.response_text_mr or resp_text
    sms_body = None
    sms_sent = False

    # Auto-create appointment if intent is appointment_request AND not emergency
    if not intent_res.is_emergency and intent_res.intent == "appointment_request":
        slot_date = intent_res.slots[0].date if (intent_res.slots and len(intent_res.slots) > 0) else "Tomorrow"
        slot_time = intent_res.slots[0].time if (intent_res.slots and len(intent_res.slots) > 0) else "09:00 AM"
        fac_id = intent_res.matched_facility_id or 1
        
        try:
            apt = crud.create_appointment(db, schemas.AppointmentCreate(
                facility_id=fac_id,
                service=intent_res.symptoms or "General OPD",
                date=slot_date,
                time=slot_time,
                patient_name="Keypad Phone Caller",
                phone=caller_phone
            ))
            
            sms_body = f"JanSethu AI Ticket #{apt.id}: Appointment confirmed at {slot_date} {slot_time} in {intent_res.location or 'Baramati'}. Show SMS at OPD desk."
            sms_sent = send_sms_confirmation(caller_phone, sms_body)
            
            resp_text += f" Appointment request submitted! Ticket #{apt.id}. SMS sent to {caller_phone}."
            resp_text_hi += f" अपॉइंटमेंट टिकट #{apt.id} दर्ज! {caller_phone} पर SMS भेजा गया।"
            resp_text_mr += f" अपॉइंटमेंट तिकीट #{apt.id} नोंदवले! {caller_phone} वर SMS पाठवला."
        except Exception as e:
            print("Appointment creation error in telephony:", e)

    say_final = resp_text_mr if lang == "mr" else (resp_text_hi if lang == "hi" else resp_text)
    xml = generate_twiml(say_final)

    return schemas.TelephonyResponse(
        call_sid=call_sid,
        speech_text=resp_text,
        speech_text_hi=resp_text_hi,
        speech_text_mr=resp_text_mr,
        twiml_xml=xml,
        sms_sent=sms_sent,
        sms_body=sms_body,
        next_step="completed" if not intent_res.is_emergency else "emergency_routing",
        symptoms=intent_res.symptoms,
        duration=intent_res.duration,
        location=intent_res.location,
        urgency=intent_res.urgency,
        next_action=intent_res.next_action,
        is_emergency=intent_res.is_emergency
    )
