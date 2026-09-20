from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import FacilityType, FacilityStatus, DepartmentStatus

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    facility_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmergencyContactResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    contact_type: str
    priority: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class FacilityBase(BaseModel):
    name: str
    facility_type: FacilityType = FacilityType.GOVERNMENT_HOSPITAL
    description: Optional[str] = None
    address: str
    village: Optional[str] = None
    district: str
    state: str = "Maharashtra"
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone_number: str
    status: FacilityStatus = FacilityStatus.ACTIVE
    emergency_available: bool = False

class FacilityCreate(FacilityBase):
    pass

class FacilityResponse(FacilityBase):
    id: int
    is_active: bool
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    emergency_capable: bool = False
    distance_km: Optional[float] = None
    departments: List[DepartmentResponse] = []
    emergency_contacts: List[EmergencyContactResponse] = []

    model_config = ConfigDict(from_attributes=True)
