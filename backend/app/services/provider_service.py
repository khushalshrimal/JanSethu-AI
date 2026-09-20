from typing import List, Optional
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.doctor import Doctor, DoctorAvailability, DoctorScheduleException
from app.models.appointment import Appointment
from app.models.audit import AuditLog
from app.models.enums import UserRole, AppointmentStatus, DoctorStatus, ExceptionType
from app.schemas.provider import (
    ProviderDashboardResponse,
    AppointmentStatusUpdateRequest,
    DoctorScheduleExceptionCreate,
    DoctorScheduleExceptionResponse,
    DoctorAvailabilityResponse
)
from app.schemas.appointment import AppointmentResponse
from app.utils.timezone import get_today_ist

class ProviderService:
    @staticmethod
    def get_provider_doctor(db: Session, current_user: User) -> Optional[Doctor]:
        if current_user.doctor_profile:
            return current_user.doctor_profile
        doc = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doc and current_user.role == UserRole.ADMIN:
            # Fallback to first doctor for admin inspecting provider view
            doc = db.query(Doctor).first()
        return doc

    @classmethod
    def get_dashboard_metrics(cls, db: Session, current_user: User) -> ProviderDashboardResponse:
        doc = cls.get_provider_doctor(db, current_user)
        if not doc:
            return ProviderDashboardResponse()

        today = get_today_ist()
        today_apts = db.query(Appointment).filter(
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date == today
        ).all()

        total = len(today_apts)
        waiting = sum(1 for a in today_apts if a.status in [AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        in_prog = sum(1 for a in today_apts if a.status == AppointmentStatus.IN_PROGRESS)
        completed = sum(1 for a in today_apts if a.status == AppointmentStatus.COMPLETED)
        cancelled = sum(1 for a in today_apts if a.status == AppointmentStatus.CANCELLED)
        no_show = sum(1 for a in today_apts if a.status == AppointmentStatus.NO_SHOW)

        return ProviderDashboardResponse(
            doctor_id=doc.id,
            doctor_name=doc.name,
            facility_name=doc.facility.name if doc.facility else None,
            department_name=doc.department.name if doc.department else None,
            today_total=total,
            waiting_count=waiting,
            in_progress_count=in_prog,
            completed_count=completed,
            cancelled_count=cancelled,
            no_show_count=no_show
        )

    @classmethod
    def update_appointment_status(
        cls,
        db: Session,
        appointment_id: int,
        req: AppointmentStatusUpdateRequest,
        current_user: User
    ) -> AppointmentResponse:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

        # Object-level authorization check
        doc = cls.get_provider_doctor(db, current_user)
        if current_user.role == UserRole.PROVIDER:
            if not doc or apt.doctor_id != doc.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Providers can only manage appointments for their assigned doctor profile."
                )

        old_status = apt.status
        apt.status = req.status
        apt.updated_at = datetime.utcnow()

        # Audit Log
        audit = AuditLog(
            user_id=current_user.id,
            action="APPOINTMENT_STATUS_CHANGED",
            entity_type="Appointment",
            entity_id=apt.id,
            metadata_json={
                "old_status": str(old_status),
                "new_status": str(req.status),
                "notes": req.notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(apt)

        from app.services.appointment_service import AppointmentService
        return AppointmentService.format_appointment_response(db, apt)

    @classmethod
    def get_provider_schedule(cls, db: Session, current_user: User) -> List[DoctorAvailabilityResponse]:
        doc = cls.get_provider_doctor(db, current_user)
        if not doc:
            return []
        avails = db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doc.id).all()
        return [DoctorAvailabilityResponse.model_validate(a) for a in avails]

    @classmethod
    def update_provider_doctor_status(
        cls,
        db: Session,
        target_doctor_id: int,
        status_val: DoctorStatus,
        current_user: User
    ) -> DoctorResponse:
        doc = db.query(Doctor).filter(Doctor.id == target_doctor_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found.")

        # IDOR check: Providers can ONLY update their OWN profile
        prov_doc = cls.get_provider_doctor(db, current_user)
        if current_user.role == UserRole.PROVIDER:
            if not prov_doc or prov_doc.id != target_doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Providers can only update operational status for their assigned doctor profile."
                )

        old_status = doc.status.value if hasattr(doc, "status") and hasattr(doc.status, "value") else str(getattr(doc, "status", "ACTIVE"))
        doc.status = status_val
        doc.is_active = (status_val != DoctorStatus.INACTIVE)
        doc.updated_at = datetime.utcnow()

        audit = AuditLog(
            user_id=current_user.id,
            action="DOCTOR_STATUS_CHANGED",
            entity_type="Doctor",
            entity_id=doc.id,
            metadata_json={"old_status": old_status, "new_status": status_val.value, "is_active": doc.is_active}
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)
        from app.schemas.doctor import DoctorResponse
        return DoctorResponse.model_validate(doc)

    @classmethod
    def create_leave_exception(
        cls,
        db: Session,
        req: DoctorScheduleExceptionCreate,
        current_user: User
    ) -> DoctorScheduleExceptionResponse:
        doc = cls.get_provider_doctor(db, current_user)
        doc_id = req.doctor_id or (doc.id if doc else None)
        if not doc_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor ID is required.")

        if current_user.role == UserRole.PROVIDER and doc and doc_id != doc.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Providers can only submit leave for their own profile.")

        exc_type = getattr(req, "exception_type", ExceptionType.LEAVE)
        exc = DoctorScheduleException(
            doctor_id=doc_id,
            date=req.date,
            start_time=req.start_time,
            end_time=req.end_time,
            exception_type=exc_type,
            reason=req.reason,
            is_active=True
        )
        db.add(exc)
        
        # Audit Log
        action_name = "DOCTOR_LEAVE_CREATED" if exc_type == ExceptionType.LEAVE else "SCHEDULE_EXCEPTION_CREATED"
        audit = AuditLog(
            user_id=current_user.id,
            action=action_name,
            entity_type="DoctorScheduleException",
            entity_id=doc_id,
            metadata_json={"date": str(req.date), "reason": req.reason, "exception_type": exc_type.value if hasattr(exc_type, "value") else str(exc_type)}
        )
        db.add(audit)
        db.commit()
        db.refresh(exc)

        return DoctorScheduleExceptionResponse.model_validate(exc)
