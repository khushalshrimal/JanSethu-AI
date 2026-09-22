from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.conversation import ConversationRequest, ConversationResponse
from app.services.conversation_manager import ConversationManager
from app.services.safety_engine import SafetyEngine, EmergencyLevel

router = APIRouter()

class EmergencyHandleRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Active session ID")
    message: str = Field(..., description="User emergency text utterance")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Optional override location object")
    language_hint: Optional[str] = Field(default="HI", description="Language preference hint")

class EmergencyHandleResponse(BaseModel):
    session_id: str
    emergency_detected: bool
    emergency_level: str
    emergency_type: Optional[str] = None
    status: str
    request_id: Optional[str] = None
    location_confirmed: bool
    location: Optional[Dict[str, Any]] = None
    assistant_message: str
    is_simulated: bool = True

@router.post("/handle", response_model=EmergencyHandleResponse)
async def handle_emergency_request(payload: EmergencyHandleRequest):
    """
    Dedicated Emergency Handling API Endpoint for JanSethu AI.
    Processes user emergency signals with highest priority, manages emergency session state,
    obtains/uses location data, and returns a transparent mock emergency assistance status.
    """
    conv_req = ConversationRequest(
        session_id=payload.session_id,
        message=payload.message,
        language_hint=payload.language_hint
    )

    conv_res: ConversationResponse = await ConversationManager.process_message(conv_req)
    state = ConversationManager.get_session(conv_res.session_id)

    loc = state.emergency_location if state else None
    if payload.location and state:
        state.emergency_location = payload.location
        loc = payload.location

    return EmergencyHandleResponse(
        session_id=conv_res.session_id,
        emergency_detected=conv_res.emergency,
        emergency_level=conv_res.emergency_level,
        emergency_type=conv_res.emergency_type,
        status=conv_res.emergency_status or "ASSISTANCE_SIMULATED",
        request_id=conv_res.ambulance_request_id,
        location_confirmed=bool(loc and (loc.get("city") or loc.get("address") or loc.get("location") or loc.get("pincode"))),
        location=loc,
        assistant_message=conv_res.assistant_message,
        is_simulated=True
    )
