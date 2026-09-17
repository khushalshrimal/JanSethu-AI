import datetime
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

def get_emergency_facilities(db: Session) -> List[models.Facility]:
    return db.query(models.Facility).filter(
        (models.Facility.services.ilike("%Emergency%")) |
        (models.Facility.services.ilike("%Maternity%")) |
        (models.Facility.facility_type.ilike("%Hospital%"))
    ).all()

def get_facility(db: Session, facility_id: int) -> Optional[models.Facility]:
    return db.query(models.Facility).filter(models.Facility.id == facility_id).first()

def get_slots(
    db: Session,
    facility_id: int,
    only_available: bool = False,
    date: Optional[str] = None
) -> List[models.Slot]:
    query = db.query(models.Slot).filter(models.Slot.facility_id == facility_id)
    if only_available:
        query = query.filter(models.Slot.available == True)
    if date:
        today = datetime.date.today()
        date_map = {
            "Today": today.strftime("%Y-%m-%d"),
            "Tomorrow": (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "Day After": (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        }
        target_date = date_map.get(date, date)
        query = query.filter((models.Slot.date == date) | (models.Slot.date == target_date))
    return query.all()

def create_slot(db: Session, slot_data: schemas.SlotCreate) -> models.Slot:
    db_slot = models.Slot(
        facility_id=slot_data.facility_id,
        date=slot_data.date,
        time=slot_data.time,
        available=slot_data.available,
        doctor_name=slot_data.doctor_name,
        department=slot_data.department
    )
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def toggle_slot_availability(db: Session, slot_id: int) -> Optional[models.Slot]:
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if slot:
        slot.available = not slot.available
        db.commit()
        db.refresh(slot)
    return slot

def delete_slot(db: Session, slot_id: int) -> bool:
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if slot:
        db.delete(slot)
        db.commit()
        return True
    return False

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

def reschedule_appointment(
    db: Session,
    appointment_id: int,
    new_date: str,
    new_time: str
) -> Optional[models.Appointment]:
    apt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if apt:
        apt.date = new_date
        apt.time = new_time
        apt.status = "rescheduled"
        db.commit()
        db.refresh(apt)
    return apt
