from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SlotBase(BaseModel):
    date: str
    time: str
    available: bool = True
    doctor_name: Optional[str] = None
    department: Optional[str] = None

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
