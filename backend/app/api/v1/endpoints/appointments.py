from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.appointment_service import AppointmentService
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    CheckInResponse,
    AppointmentCancelRequest,
    AppointmentRescheduleRequest
)
from app.models.enums import AppointmentStatus, UserRole
from app.models.user import User
from app.api.deps import get_current_user, get_current_user_optional, require_roles

router = APIRouter()
provider_router = APIRouter()
admin_router = APIRouter()

# --- APPOINTMENT ENDPOINTS ---

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    apt_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Real Appointment Booking Endpoint.
    Validates patient profile, doctor status, facility/department, IST timezone, and slot availability.
    Enforces DB-level double-booking protection (HTTP 409 Conflict if occupied).
    """
    return AppointmentService.book_appointment(db, apt_in, current_user)

@router.get("/me", response_model=List[AppointmentResponse])
def get_my_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    date_filter: Optional[date] = Query(None, alias="date"),
    upcoming: bool = Query(False, description="Filter only upcoming active appointments"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get personal appointment history for authenticated CUSTOMER or recent patient call appointments.
    """
    if not current_user:
        from app.models.appointment import Appointment
        query = db.query(Appointment).order_by(Appointment.id.desc()).limit(15)
        apts = query.all()
        return [AppointmentService.format_appointment_response(db, a) for a in apts]


    return AppointmentService.get_my_appointments(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        date_filter=date_filter,
        upcoming=upcoming
    )

@router.get("/confirmation/{confirmation_code}", response_model=AppointmentResponse)
def get_appointment_by_confirmation_code(
    confirmation_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve appointment using unique human-friendly confirmation code (JS-2026-XXXXXX).
    Requires proper object-level authorization.
    """
    return AppointmentService.get_by_confirmation_code(db, confirmation_code, current_user)

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Object-Level Authorization Appointment Detail Endpoint.
    """
    return AppointmentService.get_appointment_by_id(db, appointment_id, current_user)

@router.get("/{appointment_id}/visit-status", response_model=AppointmentResponse)
def get_appointment_visit_status(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time visit status & queue token for appointment.
    """
    return AppointmentService.get_appointment_by_id(db, appointment_id, current_user)

@router.post("/{appointment_id}/check-in", response_model=CheckInResponse)
def check_in_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform Patient OPD Check-In.
    Generates persistent queue token, updates visit status to WAITING, and dispatches SMS notification.
    """
    return AppointmentService.check_in_appointment(db, appointment_id, current_user)

@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    cancel_in: AppointmentCancelRequest = AppointmentCancelRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an existing appointment with a reason.
    """
    return AppointmentService.cancel_appointment(db, appointment_id, cancel_in, current_user)

@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: int,
    reschedule_in: AppointmentRescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reschedule an existing appointment to a newly selected date/time slot.
    """
    return AppointmentService.reschedule_appointment(db, appointment_id, reschedule_in, current_user)


# --- PROVIDER ROUTER ENDPOINTS ---

@provider_router.get("/appointments", response_model=List[AppointmentResponse])
def get_provider_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    date_filter: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Queue View.
    """
    return AppointmentService.get_provider_appointments(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        date_filter=date_filter
    )

@provider_router.post("/appointments/{appointment_id}/start-consultation", response_model=AppointmentResponse)
@router.post("/{appointment_id}/start-consultation", response_model=AppointmentResponse)
def start_consultation(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Starts OPD Consultation (WAITING -> IN_CONSULTATION).
    """
    return AppointmentService.start_consultation(db, appointment_id, current_user)

@provider_router.post("/appointments/{appointment_id}/complete-consultation", response_model=AppointmentResponse)
@router.post("/{appointment_id}/complete-consultation", response_model=AppointmentResponse)
def complete_consultation(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Completes OPD Consultation (IN_CONSULTATION -> COMPLETED).
    """
    return AppointmentService.complete_consultation(db, appointment_id, current_user)

@provider_router.post("/appointments/{appointment_id}/no-show", response_model=AppointmentResponse)
@router.post("/{appointment_id}/no-show", response_model=AppointmentResponse)
def mark_no_show(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER, UserRole.ADMIN))
):
    """
    Provider Marks Patient No-Show (WAITING -> NO_SHOW).
    """
    return AppointmentService.mark_no_show(db, appointment_id, current_user)


# --- ADMIN ROUTER ENDPOINT ---

@admin_router.get("/appointments", response_model=List[AppointmentResponse])
def get_admin_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    date_filter: Optional[date] = Query(None, alias="date"),
    facility_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    confirmation_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Admin Appointment Query View.
    Allows administrators to filter and view all system appointments.
    """
    return AppointmentService.get_admin_appointments(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        date_filter=date_filter,
        facility_id=facility_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        confirmation_code=confirmation_code
    )
