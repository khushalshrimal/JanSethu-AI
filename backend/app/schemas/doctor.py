from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
import enum

class SlotStatusEnum(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"
    PAST = "PAST"
    UNAVAILABLE = "UNAVAILABLE"

class SlotResponse(BaseModel):
    start_time: str
    end_time: str
    status: SlotStatusEnum
    reason: Optional[str] = None

class DoctorAvailabilityQueryResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    facility_id: int
    facility_name: str
    department_id: int
    department_name: str
    requested_date: date
    timezone: str = "Asia/Kolkata"
    slots: List[SlotResponse] = []


from app.models.enums import DoctorStatus, ExceptionType

class DoctorScheduleExceptionBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    exception_type: ExceptionType = ExceptionType.LEAVE
    reason: Optional[str] = "Doctor Unavailable"
    is_active: bool = True

class DoctorScheduleExceptionCreate(DoctorScheduleExceptionBase):
    pass

class DoctorScheduleExceptionResponse(DoctorScheduleExceptionBase):
    id: int
    doctor_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorAvailabilityBase(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int = 30
    is_active: bool = True

class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    pass

class DoctorAvailabilityResponse(DoctorAvailabilityBase):
    id: int
    doctor_id: int
    effective_from: datetime
    effective_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorBase(BaseModel):
    facility_id: int
    department_id: int
    name: str
    qualification: str
    specialization: str
    consultation_type: str = "OPD_IN_PERSON"
    phone_number: Optional[str] = None
    user_id: Optional[int] = None
    status: DoctorStatus = DoctorStatus.ACTIVE

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int
    is_active: bool
    created_at: datetime
    availabilities: List[DoctorAvailabilityResponse] = []
    schedule_exceptions: List[DoctorScheduleExceptionResponse] = []

    model_config = ConfigDict(from_attributes=True)
