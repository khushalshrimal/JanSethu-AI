from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.enums import DoctorStatus, ExceptionType

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    qualification = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False)
    consultation_type = Column(String(50), default="OPD_IN_PERSON", nullable=False)
    phone_number = Column(String(20), nullable=True)
    experience_years = Column(Integer, default=5, nullable=False)
    languages = Column(String(100), default="Hindi, English", nullable=False)
    gender = Column(String(20), default="Male", nullable=False)
    status = Column(Enum(DoctorStatus), default=DoctorStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_demo_data = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    user = relationship("User", back_populates="doctor_profile")
    facility = relationship("Facility", back_populates="doctors")
    department = relationship("Department", back_populates="doctors")
    availabilities = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    schedule_exceptions = relationship("DoctorScheduleException", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")
    appointment_slots = relationship("AppointmentSlot", back_populates="doctor", cascade="all, delete-orphan")


class DoctorAvailability(Base):
    __tablename__ = "doctor_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    effective_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="availabilities")


class DoctorScheduleException(Base):
    __tablename__ = "doctor_schedule_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    exception_type = Column(Enum(ExceptionType), default=ExceptionType.LEAVE, nullable=False)
    reason = Column(Text, nullable=True) # e.g. Doctor leave, Emergency Duty, Meeting, Holiday
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    doctor = relationship("Doctor", back_populates="schedule_exceptions")
