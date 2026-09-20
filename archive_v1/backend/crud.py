import datetime
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas

def get_smart_routed_facilities(
    db: Session,
    city: Optional[str] = None,
    area: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    is_emergency: bool = False
) -> List[models.Facility]:
    all_facs = db.query(models.Facility).all()
    if not all_facs:
        return []

    # Calculated Smart Scores
    scored_facilities = []
    
    for f in all_facs:
        score = 0
        search_term = (search or area or city or "").lower()
        service_term = (service or "").lower()
        
        # 1. Location match & Simulated Distance calculation (km)
        loc_match = (
            search_term in f.area.lower() or 
            search_term in f.city.lower() or 
            search_term in f.name.lower() or
            (f.name_hi and search_term in f.name_hi.lower())
        )
        
        # Simulated distance: Baramati PHC is 2.1km, District Hospital is 4.2km, Sanganer SDH is 3.5km
        if "phc" in f.name.lower() or "rural" in f.name.lower():
            simulated_distance = 2.1
        elif "malviya nagar" in f.name.lower():
            simulated_distance = 1.8
        elif "sanganer" in f.name.lower():
            simulated_distance = 3.5
        elif "baramati" in f.name.lower():
            simulated_distance = 4.2
        else:
            simulated_distance = 5.8

        distance_score = max(0, 25 - (simulated_distance * 2))

        # 2. Service Match (Weight: 35%)
        service_score = 0
        if service_term and service_term in f.services.lower():
            service_score = 35
        elif loc_match:
            service_score = 25
        else:
            service_score = 15

        # 3. Doctor Availability (Weight: 25%)
        # Check open slots in database
        available_slots = db.query(models.Slot).filter(
            models.Slot.facility_id == f.id,
            models.Slot.available == True
        ).all()
        
        doc_avail_score = 25 if len(available_slots) > 0 else 0

        # 4. Emergency Capability (Weight: 15% normal, +50 boost on emergency)
        is_emerg_cap = "emergency" in f.services.lower() or "hospital" in f.facility_type.lower()
        emergency_score = 15 if is_emerg_cap else 0
        
        if is_emergency:
            score = (100 if is_emerg_cap else 0) + doc_avail_score + distance_score
        else:
            score = service_score + doc_avail_score + distance_score + emergency_score

        # Attach computed metadata to facility model instance
        f.simulated_distance = simulated_distance
        f.doctor_available = len(available_slots) > 0
        f.emergency_available = is_emerg_cap
        f.smart_score = round(score, 1)
        f.next_opd_slot = available_slots[0].time if len(available_slots) > 0 else "No slots today"
        
        scored_facilities.append(f)

    # Sort descending by Smart Score (Suitable & available facilities rank above closer unavailable ones)
    scored_facilities.sort(key=lambda x: (x.smart_score, -x.simulated_distance), reverse=True)
    return scored_facilities

def get_facilities(
    db: Session,
    city: Optional[str] = None,
    area: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None
) -> List[models.Facility]:
    return get_smart_routed_facilities(db, city=city, area=area, service=service, search=search)

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
        status="confirmed",
        doctor_name=appointment.doctor_name or "Dr. Sharma"
    )
    # Mark slot as unavailable if matching slot found
    slot = db.query(models.Slot).filter(
        models.Slot.facility_id == appointment.facility_id,
        models.Slot.available == True
    ).first()
    if slot:
        slot.available = False
        if slot.doctor_name:
            db_appointment.doctor_name = slot.doctor_name

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # Generate Token Number format: A-104
    db_appointment.token_number = f"A-{100 + db_appointment.id}"
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def get_appointments(
    db: Session,
    facility_id: Optional[int] = None,
    status: Optional[str] = None,
    phone: Optional[str] = None
) -> List[models.Appointment]:
    query = db.query(models.Appointment)
    if facility_id:
        query = query.filter(models.Appointment.facility_id == facility_id)
    if status:
        query = query.filter(models.Appointment.status == status)
    if phone:
        query = query.filter(models.Appointment.phone.ilike(f"%{phone}%"))
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
