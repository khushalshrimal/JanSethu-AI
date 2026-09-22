from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.models.enums import Language

class NLUIntent(str, Enum):
    # Core & Greeting Intents
    GENERAL_GREETING = "GENERAL_GREETING"
    GENERAL_HELLO = "GENERAL_GREETING" # Compatibility alias
    GENERAL_HELP = "GENERAL_HELP"   # Compatibility alias
    PROVIDE_NAME = "PROVIDE_NAME"
    PROVIDE_LOCATION = "PROVIDE_LOCATION"
    LANGUAGE_CHANGE = "LANGUAGE_CHANGE"
    THANK_YOU = "THANK_YOU"
    GOODBYE = "GOODBYE"
    
    # Clinical & Healthcare Queries
    MEDICAL_HELP = "MEDICAL_HELP"
    SYMPTOM_REPORT = "SYMPTOM_REPORT"
    SYMPTOM_INFORMATION = "SYMPTOM_INFORMATION" # Compatibility alias
    FIND_FACILITY = "FIND_FACILITY"
    FACILITY_SEARCH = "FIND_FACILITY"         # Compatibility alias
    CHECK_FACILITY = "FIND_FACILITY"
    FACILITY_INFORMATION = "FACILITY_INFORMATION"
    FACILITY_DETAILS = "FACILITY_INFORMATION"       # Compatibility alias
    FIND_DOCTOR = "FIND_DOCTOR"
    DOCTOR_SEARCH = "FIND_DOCTOR"             # Compatibility alias
    FIND_SPECIALIST = "FIND_SPECIALIST"
    CHECK_DOCTOR = "FIND_DOCTOR"
    DOCTOR_INFORMATION = "DOCTOR_INFORMATION"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    DOCTOR_AVAILABILITY = "CHECK_AVAILABILITY" # Compatibility alias
    OPD_SCHEDULE = "CHECK_AVAILABILITY"
    SLOT_SEARCH = "CHECK_AVAILABILITY"         # Compatibility alias
    
    # Appointment Workflow
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    CONFIRM_APPOINTMENT = "CONFIRM_APPOINTMENT"
    APPOINTMENT_CONFIRMATION = "CONFIRM_APPOINTMENT"
    RESCHEDULE_APPOINTMENT = "RESCHEDULE_APPOINTMENT"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    MY_APPOINTMENTS = "MY_APPOINTMENTS"
    REFERRAL_ID = "REFERRAL_ID"
    REFERRAL_LOOKUP = "REFERRAL_LOOKUP" # Compatibility alias
    DISTANCE_QUERY = "DISTANCE_QUERY"
    
    # Emergency & Ambulance Pathways
    EMERGENCY = "EMERGENCY"
    AMBULANCE_REQUEST = "AMBULANCE_REQUEST"
    EMERGENCY_FACILITY_SEARCH = "EMERGENCY_FACILITY_SEARCH"
    
    # Catch-all
    UNKNOWN = "UNKNOWN"

class NLUEntities(BaseModel):
    # Patient & Demographic Entities
    patient_name: Optional[str] = None
    patient_relation: Optional[str] = None
    
    # Symptom & Clinical Attributes
    symptoms: List[str] = Field(default_factory=list)
    duration: Optional[str] = None
    severity: Optional[str] = None
    specialty: Optional[str] = None
    speciality: Optional[str] = None # Compatibility alias
    department: Optional[str] = None
    service: Optional[str] = None
    
    # Facility & Doctor Attributes
    facility_type: Optional[str] = None
    facility_name: Optional[str] = None
    facility: Optional[str] = None   # Compatibility alias
    doctor_name: Optional[str] = None
    doctor: Optional[str] = None     # Compatibility alias
    
    # Spatial & Location Attributes
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    landmark: Optional[str] = None
    
    # Temporal & Booking Attributes
    date: Optional[str] = None
    time: Optional[str] = None
    time_period: Optional[str] = None
    appointment_id: Optional[str] = None
    referral_id: Optional[str] = None
    language: Optional[str] = None
    
    # Flags & Action Intent Signals
    appointment_requested: bool = False
    ambulance_requested: bool = False
    is_correction: bool = False
    corrected_field: Optional[str] = None

class NLUAnalysisRequest(BaseModel):
    message: str = Field(..., description="User text or transcribed speech input")
    conversation_context: Optional[Dict[str, Any]] = Field(default=None, description="Active session context if available")
    language_hint: Optional[str] = Field(default=None, description="Optional language preference hint (HI, MR, EN)")

class NLUAnalysisResponse(BaseModel):
    intent: NLUIntent
    entities: NLUEntities
    language: Language
    emergency: bool = False
    emergency_signals: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    requires_database_lookup: bool = False
    requires_confirmation: bool = False
    confidence: float = 1.0
    raw_text: str = ""
    normalized_text: str = ""
    error: Optional[str] = None
