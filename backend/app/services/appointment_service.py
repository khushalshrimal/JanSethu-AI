from datetime import datetime, date, time, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.appointment import Appointment
from app.models.user import User, PatientProfile
from app.models.facility import Department
from app.models.enums import UserRole, AppointmentStatus, BookingChannel, DoctorStatus, FacilityStatus, DepartmentStatus, Language
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.facility_repository import FacilityRepository
from app.services.availability_service import check_slot_availability
from app.services.notification_service import NotificationService
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentCancelRequest,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    CheckInResponse,
    PatientMiniResponse,
    FacilityMiniResponse,
    DepartmentMiniResponse,
    DoctorMiniResponse,
    SMSNotificationResponse
)
from app.utils.timezone import get_ist_now

# VALID STATUS TRANSITION MAP
ALLOWED_TRANSITIONS = {
    AppointmentStatus.BOOKED: [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED],
    AppointmentStatus.PENDING: [AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED],
    AppointmentStatus.CONFIRMED: [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW],
    AppointmentStatus.CANCELLED: [], # Terminal
    AppointmentStatus.COMPLETED: [], # Terminal
    AppointmentStatus.NO_SHOW: []     # Terminal
}

class AppointmentService:
    @staticmethod
    def validate_status_transition(current_status: AppointmentStatus, target_status: AppointmentStatus):
        if target_status == current_status:
            return
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_STATUS_TRANSITION",
                    "message": f"Cannot transition appointment status from '{current_status.value}' to '{target_status.value}'."
                }
            )

    @classmethod
    def format_appointment_response(cls, db: Session, apt: Appointment) -> AppointmentResponse:
        patient_obj = PatientMiniResponse(
            id=apt.patient.id,
            name=apt.patient.user.name if (apt.patient and apt.patient.user) else "Patient",
            phone=apt.patient.user.phone_number if (apt.patient and apt.patient.user) else None
        )
        facility_obj = FacilityMiniResponse(
            id=apt.facility.id,
            name=apt.facility.name,
            district=apt.facility.district,
            village=apt.facility.village
        )
        dept_obj = DepartmentMiniResponse(
            id=apt.department.id,
            name=apt.department.name
        )
        doc_obj = DoctorMiniResponse(
            id=apt.doctor.id,
            name=apt.doctor.name,
            qualification=apt.doctor.qualification
        )

        latest_sms = None
        if apt.sms_notifications:
            sms_rec = sorted(apt.sms_notifications, key=lambda s: s.created_at, reverse=True)[0]
            latest_sms = SMSNotificationResponse.model_validate(sms_rec)

        return AppointmentResponse(
            id=apt.id,
            confirmation_code=apt.confirmation_code,
            status=apt.status,
            booking_channel=apt.booking_channel,
            patient=patient_obj,
            facility=facility_obj,
            department=dept_obj,
            doctor=doc_obj,
            appointment_date=apt.appointment_date,
            start_time=apt.start_time,
            end_time=apt.end_time,
            reason_for_visit=apt.reason_for_visit,
            cancellation_reason=apt.cancellation_reason,
            cancelled_at=apt.cancelled_at,
            queue_token=apt.queue_token,
            visit_status=getattr(apt, "visit_status", "NOT_CHECKED_IN") or "NOT_CHECKED_IN",
            checked_in_at=apt.checked_in_at,
            consultation_started_at=apt.consultation_started_at,
            consultation_completed_at=apt.consultation_completed_at,
            created_at=apt.created_at,
            notification=latest_sms
        )

    @classmethod
    def book_appointment(
        cls, db: Session, apt_in: AppointmentCreate, current_user: User
    ) -> AppointmentResponse:
        # 1. Determine & Validate Patient Identity
        if current_user.role == UserRole.CUSTOMER:
            if not current_user.patient_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "PATIENT_PROFILE_MISSING", "message": "Customer user profile missing."}
                )
            if apt_in.patient_id and apt_in.patient_id != current_user.patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_PATIENT_ACCESS", "message": "Customers can only book for their own profile."}
                )
            target_patient_id = current_user.patient_profile.id
        else:
            if not apt_in.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "PATIENT_ID_REQUIRED", "message": "patient_id is required for provider/admin bookings."}
                )
            patient_profile = db.query(PatientProfile).filter(PatientProfile.id == apt_in.patient_id).first()
            if not patient_profile:
                raise HTTPException(
                    status_code=status.HTTP_44_NOT_FOUND if hasattr(status, 'HTTP_44_NOT_FOUND') else status.HTTP_404_NOT_FOUND,
                    detail={"code": "PATIENT_NOT_FOUND", "message": f"Patient profile with ID {apt_in.patient_id} not found."}
                )
            target_patient_id = apt_in.patient_id

        # 2. Validate Doctor
        doc = DoctorRepository.get_by_id(db, apt_in.doctor_id)
        if not doc or not doc.is_active or (hasattr(doc, "status") and doc.status == DoctorStatus.INACTIVE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DOCTOR_INACTIVE", "message": "Doctor not found or currently inactive."}
            )
        if hasattr(doc, "status") and doc.status == DoctorStatus.ON_LEAVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DOCTOR_ON_LEAVE", "message": f"Doctor '{doc.name}' is currently on leave."}
            )

        # 3. Validate Facility & Department
        fac_id = apt_in.facility_id or doc.facility_id
        fac = FacilityRepository.get_by_id(db, fac_id)
        if not fac or not fac.is_active or (hasattr(fac, "status") and fac.status == FacilityStatus.INACTIVE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "FACILITY_INACTIVE", "message": "Facility not found or currently inactive."}
            )
        if hasattr(fac, "status") and fac.status == FacilityStatus.TEMPORARILY_UNAVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "FACILITY_TEMPORARILY_UNAVAILABLE", "message": f"Facility '{fac.name}' is temporarily unavailable for OPD appointments."}
            )

        dept_id = apt_in.department_id or doc.department_id
        if not dept_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DEPARTMENT_MISSING", "message": "Doctor department not configured."}
            )
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept or not dept.is_active or (hasattr(dept, "status") and dept.status == DepartmentStatus.INACTIVE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DEPARTMENT_INACTIVE", "message": "Department is inactive or unavailable."}
            )

        # 4. Check IST Date/Time protection
        ist_now = get_ist_now()
        today_ist = ist_now.date()
        if apt_in.appointment_date < today_ist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_APPOINTMENT_TIME", "message": "Appointment date cannot be in the past."}
            )

        if apt_in.appointment_date == today_ist and apt_in.start_time <= ist_now.time():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_APPOINTMENT_TIME", "message": "Appointment start time cannot be in the past."}
            )

        # 5. Reuse Dynamic Availability Check Engine from Phase 3
        slot_check = check_slot_availability(
            db=db,
            doctor_id=doc.id,
            target_date=apt_in.appointment_date,
            start_time=apt_in.start_time
        )
        if not slot_check["is_available"]:
            slot_status = slot_check["status"]
            reason = slot_check["reason"]
            if slot_status in ["BLOCKED", "DOCTOR_ON_LEAVE"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "DOCTOR_ON_LEAVE", "message": f"Doctor is unavailable: {reason}"}
                )
            elif slot_status in ["FACILITY_UNAVAILABLE", "FACILITY_INACTIVE"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "FACILITY_TEMPORARILY_UNAVAILABLE", "message": f"Facility unavailable: {reason}"}
                )
            elif slot_status == "DEPARTMENT_INACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "DEPARTMENT_INACTIVE", "message": f"Department unavailable: {reason}"}
                )
            elif slot_status == "BOOKED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "SLOT_ALREADY_BOOKED", "message": "The selected appointment slot is no longer available."}
                )
            elif slot_status == "PAST":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_APPOINTMENT_TIME", "message": "The selected appointment slot has already passed."}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "DOCTOR_UNAVAILABLE", "message": f"Slot is unavailable: {reason}"}
                )

        # 6. Calculate end_time if missing
        if apt_in.end_time:
            end_time_val = apt_in.end_time
        else:
            duration = doc.availabilities[0].slot_duration_minutes if doc.availabilities else 30
            dt_start = datetime.combine(apt_in.appointment_date, apt_in.start_time)
            dt_end = dt_start + timedelta(minutes=duration)
            end_time_val = dt_end.time()

        # 7. Create Appointment safely in DB transaction
        try:
            apt = AppointmentRepository.create_appointment(
                db=db,
                patient_id=target_patient_id,
                doctor_id=doc.id,
                facility_id=fac.id,
                department_id=dept_id,
                apt_date=apt_in.appointment_date,
                start_time=apt_in.start_time,
                end_time=end_time_val,
                booking_channel=apt_in.booking_channel,
                reason_for_visit=apt_in.reason_for_visit
            )
        except ValueError as val_err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "SLOT_ALREADY_BOOKED", "message": str(val_err)}
            )

        # 8. Record Audit Log
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=current_user.id,
            event_type="APPOINTMENT_CREATED",
            old_status=None,
            new_status=apt.status.value,
            notes=f"Appointment booked via {apt_in.booking_channel.value}"
        )

        # 9. Trigger Notification (Decoupled & resilient)
        NotificationService.send_appointment_notification(db, apt, event_type="BOOKING")
        db.refresh(apt)

        return cls.format_appointment_response(db, apt)

    @classmethod
    def get_appointment_by_id(cls, db: Session, appointment_id: int, current_user: User) -> AppointmentResponse:
        apt = AppointmentRepository.get_by_id(db, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPOINTMENT_NOT_FOUND", "message": f"Appointment with ID {appointment_id} not found."}
            )

        # Object-level authorization
        if current_user.role == UserRole.CUSTOMER:
            if not current_user.patient_profile or apt.patient_id != current_user.patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied. You cannot view another customer's appointment."}
                )
        elif current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied. Providers can only view appointments assigned to their doctor or facility."}
                )

        return cls.format_appointment_response(db, apt)

    @classmethod
    def get_by_confirmation_code(cls, db: Session, code: str, current_user: User) -> AppointmentResponse:
        apt = AppointmentRepository.get_by_confirmation_code(db, code)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPOINTMENT_NOT_FOUND", "message": f"Appointment with confirmation code '{code}' not found."}
            )

        # Object-level authorization
        if current_user.role == UserRole.CUSTOMER:
            if not current_user.patient_profile or apt.patient_id != current_user.patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied."}
                )
        elif current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied."}
                )

        return cls.format_appointment_response(db, apt)

    @classmethod
    def cancel_appointment(
        cls, db: Session, appointment_id: int, cancel_in: AppointmentCancelRequest, current_user: User
    ) -> AppointmentResponse:
        apt = AppointmentRepository.get_by_id(db, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPOINTMENT_NOT_FOUND", "message": f"Appointment with ID {appointment_id} not found."}
            )

        # Authorization
        if current_user.role == UserRole.CUSTOMER:
            if not current_user.patient_profile or apt.patient_id != current_user.patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied."}
                )
        elif current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied."}
                )

        # Check status & lifecycle
        if apt.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "APPOINTMENT_ALREADY_CANCELLED", "message": "Appointment is already cancelled."}
            )
        if apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "APPOINTMENT_ALREADY_COMPLETED", "message": "Completed appointments cannot be cancelled."}
            )
        if apt.status == AppointmentStatus.NO_SHOW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATUS_TRANSITION", "message": "NO_SHOW appointments cannot be cancelled."}
            )

        old_st = apt.status
        apt.status = AppointmentStatus.CANCELLED
        apt.cancellation_reason = cancel_in.reason
        apt.cancelled_at = datetime.utcnow()
        db.commit()

        # Audit log
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=current_user.id,
            event_type="APPOINTMENT_CANCELLED",
            old_status=old_st.value if old_st else None,
            new_status=AppointmentStatus.CANCELLED.value,
            notes=f"Cancelled by user {current_user.id}. Reason: {cancel_in.reason}"
        )

        # Notification
        NotificationService.send_appointment_notification(db, apt, event_type="CANCELLATION")
        db.refresh(apt)

        return cls.format_appointment_response(db, apt)

    @classmethod
    def reschedule_appointment(
        cls, db: Session, appointment_id: int, reschedule_in: AppointmentRescheduleRequest, current_user: User
    ) -> AppointmentResponse:
        apt = AppointmentRepository.get_by_id(db, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPOINTMENT_NOT_FOUND", "message": f"Appointment with ID {appointment_id} not found."}
            )

        # Authorization
        if current_user.role == UserRole.CUSTOMER:
            if not current_user.patient_profile or apt.patient_id != current_user.patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied."}
                )
        elif current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Access denied."}
                )

        # Check existing state
        if apt.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "RESCHEDULE_NOT_ALLOWED", "message": f"Cannot reschedule an appointment with status '{apt.status.value}'."}
            )

        # Check new slot date/time
        ist_now = get_ist_now()
        today_ist = ist_now.date()
        if reschedule_in.new_date < today_ist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_APPOINTMENT_TIME", "message": "New appointment date cannot be in the past."}
            )
        if reschedule_in.new_date == today_ist and reschedule_in.new_start_time <= ist_now.time():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_APPOINTMENT_TIME", "message": "New appointment start time cannot be in the past."}
            )

        # Check dynamic availability for new slot
        slot_check = check_slot_availability(
            db=db,
            doctor_id=apt.doctor_id,
            target_date=reschedule_in.new_date,
            start_time=reschedule_in.new_start_time
        )
        if not slot_check["is_available"]:
            slot_status = slot_check["status"]
            reason = slot_check["reason"]
            if slot_status == "BLOCKED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "DOCTOR_ON_LEAVE", "message": f"Doctor is unavailable on requested date: {reason}"}
                )
            elif slot_status == "BOOKED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "SLOT_ALREADY_BOOKED", "message": "The requested new appointment slot is already occupied."}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "DOCTOR_UNAVAILABLE", "message": f"New slot is unavailable: {reason}"}
                )

        # Calculate new end time
        if reschedule_in.new_end_time:
            new_end_val = reschedule_in.new_end_time
        else:
            doc = apt.doctor
            duration = doc.availabilities[0].slot_duration_minutes if (doc and doc.availabilities) else 30
            dt_start = datetime.combine(reschedule_in.new_date, reschedule_in.new_start_time)
            dt_end = dt_start + timedelta(minutes=duration)
            new_end_val = dt_end.time()

        old_date = apt.appointment_date
        old_start = apt.start_time

        apt.appointment_date = reschedule_in.new_date
        apt.start_time = reschedule_in.new_start_time
        apt.end_time = new_end_val

        db.commit()

        # Audit entry
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=current_user.id,
            event_type="APPOINTMENT_RESCHEDULED",
            old_status=apt.status.value,
            new_status=apt.status.value,
            notes=reschedule_in.reason or "Appointment rescheduled",
            metadata_json={
                "old_date": str(old_date),
                "old_start_time": str(old_start),
                "new_date": str(reschedule_in.new_date),
                "new_start_time": str(reschedule_in.new_start_time)
            }
        )

        # Notification
        NotificationService.send_appointment_notification(db, apt, event_type="RESCHEDULE")
        db.refresh(apt)

        return cls.format_appointment_response(db, apt)

    @classmethod
    def get_my_appointments(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[date] = None,
        upcoming: bool = False
    ) -> List[AppointmentResponse]:
        if current_user.role != UserRole.CUSTOMER or not current_user.patient_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Only registered customers can access personal appointments."}
            )

        apts = AppointmentRepository.get_patient_appointments(
            db=db,
            patient_id=current_user.patient_profile.id,
            status_filter=status_filter,
            date_filter=date_filter,
            upcoming_only=upcoming
        )
        return [cls.format_appointment_response(db, a) for a in apts]

    @classmethod
    def get_provider_appointments(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[date] = None
    ) -> List[AppointmentResponse]:
        if current_user.role != UserRole.PROVIDER or not current_user.doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Only healthcare providers can view provider queue."}
            )

        prov_doc = current_user.doctor_profile
        apts = AppointmentRepository.get_provider_appointments(
            db=db,
            doctor_id=prov_doc.id,
            facility_id=prov_doc.facility_id,
            status_filter=status_filter,
            date_filter=date_filter
        )
        return [cls.format_appointment_response(db, a) for a in apts]

    @classmethod
    def get_admin_appointments(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[date] = None,
        facility_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        confirmation_code: Optional[str] = None
    ) -> List[AppointmentResponse]:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Admin authorization required."}
            )

        apts = AppointmentRepository.get_admin_appointments(
            db=db,
            status_filter=status_filter,
            date_filter=date_filter,
            facility_id=facility_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            confirmation_code=confirmation_code
        )
        return [cls.format_appointment_response(db, a) for a in apts]

    @classmethod
    def check_in_appointment(
        cls, db: Session, appointment_id: int, current_user: Optional[User] = None
    ) -> CheckInResponse:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "APPOINTMENT_NOT_FOUND", "message": f"Appointment {appointment_id} not found."}
            )

        # Authorization check
        if current_user and current_user.role == UserRole.CUSTOMER:
            if not current_user.patient_profile or apt.patient_id != current_user.patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "UNAUTHORIZED_APPOINTMENT_ACCESS", "message": "Customers can only check in for their own appointments."}
                )

        # Status validation
        if apt.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "APPOINTMENT_CANCELLED", "message": "Cancelled appointments cannot be checked in."}
            )
        if apt.status == AppointmentStatus.COMPLETED or getattr(apt, "visit_status", None) == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "APPOINTMENT_COMPLETED", "message": "Completed appointments cannot be checked in."}
            )

        # Operational status pre-check (Phase 18 rule)
        if apt.doctor and (apt.doctor.status == DoctorStatus.INACTIVE or apt.doctor.status == DoctorStatus.ON_LEAVE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DOCTOR_UNAVAILABLE", "message": "Doctor is currently unavailable for OPD check-in."}
            )
        if apt.facility and apt.facility.status == FacilityStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "FACILITY_UNAVAILABLE", "message": "Facility is currently inactive."}
            )
        if apt.department and apt.department.status == DepartmentStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DEPARTMENT_UNAVAILABLE", "message": "Department is currently inactive."}
            )

        # Check-in Window Validation (Section 6 rule)
        ist_now = get_ist_now()
        today_ist = ist_now.date()

        if apt.appointment_date > today_ist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CHECKIN_TOO_EARLY", "message": "Check-in opens 60 minutes before your scheduled appointment time."}
            )
        elif apt.appointment_date < today_ist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CHECKIN_EXPIRED", "message": "Check-in window for this appointment date has expired."}
            )
        else:
            dt_start = datetime.combine(today_ist, apt.start_time)
            now_naive = ist_now.replace(tzinfo=None) if hasattr(ist_now, "tzinfo") and ist_now.tzinfo else ist_now
            diff_mins = (now_naive - dt_start).total_seconds() / 60.0
            if diff_mins < -60:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "CHECKIN_TOO_EARLY", "message": "Check-in opens 60 minutes before your scheduled appointment time."}
                )
            if diff_mins > 120:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "CHECKIN_EXPIRED", "message": "Check-in window for this appointment time has expired."}
                )

        # Idempotent double check-in protection
        current_vstatus = getattr(apt, "visit_status", "NOT_CHECKED_IN") or "NOT_CHECKED_IN"
        if current_vstatus in ["WAITING", "IN_CONSULTATION", "COMPLETED"] and apt.queue_token:
            return CheckInResponse(
                appointment_id=apt.id,
                confirmation_code=apt.confirmation_code,
                queue_token=apt.queue_token,
                visit_status=current_vstatus,
                checked_in_at=apt.checked_in_at or datetime.utcnow(),
                message="Already checked in."
            )

        # Generate Queue Token
        count_checked_in = db.query(Appointment).filter(
            Appointment.doctor_id == apt.doctor_id,
            Appointment.appointment_date == apt.appointment_date,
            Appointment.queue_token.isnot(None)
        ).count()
        token_str = f"P-{(count_checked_in + 1):03d}"

        now_utc = datetime.utcnow()
        apt.queue_token = token_str
        apt.checked_in_at = now_utc
        apt.visit_status = "WAITING"

        # Audit Log
        actor_id = current_user.id if current_user else (apt.patient.user_id if apt.patient else 1)
        actor_role = (current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)) if current_user else "PATIENT"
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=actor_id,
            event_type="PATIENT_CHECKED_IN",
            old_status=current_vstatus,
            new_status="WAITING",
            notes=f"Patient checked in via {actor_role}. Token: {token_str}"
        )

        db.commit()
        db.refresh(apt)

        # Dispatch Check-In SMS (Non-blocking)
        try:
            from app.services.notification_service import NotificationService
            user_lang = current_user.language if hasattr(current_user, "language") else Language.HI
            NotificationService.send_appointment_notification(db, apt, event_type="CHECKIN", language=user_lang)
        except Exception:
            pass

        return CheckInResponse(
            appointment_id=apt.id,
            confirmation_code=apt.confirmation_code,
            queue_token=token_str,
            visit_status="WAITING",
            checked_in_at=apt.checked_in_at,
            message="Check-in successful. Queue token assigned."
        )

    @classmethod
    def start_consultation(
        cls, db: Session, appointment_id: int, current_user: Optional[User] = None
    ) -> AppointmentResponse:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

        # Authorization
        if current_user and current_user.role == UserRole.CUSTOMER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for Customer role.")

        if current_user and current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        vstatus = getattr(apt, "visit_status", "NOT_CHECKED_IN") or "NOT_CHECKED_IN"
        if vstatus == "NOT_CHECKED_IN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "PATIENT_NOT_CHECKED_IN", "message": "Patient must check in before starting consultation."}
            )
        if vstatus == "COMPLETED" or apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": "Cannot start consultation for a completed appointment."}
            )

        old_st = apt.status
        apt.visit_status = "IN_CONSULTATION"
        apt.status = AppointmentStatus.IN_PROGRESS
        apt.consultation_started_at = datetime.utcnow()

        actor_id = current_user.id if current_user else 1
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=actor_id,
            event_type="CONSULTATION_STARTED",
            old_status=old_st.value if hasattr(old_st, "value") else str(old_st),
            new_status=AppointmentStatus.IN_PROGRESS.value,
            notes=f"Consultation started by actor #{actor_id}"
        )

        db.commit()
        db.refresh(apt)
        return cls.format_appointment_response(db, apt)

    @classmethod
    def complete_consultation(
        cls, db: Session, appointment_id: int, current_user: Optional[User] = None
    ) -> AppointmentResponse:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

        # Authorization
        if current_user and current_user.role == UserRole.CUSTOMER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for Customer role.")

        if current_user and current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        vstatus = getattr(apt, "visit_status", "NOT_CHECKED_IN") or "NOT_CHECKED_IN"
        if vstatus != "IN_CONSULTATION" or apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": f"Cannot complete consultation from status {vstatus}. Consultation must be in progress."}
            )

        old_st = apt.status
        apt.visit_status = "COMPLETED"
        apt.status = AppointmentStatus.COMPLETED
        apt.consultation_completed_at = datetime.utcnow()

        actor_id = current_user.id if current_user else 1
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=actor_id,
            event_type="CONSULTATION_COMPLETED",
            old_status=old_st.value if hasattr(old_st, "value") else str(old_st),
            new_status=AppointmentStatus.COMPLETED.value,
            notes=f"Consultation completed by actor #{actor_id}"
        )

        db.commit()
        db.refresh(apt)
        return cls.format_appointment_response(db, apt)

    @classmethod
    def mark_no_show(
        cls, db: Session, appointment_id: int, current_user: Optional[User] = None
    ) -> AppointmentResponse:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment not found.")

        # Authorization
        if current_user and current_user.role == UserRole.CUSTOMER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for Customer role.")

        if current_user and current_user.role == UserRole.PROVIDER:
            prov_doc = current_user.doctor_profile
            if not prov_doc or not (apt.doctor_id == prov_doc.id or apt.facility_id == prov_doc.facility_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        vstatus = getattr(apt, "visit_status", "NOT_CHECKED_IN") or "NOT_CHECKED_IN"
        if vstatus == "COMPLETED" or apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": "Cannot mark completed appointment as no-show."}
            )

        old_st = apt.status
        apt.visit_status = "NO_SHOW"
        apt.status = AppointmentStatus.NO_SHOW

        actor_id = current_user.id if current_user else 1
        AppointmentRepository.create_audit_entry(
            db=db,
            appointment_id=apt.id,
            actor_id=actor_id,
            event_type="PATIENT_NO_SHOW",
            old_status=old_st.value if hasattr(old_st, "value") else str(old_st),
            new_status=AppointmentStatus.NO_SHOW.value,
            notes=f"Appointment marked no-show by actor #{actor_id}"
        )

        db.commit()
        db.refresh(apt)
        return cls.format_appointment_response(db, apt)
