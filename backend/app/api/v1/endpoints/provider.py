from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole, AppointmentStatus
from app.api.deps import require_roles
from app.services.provider_service import ProviderService
from app.services.appointment_service import AppointmentService
from app.schemas.provider import (
    ProviderDashboardResponse,
    AppointmentStatusUpdateRequest,
    DoctorScheduleExceptionCreate,
    DoctorScheduleExceptionResponse,
    DoctorAvailabilityResponse
)
from app.schemas.appointment import AppointmentResponse

router = APIRouter()

@router.get("/dashboard", response_model=ProviderDashboardResponse)
def get_provider_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Get provider dashboard OPD metrics for today.
    """
    return ProviderService.get_dashboard_metrics(db, current_user)

@router.get("/appointments", response_model=List[AppointmentResponse])
def get_provider_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    date_filter: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider OPD Queue View.
    Returns appointments for the authenticated provider's assigned doctor/facility.
    """
    return AppointmentService.get_provider_appointments(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        date_filter=date_filter
    )

@router.put("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    req: AppointmentStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Update OPD appointment status (e.g. BOOKED -> IN_PROGRESS -> COMPLETED / NO_SHOW / CANCELLED).
    Enforces object-level authorization & audit logging.
    """
    return ProviderService.update_appointment_status(db, appointment_id, req, current_user)

@router.post("/appointments/{appointment_id}/start-consultation", response_model=AppointmentResponse)
def start_consultation(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Starts OPD Consultation (WAITING -> IN_CONSULTATION).
    """
    return AppointmentService.start_consultation(db, appointment_id, current_user)

@router.post("/appointments/{appointment_id}/complete-consultation", response_model=AppointmentResponse)
def complete_consultation(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Completes OPD Consultation (IN_CONSULTATION -> COMPLETED).
    """
    return AppointmentService.complete_consultation(db, appointment_id, current_user)

@router.post("/appointments/{appointment_id}/no-show", response_model=AppointmentResponse)
def mark_no_show(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Marks Patient No-Show (WAITING -> NO_SHOW).
    """
    return AppointmentService.mark_no_show(db, appointment_id, current_user)

@router.get("/schedule", response_model=List[DoctorAvailabilityResponse])
def get_provider_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Get assigned doctor's weekly recurring availability schedule.
    """
    return ProviderService.get_provider_schedule(db, current_user)

@router.post("/schedule-exceptions", response_model=DoctorScheduleExceptionResponse, status_code=status.HTTP_201_CREATED)
def create_leave_exception(
    req: DoctorScheduleExceptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Submit a doctor leave / schedule exception for a specific date.
    Immediately blocks slot generation across PWA, Phone DTMF, and Voice IVR.
    """
    return ProviderService.create_leave_exception(db, req, current_user)
