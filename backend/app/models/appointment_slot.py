from sqlalchemy import Column, Integer, Date, Time, Enum, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.enums import SlotStatus

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(Enum(SlotStatus), default=SlotStatus.AVAILABLE, nullable=False, index=True)
    is_demo_data = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="appointment_slots")
    facility = relationship("Facility")
    department = relationship("Department")

    __table_args__ = (
        UniqueConstraint('doctor_id', 'slot_date', 'start_time', name='uq_doctor_slot_date_start'),
    )
