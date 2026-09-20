from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from enum import Enum
from app.models.enums import Language, CallSessionStatus

class PhoneInputType(str, Enum):
    DTMF = "DTMF"
    SPEECH = "SPEECH"

class PhoneStartCallRequest(BaseModel):
    caller_phone: str
    channel: Optional[str] = "TELEPHONY_SIMULATOR"
    resume: Optional[bool] = False

class PhoneInputRequest(BaseModel):
    input_type: PhoneInputType = PhoneInputType.DTMF
    value: str

class PhoneMenuOption(BaseModel):
    key: str
    label: str

class PhoneSessionResponse(BaseModel):
    session_id: int
    caller_phone: str
    current_state: str
    language: Language
    status: CallSessionStatus
    prompt_text: str
    voice_playback: str
    options: List[PhoneMenuOption] = []
    selected_facility_id: Optional[int] = None
    selected_department_id: Optional[int] = None
    selected_doctor_id: Optional[int] = None
    selected_date: Optional[str] = None
    selected_start_time: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VoiceTranscribeRequest(BaseModel):
    text: str
    language_hint: Optional[str] = "HI"


class VoiceUnderstandRequest(BaseModel):
    text: str
    language_hint: Optional[str] = None


class VoiceInputSessionRequest(BaseModel):
    call_session_id: int
    text: str
    language_hint: Optional[str] = None


class VoiceInputSessionResponse(BaseModel):
    session_id: int
    caller_phone: str
    current_state: str
    language: Language
    status: CallSessionStatus
    prompt_text: str
    voice_playback: str
    options: List[PhoneMenuOption] = []
    intent: str
    confidence: float
    detected_language: str
    raw_text: str
    normalized_text: str
    entities: dict = {}

    model_config = ConfigDict(from_attributes=True)


class TTSRequest(BaseModel):
    text: str
    language: str = "hi"


class TTSResponse(BaseModel):
    text: str
    language: str
    audio_available: bool = False
    audio_url: Optional[str] = None

