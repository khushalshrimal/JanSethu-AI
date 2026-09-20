from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database.session import get_db
from app.services.doctor_service import DoctorService
from app.schemas.doctor import (
    DoctorCreate, DoctorResponse, DoctorAvailabilityCreate, DoctorAvailabilityResponse,
    DoctorScheduleExceptionCreate, DoctorScheduleExceptionResponse, DoctorAvailabilityQueryResponse
)
from app.models.enums import UserRole
from app.models.user import User
from app.api.deps import require_roles, get_current_user

router = APIRouter()

@router.get("/", response_model=List[DoctorResponse])
def list_doctors(
    facility_id: int = Query(..., description="Filter doctors by facility ID"),
    department_id: Optional[int] = Query(None, description="Filter doctors by department ID"),
    db: Session = Depends(get_db)
):
    """Public endpoint to list active doctors by facility."""
    return DoctorService.list_doctors(db, facility_id=facility_id, department_id=department_id)

@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Public endpoint to retrieve doctor profile & recurring availability."""
    return DoctorService.get_doctor(db, doctor_id)

@router.get("/{doctor_id}/availability", response_model=DoctorAvailabilityQueryResponse)
def get_doctor_availability_slots(
    doctor_id: int,
    date: date = Query(..., description="Target date for appointment slot discovery (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Public dynamic slot discovery engine.
    Generates actual 30-min availability slots for a target date,
    filtering out booked appointments, schedule exceptions, and past times in Asia/Kolkata timezone.
    """
    return DoctorService.get_doctor_availability_slots(db, doctor_id=doctor_id, target_date=date)

@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(
    doctor_in: DoctorCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """ADMIN ONLY: Registers a new doctor under a facility."""
    return DoctorService.create_doctor(db, doctor_in)

@router.post("/{doctor_id}/availability", response_model=DoctorAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def add_doctor_availability(
    doctor_id: int,
    avail_in: DoctorAvailabilityCreate,
    db: Session = Depends(get_db),
    authorized_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROVIDER))
):
    """ADMIN or PROVIDER ONLY: Configures recurring doctor schedule."""
    return DoctorService.add_availability(db, doctor_id, avail_in)

@router.post("/{doctor_id}/exceptions", response_model=DoctorScheduleExceptionResponse, status_code=status.HTTP_201_CREATED)
def add_schedule_exception(
    doctor_id: int,
    exc_in: DoctorScheduleExceptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROVIDER))
):
    """
    ADMIN or PROVIDER ONLY: Adds a schedule exception (leave / emergency duty / blocked time).
    Prevents slots from being booked during the exception window.
    """
    return DoctorService.add_schedule_exception(db, doctor_id=doctor_id, exc_in=exc_in, current_user=current_user)
