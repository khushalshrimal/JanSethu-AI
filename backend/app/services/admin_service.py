from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.facility import Facility, Department, EmergencyContact
from app.models.doctor import Doctor, DoctorAvailability, DoctorScheduleException
from app.models.appointment import Appointment
from app.models.audit import AuditLog
from app.models.enums import UserRole, AppointmentStatus, FacilityType, FacilityStatus, DepartmentStatus, DoctorStatus
from app.schemas.admin import (
    AdminDashboardResponse,
    DoctorCreateAdmin,
    EmergencyContactCreate,
    EmergencyContactResponse,
    AuditLogResponse
)
from app.schemas.facility import FacilityCreate, FacilityResponse, DepartmentCreate, DepartmentResponse
from app.schemas.doctor import DoctorResponse
from app.schemas.provider import DoctorAvailabilityCreate, DoctorAvailabilityResponse, DoctorScheduleExceptionResponse
from app.utils.timezone import get_today_ist

class AdminService:
    @classmethod
    def get_dashboard_metrics(cls, db: Session) -> AdminDashboardResponse:
        total_facs = db.query(Facility).count()
        total_docs = db.query(Doctor).count()
        active_docs = db.query(Doctor).filter(Doctor.is_active == True).count()

        today = get_today_ist()
        today_apts = db.query(Appointment).filter(Appointment.appointment_date == today).all()

        today_total = len(today_apts)
        pending_today = sum(1 for a in today_apts if a.status in [AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        completed_today = sum(1 for a in today_apts if a.status == AppointmentStatus.COMPLETED)
        cancelled_today = sum(1 for a in today_apts if a.status == AppointmentStatus.CANCELLED)

        total_providers = db.query(User).filter(User.role == UserRole.PROVIDER).count()
        emg_count = db.query(EmergencyContact).count()

        return AdminDashboardResponse(
            total_facilities=total_facs,
            total_doctors=total_docs,
            active_doctors=active_docs,
            today_appointments=today_total,
            pending_today=pending_today,
            completed_today=completed_today,
            cancelled_today=cancelled_today,
            total_providers=total_providers,
            emergency_contacts_count=emg_count
        )

    # ------------------- FACILITY MANAGEMENT ------------------- #
    @staticmethod
    def toggle_facility_status(db: Session, facility_id: int, is_active: bool, current_user: User, status_val: Optional[FacilityStatus] = None, reason: Optional[str] = None) -> FacilityResponse:
        fac = db.query(Facility).filter(Facility.id == facility_id).first()
        if not fac:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found.")
        
        old_status = fac.status.value if hasattr(fac, "status") and hasattr(fac.status, "value") else str(getattr(fac, "status", "ACTIVE"))
        if status_val is not None:
            fac.status = status_val
            fac.is_active = (status_val == FacilityStatus.ACTIVE)
        else:
            fac.is_active = is_active
            fac.status = FacilityStatus.ACTIVE if is_active else FacilityStatus.INACTIVE
            
        fac.updated_at = datetime.utcnow()
        fac.last_verified_at = datetime.utcnow()

        new_status_str = fac.status.value if hasattr(fac.status, "value") else str(fac.status)

        audit = AuditLog(
            user_id=current_user.id,
            action="FACILITY_STATUS_CHANGED",
            entity_type="Facility",
            entity_id=fac.id,
            metadata_json={"old_status": old_status, "new_status": new_status_str, "is_active": fac.is_active, "reason": reason}
        )
        db.add(audit)
        db.commit()
        db.refresh(fac)
        return FacilityResponse.model_validate(fac)

    # ------------------- DEPARTMENT MANAGEMENT ------------------- #
    @staticmethod
    def toggle_department_status(db: Session, dept_id: int, is_active: bool, current_user: User, status_val: Optional[DepartmentStatus] = None) -> DepartmentResponse:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
        
        old_status = dept.status.value if hasattr(dept, "status") and hasattr(dept.status, "value") else str(getattr(dept, "status", "ACTIVE"))
        if status_val is not None:
            dept.status = status_val
            dept.is_active = (status_val == DepartmentStatus.ACTIVE)
        else:
            dept.is_active = is_active
            dept.status = DepartmentStatus.ACTIVE if is_active else DepartmentStatus.INACTIVE

        dept.updated_at = datetime.utcnow()
        new_status_str = dept.status.value if hasattr(dept.status, "value") else str(dept.status)

        audit = AuditLog(
            user_id=current_user.id,
            action="DEPARTMENT_STATUS_CHANGED",
            entity_type="Department",
            entity_id=dept.id,
            metadata_json={"old_status": old_status, "new_status": new_status_str, "is_active": dept.is_active}
        )
        db.add(audit)
        db.commit()
        db.refresh(dept)
        return DepartmentResponse.model_validate(dept)

    # ------------------- DOCTOR MANAGEMENT ------------------- #
    @staticmethod
    def create_doctor(db: Session, req: DoctorCreateAdmin, current_user: User) -> DoctorResponse:
        doc = Doctor(
            facility_id=req.facility_id,
            department_id=req.department_id,
            name=req.name,
            qualification=req.qualification,
            specialization=req.specialization,
            phone_number=req.phone_number,
            consultation_type=req.consultation_type,
            user_id=req.user_id,
            status=DoctorStatus.ACTIVE,
            is_active=req.is_active
        )
        db.add(doc)
        db.flush()

        # Seed default 7-day recurring availability (Mon-Sun 09:00 AM - 01:00 PM)
        for day in range(0, 7):
            avail = DoctorAvailability(
                doctor_id=doc.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(13, 0),
                slot_duration_minutes=30
            )
            db.add(avail)

        audit = AuditLog(
            user_id=current_user.id,
            action="DOCTOR_CREATED",
            entity_type="Doctor",
            entity_id=doc.id,
            metadata_json={"name": req.name, "specialization": req.specialization}
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)
        return DoctorResponse.model_validate(doc)

    @staticmethod
    def toggle_doctor_status(db: Session, doctor_id: int, is_active: bool, current_user: User, status_val: Optional[DoctorStatus] = None) -> DoctorResponse:
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
        
        old_status = doc.status.value if hasattr(doc, "status") and hasattr(doc.status, "value") else str(getattr(doc, "status", "ACTIVE"))
        if status_val is not None:
            doc.status = status_val
            doc.is_active = (status_val != DoctorStatus.INACTIVE)
        else:
            doc.is_active = is_active
            doc.status = DoctorStatus.ACTIVE if is_active else DoctorStatus.INACTIVE

        doc.updated_at = datetime.utcnow()
        new_status_str = doc.status.value if hasattr(doc.status, "value") else str(doc.status)

        audit = AuditLog(
            user_id=current_user.id,
            action="DOCTOR_STATUS_CHANGED",
            entity_type="Doctor",
            entity_id=doc.id,
            metadata_json={"old_status": old_status, "new_status": new_status_str, "is_active": doc.is_active}
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)
        return DoctorResponse.model_validate(doc)

    # ------------------- RECURRING SCHEDULE MANAGEMENT ------------------- #
    @staticmethod
    def create_or_update_schedule(db: Session, req: DoctorAvailabilityCreate, current_user: User) -> DoctorAvailabilityResponse:
        doc = db.query(Doctor).filter(Doctor.id == req.doctor_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

        existing = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == req.doctor_id,
            DoctorAvailability.day_of_week == req.day_of_week
        ).first()

        if existing:
            existing.start_time = req.start_time
            existing.end_time = req.end_time
            existing.slot_duration_minutes = req.slot_duration_minutes
            existing.is_active = req.is_active
            existing.updated_at = datetime.utcnow()
            target_avail = existing
        else:
            target_avail = DoctorAvailability(
                doctor_id=req.doctor_id,
                day_of_week=req.day_of_week,
                start_time=req.start_time,
                end_time=req.end_time,
                slot_duration_minutes=req.slot_duration_minutes,
                is_active=req.is_active
            )
            db.add(target_avail)

        audit = AuditLog(
            user_id=current_user.id,
            action="SCHEDULE_CHANGED",
            entity_type="DoctorAvailability",
            entity_id=req.doctor_id,
            metadata_json={"day_of_week": req.day_of_week, "start_time": str(req.start_time), "end_time": str(req.end_time)}
        )
        db.add(audit)
        db.commit()
        db.refresh(target_avail)
        return DoctorAvailabilityResponse.model_validate(target_avail)

    # ------------------- EMERGENCY CONTACTS MANAGEMENT ------------------- #
    @staticmethod
    def list_emergency_contacts(db: Session) -> List[EmergencyContactResponse]:
        contacts = db.query(EmergencyContact).order_by(EmergencyContact.priority.asc(), EmergencyContact.id.asc()).all()
        return [EmergencyContactResponse.model_validate(c) for c in contacts]

    @staticmethod
    def create_emergency_contact(db: Session, req: EmergencyContactCreate, current_user: User) -> EmergencyContactResponse:
        contact = EmergencyContact(
            facility_id=req.facility_id,
            name=req.name,
            phone_number=req.phone_number,
            contact_type=req.contact_type,
            priority=req.priority,
            is_active=req.is_active
        )
        db.add(contact)
        
        audit = AuditLog(
            user_id=current_user.id,
            action="EMERGENCY_CONTACT_CREATED",
            entity_type="EmergencyContact",
            entity_id=None,
            metadata_json={"name": req.name, "phone": req.phone_number}
        )
        db.add(audit)
        db.commit()
        db.refresh(contact)
        return EmergencyContactResponse.model_validate(contact)

    # ------------------- AUDIT LOGS QUERY ------------------- #
    @staticmethod
    def get_audit_logs(db: Session, action: Optional[str] = None, user_id: Optional[int] = None, limit: int = 50) -> List[AuditLogResponse]:
        q = db.query(AuditLog)
        if action:
            q = q.filter(AuditLog.action == action)
        if user_id:
            q = q.filter(AuditLog.user_id == user_id)
        
        logs = q.order_by(AuditLog.id.desc()).limit(limit).all()
        result = []
        for l in logs:
            user_email = l.user.email if hasattr(l, "user") and l.user else None
            item = AuditLogResponse.model_validate(l)
            item.user_email = user_email
            result.append(item)
        return result

    # ------------------- SAFE DEMO RESET ------------------- #
    @staticmethod
    def execute_demo_reset(db: Session, current_user: User) -> Dict[str, Any]:
        from app.core.config import settings
        if settings.APP_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Demo reset is disabled in production environments."
            )

        from app.models.telephony import CallSession, ConversationMessage, SMSNotification
        from app.models.appointment_audit import AppointmentAuditLog

        # Delete call session messages & sessions
        db.query(ConversationMessage).delete()
        db.query(CallSession).delete()
        db.query(SMSNotification).delete()
        db.query(AppointmentAuditLog).delete()

        # Delete non-seed appointments (keep SEED appointments)
        non_seed = db.query(Appointment).filter(~Appointment.confirmation_code.like("JS-2026-SEED%")).all()
        deleted_apts_count = len(non_seed)
        for apt in non_seed:
            db.delete(apt)

        audit = AuditLog(
            user_id=current_user.id,
            action="DEMO_RESET_EXECUTED",
            entity_type="System",
            entity_id=None,
            metadata_json={"deleted_appointments": deleted_apts_count, "env": settings.APP_ENV}
        )
        db.add(audit)
        db.commit()

        return {
            "status": "RESET_SUCCESSFUL",
            "message": "Demo appointments, call sessions, conversation logs, and SMS records reset successfully.",
            "deleted_appointments_count": deleted_apts_count,
            "environment": settings.APP_ENV
        }

