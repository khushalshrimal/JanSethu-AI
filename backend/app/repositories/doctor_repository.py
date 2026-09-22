from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.doctor import Doctor, DoctorAvailability
from app.schemas.doctor import DoctorCreate, DoctorAvailabilityCreate

class DoctorRepository:
    @staticmethod
    def get_by_id(db: Session, doctor_id: int) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.id == doctor_id).first()

    @staticmethod
    def get_by_facility(db: Session, facility_id: int, department_id: Optional[int] = None) -> List[Doctor]:
        query = db.query(Doctor).filter(Doctor.facility_id == facility_id, Doctor.is_active == True)
        if department_id:
            query = query.filter(Doctor.department_id == department_id)
        return query.all()

    @staticmethod
    def search_doctors(db: Session, q: Optional[str] = None, facility_id: Optional[int] = None, department_id: Optional[int] = None) -> List[Doctor]:
        query = db.query(Doctor).filter(Doctor.is_active == True)
        if facility_id:
            query = query.filter(Doctor.facility_id == facility_id)
        if department_id:
            query = query.filter(Doctor.department_id == department_id)
        if q:
            query = query.filter(Doctor.name.ilike(f"%{q}%"))
        return query.all()

    @staticmethod
    def create_doctor(db: Session, doctor_in: DoctorCreate) -> Doctor:
        db_doctor = Doctor(**doctor_in.model_dump())
        db.add(db_doctor)
        db.commit()
        db.refresh(db_doctor)
        return db_doctor

    @staticmethod
    def add_availability(db: Session, doctor_id: int, avail_in: DoctorAvailabilityCreate) -> DoctorAvailability:
        db_avail = DoctorAvailability(doctor_id=doctor_id, **avail_in.model_dump())
        db.add(db_avail)
        db.commit()
        db.refresh(db_avail)
        return db_avail
