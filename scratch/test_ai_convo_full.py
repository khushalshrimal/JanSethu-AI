import sys
import os
import asyncio

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

sys.stdout.reconfigure(encoding='utf-8')

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models import facility, doctor, appointment, user, audit, telephony, appointment_audit
from app.models.enums import FacilityType, FacilityStatus, DepartmentStatus, DoctorStatus

from app.schemas.conversation import ConversationRequest
from app.services.conversation_manager import ConversationManager
from app.services.phone_session_service import PhoneSessionService

def seed_sample_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    f1 = facility.Facility(
        name="Jaipur General Hospital",
        facility_type=FacilityType.GOVERNMENT_HOSPITAL,
        address="Civil Lines, Jaipur",
        district="Jaipur",
        state="Rajasthan",
        pincode="302006",
        phone_number="01412345678",
        status=FacilityStatus.ACTIVE,
        is_active=True
    )
    f2 = facility.Facility(
        name="Baramati Civil Hospital",
        facility_type=FacilityType.GOVERNMENT_HOSPITAL,
        address="Main Road, Baramati",
        district="Pune",
        state="Maharashtra",
        pincode="413102",
        phone_number="02112234567",
        status=FacilityStatus.ACTIVE,
        is_active=True
    )
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)
    
    d1 = facility.Department(
        facility_id=f1.id,
        name="General Medicine",
        status=DepartmentStatus.ACTIVE,
        is_active=True
    )
    d2 = facility.Department(
        facility_id=f2.id,
        name="General Medicine",
        status=DepartmentStatus.ACTIVE,
        is_active=True
    )
    db.add_all([d1, d2])
    db.commit()
    db.refresh(d1)
    db.refresh(d2)
    
    doc1 = doctor.Doctor(
        facility_id=f1.id,
        department_id=d1.id,
        name="Dr. Rajesh Sharma",
        qualification="MBBS, MD",
        specialization="General Physician",
        status=DoctorStatus.ACTIVE,
        is_active=True
    )
    doc2 = doctor.Doctor(
        facility_id=f2.id,
        department_id=d2.id,
        name="Dr. Anil Deshmukh",
        qualification="MBBS",
        specialization="General Physician",
        status=DoctorStatus.ACTIVE,
        is_active=True
    )
    db.add_all([doc1, doc2])
    db.commit()
        
    db.close()

async def test_web_ai_conversation():
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("DEMO TEST 1: WEB / MOBILE APP AI CONVERSATION MANAGER (/api/v1/conversation/message)")
    print("="*60 + "\n")
    
    session_id = "demo-user-session-101"
    
    scenarios = [
        ("Greetings & Intro", "Namaste! Main JanSethu AI se baat kar raha hoon."),
        ("Doctor Inquiry", "Mujhe General Physician se milna hai Jaipur mein"),
        ("Date & Time Request", "Kal subah 10 baje doctor available hai kya?"),
        ("Emergency Intervention", "Mujhe seene mein bahut tez dard ho raha hai, saans nahi aa rahi!"),
        ("Emergency Location", "Main Civil Lines Jaipur mein hoon"),
    ]
    
    for label, msg in scenarios:
        print(f"--- Scenario: {label} ---")
        print(f"USER: \"{msg}\"")
        req = ConversationRequest(session_id=session_id, message=msg, language_hint="hi")
        res = await ConversationManager.process_message(req, db=db)
        print(f"AI [{res.response_type.value}]:")
        print(f"  Message: \"{res.assistant_message}\"")
        print(f"  Intent: {res.intent.value}")
        print(f"  Entities Extracted: {res.entities.model_dump(exclude_none=True)}")
        print(f"  Emergency Mode: {res.emergency} (Level: {res.emergency_level}, Status: {res.emergency_status})")
        print()

    db.close()

async def test_phone_call_session():
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("DEMO TEST 2: PHONE TELEPHONY CALL SESSION ENGINE (/api/v1/phone/calls/...)")
    print("="*60 + "\n")
    
    # Start call session
    session = PhoneSessionService.start_session(db, phone_number="9876543210", channel="TELEPHONY_SIMULATOR")
    session_id = session.id
    resp = PhoneSessionService.format_response(db, session)
    
    print(f"Call Session Started #{session_id}")
    print(f"AI Prompt: \"{resp.prompt_text}\"")
    print(f"Voice Playback File: {resp.voice_playback}")
    print()
    
    voice_turns = [
        ("User Greeting", "Namaste mera naam Khushal hai"),
        ("Option Selection", "Mujhe doctor appointment book karni hai"),
        ("Location Mention", "Jaipur me hospital chahiye"),
        ("Emergency Utterance", "Achanak saans phool rahi hai emergency hai"),
    ]
    
    for turn_label, turn_text in voice_turns:
        print(f"--- Phone Voice Turn: {turn_label} ---")
        print(f"USER SPOKE: \"{turn_text}\"")
        session_resp, nlu = await PhoneSessionService.process_voice_input(
            db, session_id=session_id, utterance_or_audio=turn_text, language_hint="hi"
        )
        print(f"AI SPOKE (Prompt): \"{session_resp.prompt_text}\"")
        print(f"Voice Playback Audio: {session_resp.voice_playback}")
        print(f"State Machine State: {session_resp.current_state}")
        print(f"NLU Intent: {nlu.intent.value} (Confidence: {nlu.confidence})")
        print()
        
    db.close()

async def main():
    seed_sample_database()
    await test_web_ai_conversation()
    await test_phone_call_session()

if __name__ == "__main__":
    asyncio.run(main())
