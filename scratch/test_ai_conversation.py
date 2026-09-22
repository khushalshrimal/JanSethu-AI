import sys
import os
import asyncio

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

# Force UTF-8 stdout encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

from app.database.session import SessionLocal, engine
from app.database.base import Base

# Import all models to register with Base.metadata
from app.models import facility, doctor, appointment, user, audit, telephony, appointment_audit

from app.schemas.conversation import ConversationRequest
from app.services.conversation_manager import ConversationManager
from app.services.phone_session_service import PhoneSessionService

async def test_conversation():
    # Create DB tables if not existing
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    session_id = "test-ai-convo-1"
    
    turns = [
        "Namaste, mujhe doctor se milna hai.",
        "Kolkata me general physician chahiye kal ke liye",
        "Mujhe saans lene me bahut dikkat ho rahi hai emergency hai!",
        "Main Park Street Kolkata me hu, jaldi help bhejo",
    ]
    
    print("\n==========================================")
    print("TESTING CONVERSATION MANAGER (MULTI-TURN AI)")
    print("==========================================\n")
    
    for turn in turns:
        print(f"USER: {turn}")
        req = ConversationRequest(session_id=session_id, message=turn, language_hint="hi")
        res = await ConversationManager.process_message(req, db=db)
        print(f"JANSETHU AI [{res.response_type.value}]:")
        print(f"   \"{res.assistant_message}\"")
        print(f"   [Intent: {res.intent.value} | City: {res.entities.city} | Emergency: {res.emergency}]")
        print("------------------------------------------\n")
        
    db.close()

async def test_phone_session():
    db = SessionLocal()
    print("\n==========================================")
    print("TESTING PHONE SESSION SERVICE (VOICE/TELEPHONY)")
    print("==========================================\n")
    
    session = PhoneSessionService.start_session(db, phone_number="9876543210", channel="TELEPHONY_SIMULATOR")
    session_id = session.id
    print(f"CALL STARTED (Session #{session_id})")
    print(f"AI SPOKE: \"{session.prompt_text}\"")
    print("------------------------------------------\n")
    
    voice_inputs = [
        "Namaste, mujhe doctor ki appointment chahiye",
        "Kolkata mein General Physician mil jayega?",
        "Mujhe saans lene mein dikkat ho rahi hai, emergency hai!"
    ]
    
    for inp in voice_inputs:
        print(f"USER SPOKE: \"{inp}\"")
        session_resp, nlu = await PhoneSessionService.process_voice_input(
            db, session_id=session_id, utterance_or_audio=inp, language_hint="hi"
        )
        print(f"AI SPOKE: \"{session_resp.prompt_text}\"")
        print(f"   [Audio file: {session_resp.voice_playback} | Detected Intent: {nlu.intent.value}]")
        print("------------------------------------------\n")
        
    db.close()

async def main():
    await test_conversation()
    await test_phone_session()

if __name__ == "__main__":
    asyncio.run(main())
