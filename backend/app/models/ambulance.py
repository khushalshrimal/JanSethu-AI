from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.enums import AmbulanceStatus, AmbulanceType

class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_identifier = Column(String(50), unique=True, index=True, nullable=False)
    ambulance_type = Column(Enum(AmbulanceType), default=AmbulanceType.BASIC_LIFE_SUPPORT, nullable=False)
    status = Column(Enum(AmbulanceStatus), default=AmbulanceStatus.AVAILABLE, nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    driver_name = Column(String(100), nullable=True)
    driver_phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_demo_data = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    facility = relationship("Facility", back_populates="ambulances")
