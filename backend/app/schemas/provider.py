from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, time, datetime
from app.models.enums import AppointmentStatus

class ProviderDashboardResponse(BaseModel):
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    department_name: Optional[str] = None
    today_total: int = 0
    waiting_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    no_show_count: int = 0

class AppointmentStatusUpdateRequest(BaseModel):
    status: AppointmentStatus
    notes: Optional[str] = None

class DoctorScheduleExceptionCreate(BaseModel):
    doctor_id: Optional[int] = None # Filled from provider context if omitted
    date: date
    start_time: time = time(9, 0)
    end_time: time = time(17, 0)
    reason: Optional[str] = "Doctor Leave / Schedule Exception"

class DoctorScheduleExceptionResponse(BaseModel):
    id: int
    doctor_id: int
    date: date
    start_time: time
    end_time: time
    reason: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DoctorAvailabilityCreate(BaseModel):
    doctor_id: int
    day_of_week: int # 0=Mon, 6=Sun
    start_time: time
    end_time: time
    slot_duration_minutes: int = 30
    is_active: bool = True

class DoctorAvailabilityResponse(BaseModel):
    id: int
    doctor_id: int
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
