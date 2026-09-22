from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

class FacilityService(Base):
    __tablename__ = "facility_services"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    specialty_name = Column(String(100), nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    emergency_supported = Column(Boolean, default=False, nullable=False)
    outpatient_supported = Column(Boolean, default=True, nullable=False)
    inpatient_supported = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    facility = relationship("Facility", back_populates="facility_services")
    department = relationship("Department")
