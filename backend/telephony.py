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
        welcome_en = "Welcome to JanSethu AI Healthcare Access. Press 1 for Hindi, Press 2 for English, or speak your request after the tone."
        welcome_hi = "जनसेतु AI स्वास्थ्य सेवा पहुँच में आपका स्वागत है। हिंदी के लिए 1 दबाएं, अंग्रेजी के लिए 2 दबाएं, या अपनी बात बोलें।"
        
        say_msg = welcome_hi if lang == "hi" else welcome_en
        xml = generate_twiml(say_msg)
        
        return schemas.TelephonyResponse(
            call_sid=call_sid,
            speech_text=welcome_en,
            speech_text_hi=welcome_hi,
            twiml_xml=xml,
            sms_sent=False,
            next_step="gather_language"
        )

    # STEP 2: LANGUAGE SELECTION VIA KEYPAD (DTMF)
    if digits:
        if digits == "1":
            lang = "hi"
            msg = "आपने हिंदी चुना है। आप किस अस्पताल या डॉक्टर की सुविधा चाहते हैं? बोलें।"
        elif digits == "2":
            lang = "en"
            msg = "You selected English. What healthcare facility or doctor slot do you need? Speak now."
        else:
            msg = "Invalid input. Please speak your healthcare request."
        
        xml = generate_twiml(msg)
        return schemas.TelephonyResponse(
            call_sid=call_sid,
            speech_text=msg,
            speech_text_hi=msg,
            twiml_xml=xml,
            sms_sent=False,
            next_step="gather_intent"
        )

    # STEP 3: SPEECH RECOGNITION & VOICE INTENT ENGINE PROCESS
    voice_input = speech or "I need to see a doctor tomorrow in Sanganer"
    
    # Delegate to existing backend voice intent engine
    intent_res = intent_engine.process_voice_intent(
        schemas.VoiceRequest(transcript=voice_input, lang=lang),
        db
    )

    resp_text = intent_res.response_text_hi if lang == "hi" and intent_res.response_text_hi else intent_res.response_text
    sms_body = None
    sms_sent = False

    # Auto-create appointment if intent is appointment_request and slots are returned
    if intent_res.intent == "appointment_request" and intent_res.slots and len(intent_res.slots) > 0:
        slot = intent_res.slots[0]
        fac_id = intent_res.matched_facility_id or 1
        
        try:
            apt = crud.create_appointment(db, schemas.AppointmentCreate(
                facility_id=fac_id,
                service="General OPD",
                date=slot.date,
                time=slot.time,
                patient_name="Keypad Phone Caller",
                phone=caller_phone
            ))
            
            sms_body = f"JanSethu AI Confirmation: Appointment requested for {slot.date} at {slot.time}. Ticket #{apt.id}. Facility: {apt.facility_id}."
            sms_sent = send_sms_confirmation(caller_phone, sms_body)
            
            resp_text += f" Appointment booked! SMS sent to {caller_phone}. Ticket #{apt.id}."
        except Exception as e:
            print("Appointment creation error in telephony:", e)

    xml = generate_twiml(resp_text)

    return schemas.TelephonyResponse(
        call_sid=call_sid,
        speech_text=resp_text,
        speech_text_hi=resp_text,
        twiml_xml=xml,
        sms_sent=sms_sent,
        sms_body=sms_body,
        next_step="completed"
    )
