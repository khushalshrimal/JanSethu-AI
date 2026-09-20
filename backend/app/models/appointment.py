from sqlalchemy import Column, Integer, String, Date, Time, Enum, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.enums import AppointmentStatus, BookingChannel

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    appointment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.BOOKED, nullable=False)
    booking_channel = Column(Enum(BookingChannel), default=BookingChannel.PWA, nullable=False)
    reason_for_visit = Column(Text, nullable=True) # Non-diagnostic user query text
    confirmation_code = Column(String(50), unique=True, index=True, nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    reminder_sent_at = Column(DateTime, nullable=True)
    queue_token = Column(String(50), nullable=True, index=True)
    checked_in_at = Column(DateTime, nullable=True)
    visit_status = Column(String(30), default="NOT_CHECKED_IN", server_default="NOT_CHECKED_IN", nullable=False)
    consultation_started_at = Column(DateTime, nullable=True)
    consultation_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("PatientProfile", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    facility = relationship("Facility", back_populates="appointments")
    department = relationship("Department", back_populates="appointments")
    sms_notifications = relationship("SMSNotification", back_populates="appointment", cascade="all, delete-orphan")
    audit_logs = relationship("AppointmentAuditLog", back_populates="appointment", cascade="all, delete-orphan")

    # Double-booking protection: Unique constraint on active slot per doctor
    __table_args__ = (
        UniqueConstraint('doctor_id', 'appointment_date', 'start_time', name='uq_doctor_slot_time'),
    )
