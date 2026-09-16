from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas

def get_facilities(
    db: Session,
    city: Optional[str] = None,
    area: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None
) -> List[models.Facility]:
    query = db.query(models.Facility)
    if city:
        query = query.filter(models.Facility.city.ilike(f"%{city}%"))
    if area:
        query = query.filter(models.Facility.area.ilike(f"%{area}%"))
    if service:
        query = query.filter(models.Facility.services.ilike(f"%{service}%"))
    if search:
        query = query.filter(
            (models.Facility.name.ilike(f"%{search}%")) |
            (models.Facility.name_hi.ilike(f"%{search}%")) |
            (models.Facility.city.ilike(f"%{search}%")) |
            (models.Facility.area.ilike(f"%{search}%")) |
            (models.Facility.services.ilike(f"%{search}%"))
        )
    return query.all()

def get_facility(db: Session, facility_id: int) -> Optional[models.Facility]:
    return db.query(models.Facility).filter(models.Facility.id == facility_id).first()

def get_slots(
    db: Session,
    facility_id: int,
    only_available: bool = True,
    date: Optional[str] = None
) -> List[models.Slot]:
    query = db.query(models.Slot).filter(models.Slot.facility_id == facility_id)
    if only_available:
        query = query.filter(models.Slot.available == True)
    if date:
        query = query.filter(models.Slot.date == date)
    return query.all()

def create_appointment(db: Session, appointment: schemas.AppointmentCreate) -> models.Appointment:
    db_appointment = models.Appointment(
        facility_id=appointment.facility_id,
        service=appointment.service,
        date=appointment.date,
        time=appointment.time,
        patient_name=appointment.patient_name,
        phone=appointment.phone,
        status="pending"
    )
    # Mark slot as unavailable if matching slot found
    slot = db.query(models.Slot).filter(
        models.Slot.facility_id == appointment.facility_id,
        models.Slot.date == appointment.date,
        models.Slot.time == appointment.time,
        models.Slot.available == True
    ).first()
    if slot:
        slot.available = False

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def get_appointments(
    db: Session,
    facility_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[models.Appointment]:
    query = db.query(models.Appointment)
    if facility_id:
        query = query.filter(models.Appointment.facility_id == facility_id)
    if status:
        query = query.filter(models.Appointment.status == status)
    return query.order_by(models.Appointment.created_at.desc()).all()

def get_appointment(db: Session, appointment_id: int) -> Optional[models.Appointment]:
    return db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()

def update_appointment_status(
    db: Session,
    appointment_id: int,
    status: str
) -> Optional[models.Appointment]:
    apt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if apt:
        apt.status = status
        db.commit()
        db.refresh(apt)
    return apt
