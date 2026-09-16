import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base

class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    name_hi = Column(String, nullable=True) # Hindi name for accessibility
    city = Column(String, nullable=False, index=True)
    area = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    services = Column(Text, nullable=False) # JSON or comma-separated string of services
    contact_phone = Column(String, nullable=False)
    facility_type = Column(String, default="Government Hospital") # Hospital, PHC, CHC, Clinic

    slots = relationship("Slot", back_populates="facility", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="facility", cascade="all, delete-orphan")

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD
    time = Column(String, nullable=False) # HH:MM AM/PM
    available = Column(Boolean, default=True)
    doctor_name = Column(String, nullable=True)
    department = Column(String, nullable=True)

    facility = relationship("Facility", back_populates="slots")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    service = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, confirmed, rejected, rescheduled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    facility = relationship("Facility", back_populates="appointments")
