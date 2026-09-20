from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import UserRole, Language

class PatientProfileBase(BaseModel):
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = "Maharashtra"
    pincode: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class PatientProfileCreate(PatientProfileBase):
    pass

class PatientProfileResponse(PatientProfileBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    preferred_language: Language = Language.HI

class UserCreate(UserBase):
    password: str
    patient_profile: Optional[PatientProfileCreate] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    patient_profile: Optional[PatientProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
