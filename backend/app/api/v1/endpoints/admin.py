from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole, AppointmentStatus
from app.models.facility import Facility, Department, EmergencyContact
from app.models.doctor import Doctor
from app.api.deps import require_roles
from app.services.admin_service import AdminService
from app.services.facility_service import FacilityService
from app.services.doctor_service import DoctorService
from app.services.appointment_service import AppointmentService
from app.services.provider_service import ProviderService
from app.schemas.admin import (
    AdminDashboardResponse,
    StatusToggleRequest,
    DoctorCreateAdmin,
    EmergencyContactCreate,
    EmergencyContactResponse,
    AuditLogResponse
)
from app.schemas.facility import FacilityCreate, FacilityResponse, DepartmentCreate, DepartmentResponse
from app.schemas.doctor import DoctorResponse
from app.schemas.provider import DoctorAvailabilityCreate, DoctorAvailabilityResponse, DoctorScheduleExceptionCreate, DoctorScheduleExceptionResponse
from app.schemas.appointment import AppointmentResponse

router = APIRouter()

@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Get operational admin dashboard metrics across facilities, doctors, appointments, and system activity.
    """
    return AdminService.get_dashboard_metrics(db)

# --- FACILITY MANAGEMENT ---

@router.get("/facilities", response_model=List[FacilityResponse])
def list_admin_facilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    List all healthcare facilities (including inactive ones) for admin console.
    """
    facilities = db.query(Facility).order_by(Facility.id.desc()).all()
    return [FacilityResponse.model_validate(f) for f in facilities]

@router.post("/facilities", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(
    facility_in: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Create a new healthcare facility (PHC, CHC, Sub-Center, District Hospital).
    """
    return FacilityService.create_facility(db, facility_in)

@router.patch("/facilities/{facility_id}/status", response_model=FacilityResponse)
def toggle_facility_status(
    facility_id: int,
    req: StatusToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Activate or deactivate a healthcare facility. Affects global search and slot engines.
    """
    return AdminService.toggle_facility_status(db, facility_id, req.is_active, current_user)

# --- DEPARTMENT MANAGEMENT ---

@router.post("/facilities/{facility_id}/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    facility_id: int,
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Add a new medical department to a facility.
    """
    return FacilityService.add_department(db, facility_id, dept_in)

@router.patch("/departments/{department_id}/status", response_model=DepartmentResponse)
def toggle_department_status(
    department_id: int,
    req: StatusToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Activate or deactivate a department.
    """
    return AdminService.toggle_department_status(db, department_id, req.is_active, current_user)

# --- DOCTOR MANAGEMENT ---

@router.get("/doctors", response_model=List[DoctorResponse])
def list_admin_doctors(
    facility_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    List all doctors across facilities for admin management.
    """
    q = db.query(Doctor)
    if facility_id:
        q = q.filter(Doctor.facility_id == facility_id)
    docs = q.order_by(Doctor.id.desc()).all()
    return [DoctorResponse.model_validate(d) for d in docs]

@router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(
    req: DoctorCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Onboard a doctor and automatically seed 7-day recurring OPD schedule.
    """
    return AdminService.create_doctor(db, req, current_user)

@router.patch("/doctors/{doctor_id}/status", response_model=DoctorResponse)
def toggle_doctor_status(
    doctor_id: int,
    req: StatusToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Activate or deactivate a doctor's profile. Immediately affects slot generation.
    """
    return AdminService.toggle_doctor_status(db, doctor_id, req.is_active, current_user)

# --- RECURRING SCHEDULE & LEAVE EXCEPTIONS ---

@router.post("/schedules", response_model=DoctorAvailabilityResponse)
def create_or_update_schedule(
    req: DoctorAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Create or update weekly recurring availability slot definitions for a doctor.
    """
    return AdminService.create_or_update_schedule(db, req, current_user)

@router.post("/schedule-exceptions", response_model=DoctorScheduleExceptionResponse, status_code=status.HTTP_201_CREATED)
def create_leave_exception_admin(
    req: DoctorScheduleExceptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Create a leave / schedule exception for any doctor.
    """
    return ProviderService.create_leave_exception(db, req, current_user)

# --- APPOINTMENTS & AUDIT ---

@router.get("/appointments", response_model=List[AppointmentResponse])
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
    Admin global appointment monitor.
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

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Audit log trail monitoring administrative and provider operations.
    """
    return AdminService.get_audit_logs(db, action=action, user_id=user_id, limit=limit)

# --- EMERGENCY CONTACTS ---

@router.get("/emergency-contacts", response_model=List[EmergencyContactResponse])
def list_emergency_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    List system emergency contacts (Ambulance, Helpline, Blood Bank).
    """
    return AdminService.list_emergency_contacts(db)

@router.post("/emergency-contacts", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
def create_emergency_contact(
    req: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Create a new emergency contact record.
    """
    return AdminService.create_emergency_contact(db, req, current_user)

@router.delete("/emergency-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emergency_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Delete an emergency contact.
    """
    contact = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency contact not found.")
    db.delete(contact)
    db.commit()
    return None

# --- DEMO RESET ---

@router.post("/demo-reset", summary="Safe reset of interactive demo data")
def demo_reset(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Safely reset demo appointments, call sessions, conversation logs, and SMS records.
    Requires Admin authorization and non-production APP_ENV.
    """
    return AdminService.execute_demo_reset(db, current_user)

