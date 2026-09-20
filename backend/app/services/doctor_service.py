from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from fastapi import HTTPException, status
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.facility_repository import FacilityRepository
from app.models.doctor import DoctorScheduleException
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.doctor import (
    DoctorCreate, DoctorResponse, DoctorAvailabilityCreate, DoctorAvailabilityResponse,
    DoctorScheduleExceptionCreate, DoctorScheduleExceptionResponse, DoctorAvailabilityQueryResponse
)
from app.services.availability_service import AvailabilityService

class DoctorService:
    @staticmethod
    def get_doctor(db: Session, doctor_id: int) -> DoctorResponse:
        doc = DoctorRepository.get_by_id(db, doctor_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found."
            )
        return doc

    @staticmethod
    def list_doctors(db: Session, facility_id: int, department_id: Optional[int] = None) -> List[DoctorResponse]:
        return DoctorRepository.get_by_facility(db, facility_id, department_id)

    @staticmethod
    def create_doctor(db: Session, doctor_in: DoctorCreate) -> DoctorResponse:
        fac = FacilityRepository.get_by_id(db, doctor_in.facility_id)
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {doctor_in.facility_id} not found."
            )
        return DoctorRepository.create_doctor(db, doctor_in)

    @staticmethod
    def add_availability(db: Session, doctor_id: int, avail_in: DoctorAvailabilityCreate) -> DoctorAvailabilityResponse:
        doc = DoctorRepository.get_by_id(db, doctor_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found."
            )
        return DoctorRepository.add_availability(db, doctor_id, avail_in)

    @staticmethod
    def get_doctor_availability_slots(db: Session, doctor_id: int, target_date: date) -> DoctorAvailabilityQueryResponse:
        """Public dynamic availability generator for any given date."""
        return AvailabilityService.generate_doctor_slots(db, doctor_id, target_date)

    @staticmethod
    def add_schedule_exception(
        db: Session,
        doctor_id: int,
        exc_in: DoctorScheduleExceptionCreate,
        current_user: User
    ) -> DoctorScheduleExceptionResponse:
        doc = DoctorRepository.get_by_id(db, doctor_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found."
            )

        # Scoped authorization check for Providers
        if current_user.role == UserRole.PROVIDER:
            if not current_user.doctor_profile or current_user.doctor_profile.id != doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Providers can only manage schedule exceptions for their own doctor profile."
                )

        db_exc = DoctorScheduleException(doctor_id=doctor_id, **exc_in.model_dump())
        db.add(db_exc)
        db.commit()
        db.refresh(db_exc)
        return db_exc
