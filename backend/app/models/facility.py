from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.enums import FacilityType, FacilityStatus, DepartmentStatus

class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    facility_type = Column(Enum(FacilityType), default=FacilityType.GOVERNMENT_HOSPITAL, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=False)
    village = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), default="Maharashtra", nullable=False)
    pincode = Column(String(10), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone_number = Column(String(20), nullable=False, default="+91-20-108")
    status = Column(Enum(FacilityStatus), default=FacilityStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    area = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    email = Column(String(100), nullable=True)
    is_24x7 = Column(Boolean, default=True, nullable=False)
    emergency_available = Column(Boolean, default=False, nullable=False)
    ambulance_available = Column(Boolean, default=False, nullable=False)
    telemedicine_available = Column(Boolean, default=False, nullable=False)
    emergency_level = Column(String(50), default="BASIC_EMERGENCY", nullable=True)
    icu_available = Column(Boolean, default=False, nullable=False)
    trauma_support = Column(Boolean, default=False, nullable=False)
    cardiac_support = Column(Boolean, default=False, nullable=False)
    pediatric_emergency = Column(Boolean, default=False, nullable=False)
    is_demo_data = Column(Boolean, default=True, nullable=False)
    last_verified_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    departments = relationship("Department", back_populates="facility", cascade="all, delete-orphan")
    doctors = relationship("Doctor", back_populates="facility")
    appointments = relationship("Appointment", back_populates="facility")
    emergency_contacts = relationship("EmergencyContact", back_populates="facility", cascade="all, delete-orphan")
    facility_services = relationship("FacilityService", back_populates="facility", cascade="all, delete-orphan")
    ambulances = relationship("Ambulance", back_populates="facility", cascade="all, delete-orphan")

    @property
    def emergency_capable(self) -> bool:
        return self.emergency_available


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(DepartmentStatus), default=DepartmentStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    facility = relationship("Facility", back_populates="departments")
    doctors = relationship("Doctor", back_populates="department")
    appointments = relationship("Appointment", back_populates="department")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    contact_type = Column(String(50), default="AMBULANCE", nullable=False) # e.g. AMBULANCE, HELPLINE, CASUALTY
    priority = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    facility = relationship("Facility", back_populates="emergency_contacts")
