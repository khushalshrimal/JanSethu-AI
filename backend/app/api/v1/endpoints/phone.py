from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.phone import PhoneStartCallRequest, PhoneInputRequest, PhoneSessionResponse
from app.services.phone_session_service import PhoneSessionService

router = APIRouter()

@router.post("/calls/start", response_model=PhoneSessionResponse, status_code=status.HTTP_201_CREATED)
def start_call_session(req: PhoneStartCallRequest, db: Session = Depends(get_db)):
    """
    Initiates a new telephony call session.
    Persists initial state (GREETING) into the database.
    """
    session = PhoneSessionService.start_session(
        db,
        phone_number=req.caller_phone,
        channel=req.channel or "TELEPHONY_SIMULATOR",
        resume_existing=req.resume or False
    )
    return PhoneSessionService.format_response(db, session)

@router.post("/calls/{session_id}/input", response_model=PhoneSessionResponse)
def process_call_input(session_id: int, req: PhoneInputRequest, db: Session = Depends(get_db)):
    """
    Processes DTMF keypad or speech input for an active call session.
    Advances the state machine, persists selections to DB, and returns next prompt.
    """
    return PhoneSessionService.process_dtmf_input(db, session_id=session_id, key=req.value)

@router.get("/calls/{session_id}", response_model=PhoneSessionResponse)
def get_call_session(session_id: int, db: Session = Depends(get_db)):
    """Retrieves current persisted call session state."""
    session = PhoneSessionService.get_session(db, session_id)
    return PhoneSessionService.format_response(db, session)

@router.post("/calls/{session_id}/end", response_model=PhoneSessionResponse)
def end_call_session(session_id: int, db: Session = Depends(get_db)):
    """Terminates an active call session."""
    session = PhoneSessionService.end_session(db, session_id)
    return PhoneSessionService.format_response(db, session)

# ------------------- VOICE INTERACTION ENDPOINTS ------------------- #

from app.schemas.phone import (
    VoiceTranscribeRequest,
    VoiceUnderstandRequest,
    VoiceInputSessionRequest,
    VoiceInputSessionResponse,
    TTSRequest,
    TTSResponse
)
from app.services.voice import (
    LocalSpeechInputProvider,
    VoiceUnderstandingService,
    LocalTTSProvider
)

@router.post("/voice/transcribe")
async def voice_transcribe(req: VoiceTranscribeRequest):
    """STT abstraction endpoint for speech transcription."""
    stt = LocalSpeechInputProvider()
    return await stt.transcribe(req.text, language_hint=req.language_hint)

@router.post("/voice/understand")
async def voice_understand(req: VoiceUnderstandRequest):
    """NLU abstraction endpoint for language detection, intent parsing, and entity extraction."""
    service = VoiceUnderstandingService()
    res = await service.process_utterance(req.text, language_hint=req.language_hint)
    return res

@router.post("/voice/input", response_model=VoiceInputSessionResponse)
async def voice_input_session(req: VoiceInputSessionRequest, db: Session = Depends(get_db)):
    """
    Submits voice speech/utterance into active CallSession state machine.
    Advances state machine and returns prompt + NLU metadata.
    """
    session_resp, nlu = await PhoneSessionService.process_voice_input(
        db,
        session_id=req.call_session_id,
        utterance_or_audio=req.text,
        language_hint=req.language_hint
    )
    return VoiceInputSessionResponse(
        session_id=session_resp.session_id,
        caller_phone=session_resp.caller_phone,
        current_state=session_resp.current_state,
        language=session_resp.language,
        status=session_resp.status,
        prompt_text=session_resp.prompt_text,
        voice_playback=session_resp.voice_playback,
        options=session_resp.options,
        intent=nlu.intent.value,
        confidence=nlu.confidence,
        detected_language=nlu.language.value,
        raw_text=nlu.raw_text,
        normalized_text=nlu.normalized_text,
        entities=nlu.entities
    )

@router.post("/voice/tts", response_model=TTSResponse)
async def voice_tts(req: TTSRequest):
    """TTS abstraction endpoint for synthesizing text to spoken audio."""
    tts = LocalTTSProvider()
    res = await tts.synthesize(req.text, language=req.language)
    return TTSResponse(**res)

