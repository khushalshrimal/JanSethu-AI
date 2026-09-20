from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class CallDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

class CallStatus(str, Enum):
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"

class CallControlAction(str, Enum):
    PLAY_PROMPT = "PLAY_PROMPT"
    COLLECT_DTMF = "COLLECT_DTMF"
    COLLECT_SPEECH = "COLLECT_SPEECH"
    TRANSFER = "TRANSFER"
    END_CALL = "END_CALL"

class IncomingCall(BaseModel):
    provider: str = "development"
    provider_call_id: str
    from_number: str
    to_number: str
    direction: CallDirection = CallDirection.INBOUND
    status: CallStatus = CallStatus.RINGING
    received_at: datetime = Field(default_factory=datetime.utcnow)
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class CallControlResponse(BaseModel):
    action: CallControlAction
    prompt: Optional[str] = None
    language: str = "hi"
    timeout_seconds: int = 8
    dtmf_fallback: bool = True
    transfer_number: Optional[str] = None
    provider_payload: Optional[Dict[str, Any]] = None
