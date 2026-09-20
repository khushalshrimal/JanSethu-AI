from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Dict
from datetime import datetime, date, time
from app.models.enums import AppointmentStatus, BookingChannel, NotificationStatus

class PatientMiniResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class FacilityMiniResponse(BaseModel):
    id: int
    name: str
    district: Optional[str] = None
    village: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DepartmentMiniResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class DoctorMiniResponse(BaseModel):
    id: int
    name: str
    qualification: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class AppointmentBase(BaseModel):
    doctor_id: int
    appointment_date: date
    start_time: time
    end_time: Optional[time] = None
    patient_id: Optional[int] = None
    facility_id: Optional[int] = None
    department_id: Optional[int] = None
    booking_channel: BookingChannel = BookingChannel.PWA
    reason_for_visit: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentCancelRequest(BaseModel):
    reason: str = Field(default="Patient request", description="Reason for cancelling the appointment")

class AppointmentRescheduleRequest(BaseModel):
    new_date: date
    new_start_time: time
    new_end_time: Optional[time] = None
    reason: Optional[str] = Field(default="Patient requested schedule change")

class AppointmentAuditResponse(BaseModel):
    id: int
    appointment_id: int
    actor_id: Optional[int] = None
    event_type: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    notes: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SMSNotificationResponse(BaseModel):
    id: int
    phone_number: str
    message: str
    event_type: str = "BOOKING"
    status: NotificationStatus
    provider: str
    provider_message_id: Optional[str] = None
    failure_reason: Optional[str] = None
    attempt_count: int = 0
    last_attempt_at: Optional[datetime] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CheckInResponse(BaseModel):
    appointment_id: int
    confirmation_code: str
    queue_token: str
    visit_status: str
    checked_in_at: datetime
    message: str
    model_config = ConfigDict(from_attributes=True)

class AppointmentResponse(BaseModel):
    id: int
    confirmation_code: str
    status: AppointmentStatus
    booking_channel: BookingChannel
    patient: PatientMiniResponse
    facility: FacilityMiniResponse
    department: DepartmentMiniResponse
    doctor: DoctorMiniResponse
    appointment_date: date
    start_time: time
    end_time: time
    reason_for_visit: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    queue_token: Optional[str] = None
    visit_status: str = "NOT_CHECKED_IN"
    checked_in_at: Optional[datetime] = None
    consultation_started_at: Optional[datetime] = None
    consultation_completed_at: Optional[datetime] = None
    created_at: datetime
    notification: Optional[SMSNotificationResponse] = None

    model_config = ConfigDict(from_attributes=True)
