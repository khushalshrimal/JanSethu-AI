import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
from app.models.appointment import Appointment
from app.models.appointment_audit import AppointmentAuditLog
from app.models.enums import AppointmentStatus, BookingChannel
from app.schemas.appointment import AppointmentCreate
from app.utils.timezone import get_ist_now

def generate_unique_confirmation_code(db: Session) -> str:
    year = get_ist_now().year
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(10):
        code_str = ''.join(secrets.choice(alphabet) for _ in range(6))
        code = f"JS-{year}-{code_str}"
        existing = db.query(Appointment).filter(Appointment.confirmation_code == code).first()
        if not existing:
            return code
    # Fallback with timestamp
    return f"JS-{year}-{secrets.token_hex(3).upper()}"

class AppointmentRepository:
    @staticmethod
    def get_by_id(db: Session, appointment_id: int) -> Optional[Appointment]:
        return db.query(Appointment).filter(Appointment.id == appointment_id).first()

    @staticmethod
    def get_by_confirmation_code(db: Session, code: str) -> Optional[Appointment]:
        if not code or not str(code).strip():
            return None

        raw_code = str(code).strip()
        clean_code = raw_code.upper()

        # 1. Exact match on confirmation_code
        apt = db.query(Appointment).filter(Appointment.confirmation_code == clean_code).first()
        if apt:
            return apt

        # 2. Case-insensitive match using func.upper
        from sqlalchemy import func
        apt = db.query(Appointment).filter(func.upper(Appointment.confirmation_code) == clean_code).first()
        if apt:
            return apt

        # 3. Handle prefix variations (JS-, JAN-REF-, REF-, APP-)
        alt_code = clean_code
        for prefix in ["JAN-REF-", "REF-", "APP-", "JS-"]:
            if alt_code.startswith(prefix):
                alt_code = alt_code[len(prefix):]
                break

        if alt_code != clean_code:
            js_code = f"JS-{alt_code}"
            apt = db.query(Appointment).filter(Appointment.confirmation_code == js_code).first()
            if apt:
                return apt

        # 4. Fallback: If numeric string, try matching appointment ID
        if clean_code.isdigit():
            try:
                apt_id = int(clean_code)
                apt = db.query(Appointment).filter(Appointment.id == apt_id).first()
                if apt:
                    return apt
            except ValueError:
                pass

        return None

    @staticmethod
    def get_existing_slot_booking(db: Session, doctor_id: int, apt_date: date, start_time: time) -> Optional[Appointment]:
        return db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == apt_date,
            Appointment.start_time == start_time,
            Appointment.status.in_([AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        ).first()

    @staticmethod
    def create_appointment(
        db: Session,
        patient_id: int,
        doctor_id: int,
        facility_id: int,
        department_id: int,
        apt_date: date,
        start_time: time,
        end_time: time,
        booking_channel: BookingChannel,
        reason_for_visit: Optional[str] = None,
        status: AppointmentStatus = AppointmentStatus.BOOKED
    ) -> Appointment:
        existing = AppointmentRepository.get_existing_slot_booking(db, doctor_id, apt_date, start_time)
        if existing:
            raise ValueError("SLOT_ALREADY_BOOKED: The selected appointment slot is no longer available.")

        code = generate_unique_confirmation_code(db)
        db_apt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            facility_id=facility_id,
            department_id=department_id,
            appointment_date=apt_date,
            start_time=start_time,
            end_time=end_time,
            booking_channel=booking_channel,
            reason_for_visit=reason_for_visit,
            confirmation_code=code,
            status=status
        )
        db.add(db_apt)
        try:
            db.commit()
            db.refresh(db_apt)
            return db_apt
        except IntegrityError as e:
            db.rollback()
            raise ValueError("SLOT_ALREADY_BOOKED: The selected appointment slot is no longer available.") from e

    @staticmethod
    def create_audit_entry(
        db: Session,
        appointment_id: int,
        actor_id: Optional[int],
        event_type: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        notes: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> AppointmentAuditLog:
        audit = AppointmentAuditLog(
            appointment_id=appointment_id,
            actor_id=actor_id,
            event_type=event_type,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
            metadata_json=metadata_json
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def get_patient_appointments(
        db: Session,
        patient_id: int,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[date] = None,
        upcoming_only: bool = False
    ) -> List[Appointment]:
        query = db.query(Appointment).filter(Appointment.patient_id == patient_id)
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if date_filter:
            query = query.filter(Appointment.appointment_date == date_filter)
        if upcoming_only:
            today_ist = get_ist_now().date()
            query = query.filter(
                Appointment.appointment_date >= today_ist,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED])
            )
        return query.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()

    @staticmethod
    def get_provider_appointments(
        db: Session,
        doctor_id: Optional[int] = None,
        facility_id: Optional[int] = None,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[date] = None
    ) -> List[Appointment]:
        query = db.query(Appointment)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
        elif facility_id:
            query = query.filter(Appointment.facility_id == facility_id)
        else:
            return []

        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if date_filter:
            query = query.filter(Appointment.appointment_date == date_filter)

        return query.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()

    @staticmethod
    def get_admin_appointments(
        db: Session,
        status_filter: Optional[AppointmentStatus] = None,
        date_filter: Optional[date] = None,
        facility_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        confirmation_code: Optional[str] = None
    ) -> List[Appointment]:
        query = db.query(Appointment)
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if date_filter:
            query = query.filter(Appointment.appointment_date == date_filter)
        if facility_id:
            query = query.filter(Appointment.facility_id == facility_id)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        if confirmation_code:
            query = query.filter(Appointment.confirmation_code.ilike(f"%{confirmation_code}%"))

        return query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.asc()).all()
