from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import Language
from app.schemas.nlu import NLUIntent, NLUEntities

class ResponseType(str, Enum):
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    ANSWER = "ANSWER"
    SEARCH_REQUIRED = "SEARCH_REQUIRED"
    BOOKING_REQUIRED = "BOOKING_REQUIRED"
    EMERGENCY = "EMERGENCY"
    UNKNOWN = "UNKNOWN"

class ConversationMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Text message content")
    intent: Optional[str] = Field(default=None, description="Extracted intent for this turn if user")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ConversationState(BaseModel):
    session_id: str
    language: Language = Language.HI
    intent: Optional[NLUIntent] = None
    entities: NLUEntities = Field(default_factory=NLUEntities)
    missing_fields: List[str] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    history: List[ConversationMessage] = Field(default_factory=list)
    
    # Phase 6 Emergency Safety State Fields
    emergency_triggered: bool = False
    emergency_level: str = "NORMAL" # NORMAL, POTENTIAL_EMERGENCY, HIGH_CONFIDENCE_EMERGENCY
    emergency_type: Optional[str] = None # BREATHING, CHEST_PAIN, ACCIDENT, BLEEDING, UNCONSCIOUS, GENERAL_EMERGENCY
    emergency_status: str = "IDLE" # IDLE, LOCATION_REQUIRED, LOCATION_CONFIRMED, ASSISTANCE_SIMULATED, RESOLVED
    emergency_location: Optional[Dict[str, Any]] = None # {address, landmark, area, city, state, pincode}
    ambulance_request_id: Optional[str] = None # e.g. AMB-MOCK-00124
    emergency_resolved: bool = False

    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ConversationRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Optional unique session identifier. A new session ID is generated if omitted.")
    user_id: Optional[int] = Field(default=None, description="Optional user ID if authenticated")
    phone_number: Optional[str] = Field(default=None, description="Optional caller phone number")
    message: str = Field(..., description="User input text or speech transcript")
    language_hint: Optional[str] = Field(default=None, description="Language preference hint (HI, MR, EN)")

class ConversationResponse(BaseModel):
    session_id: str
    response_type: ResponseType
    assistant_message: str
    intent: NLUIntent
    entities: NLUEntities
    missing_fields: List[str] = Field(default_factory=list)
    language: Language
    
    # Phase 6 Emergency Response Fields
    emergency: bool = False
    emergency_level: str = "NORMAL"
    emergency_type: Optional[str] = None
    emergency_status: Optional[str] = None
    emergency_location: Optional[Dict[str, Any]] = None
    ambulance_request_id: Optional[str] = None
    
    requires_action: Optional[str] = Field(default=None, description="Suggested action tag (e.g. SEARCH_REQUIRED, BOOKING_REQUIRED)")
    raw_user_message: str = ""
