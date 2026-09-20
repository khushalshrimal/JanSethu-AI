from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SlotBase(BaseModel):
    date: str
    time: str
    available: bool = True
    doctor_name: Optional[str] = None
    department: Optional[str] = None

class SlotCreate(SlotBase):
    facility_id: int

class SlotResponse(SlotBase):
    id: int
    facility_id: int

    class Config:
        from_attributes = True

class FacilityBase(BaseModel):
    name: str
    name_hi: Optional[str] = None
    city: str
    area: str
    address: str
    latitude: float
    longitude: float
    services: str
    contact_phone: str
    facility_type: str = "Hospital"

class FacilityResponse(FacilityBase):
    id: int
    simulated_distance: Optional[float] = 4.2
    doctor_available: Optional[bool] = True
    emergency_available: Optional[bool] = True
    smart_score: Optional[float] = 85.0
    next_opd_slot: Optional[str] = "10:30 AM"

    class Config:
        from_attributes = True

class FacilityDetailResponse(FacilityResponse):
    slots: List[SlotResponse] = []

class AppointmentCreate(BaseModel):
    facility_id: int
    service: str
    date: str
    time: str
    patient_name: str
    phone: str
    doctor_name: Optional[str] = "Dr. Sharma"
    token_number: Optional[str] = None

class AppointmentReschedule(BaseModel):
    new_date: str
    new_time: str

class AppointmentResponse(BaseModel):
    id: int
    facility_id: int
    service: str
    date: str
    time: str
    patient_name: str
    phone: str
    status: str
    created_at: datetime
    facility_name: Optional[str] = None
    token_number: Optional[str] = "A-104"
    doctor_name: Optional[str] = "Dr. Sharma"

    class Config:
        from_attributes = True

class EmergencyContact(BaseModel):
    title: str
    title_hi: str
    number: str
    description: str
    description_hi: str

class EmergencyInfo(BaseModel):
    message: str
    message_hi: str
    contacts: List[EmergencyContact]

class VoiceRequest(BaseModel):
    transcript: str
    lang: Optional[str] = "en"
    context_location: Optional[str] = None
    context_service: Optional[str] = None
    context_date: Optional[str] = None

class VoiceResponse(BaseModel):
    intent: str
    response_text: str
    response_text_hi: Optional[str] = None
    response_text_mr: Optional[str] = None
    missing_field: Optional[str] = None
    matched_facility_id: Optional[int] = None
    facilities: Optional[List[FacilityResponse]] = []
    slots: Optional[List[SlotResponse]] = []
    action: Optional[str] = None
    symptoms: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    urgency: Optional[str] = "Low"
    next_action: Optional[str] = "Information Routing"
    is_emergency: bool = False

class TelephonyCallPayload(BaseModel):
    Caller: Optional[str] = "+91-9876543210"
    CallSid: Optional[str] = "CALL_MOCK_1001"
    Digits: Optional[str] = None
    SpeechResult: Optional[str] = None
    Language: Optional[str] = "hi"
    Step: Optional[str] = "welcome"

class TelephonyResponse(BaseModel):
    call_sid: str
    speech_text: str
    speech_text_hi: Optional[str] = None
    speech_text_mr: Optional[str] = None
    twiml_xml: str
    sms_sent: bool = False
    sms_body: Optional[str] = None
    next_step: str
    symptoms: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    urgency: Optional[str] = "Low"
    next_action: Optional[str] = "Information Routing"
    is_emergency: bool = False

class EmergencyCaseResponse(BaseModel):
    id: int
    patient_name: str
    phone: str
    location: str
    detected_issue: str
    urgency: str
    status: str
    timestamp: str

