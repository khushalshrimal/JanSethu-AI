from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from app.models.enums import FacilityType, UserRole, AppointmentStatus, BookingChannel

class AdminDashboardResponse(BaseModel):
    total_facilities: int = 0
    total_doctors: int = 0
    active_doctors: int = 0
    today_appointments: int = 0
    pending_today: int = 0
    completed_today: int = 0
    cancelled_today: int = 0
    total_providers: int = 0
    emergency_contacts_count: int = 0

class StatusToggleRequest(BaseModel):
    is_active: bool

class DoctorCreateAdmin(BaseModel):
    facility_id: int
    department_id: int
    name: str
    qualification: str
    specialization: str
    phone_number: Optional[str] = None
    consultation_type: str = "OPD_IN_PERSON"
    user_id: Optional[int] = None
    is_active: bool = True

class EmergencyContactCreate(BaseModel):
    facility_id: Optional[int] = None
    name: str
    phone_number: str
    contact_type: str = "AMBULANCE"
    priority: int = 1
    is_active: bool = True

class EmergencyContactResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    name: str
    phone_number: str
    contact_type: str
    priority: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
