from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.enums import CallSessionStatus, NotificationStatus, Language

class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    language = Column(Enum(Language), default=Language.HI, nullable=False)
    channel = Column(String(50), default="TELEPHONY_SIMULATOR", nullable=False)
    provider = Column(String(50), default="development", nullable=False)
    provider_call_id = Column(String(100), nullable=True, index=True)
    status = Column(Enum(CallSessionStatus), default=CallSessionStatus.ACTIVE, nullable=False)
    
    # State Machine Persistence Fields
    current_state = Column(String(50), default="GREETING", nullable=False)
    selected_intent = Column(String(50), nullable=True)
    selected_facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True)
    selected_department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    selected_doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    selected_date = Column(String(20), nullable=True)
    selected_start_time = Column(String(20), nullable=True)
    selected_end_time = Column(String(20), nullable=True)
    context_json = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("ConversationMessage", back_populates="call_session", cascade="all, delete-orphan")
    facility = relationship("Facility", foreign_keys=[selected_facility_id])
    department = relationship("Department", foreign_keys=[selected_department_id])
    doctor = relationship("Doctor", foreign_keys=[selected_doctor_id])


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False)
    sender_type = Column(String(20), nullable=False) # USER | SYSTEM
    message_type = Column(String(20), nullable=False) # VOICE | TEXT | DTMF | SYSTEM
    language = Column(Enum(Language), default=Language.HI, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    call_session = relationship("CallSession", back_populates="messages")


class SMSNotification(Base):
    __tablename__ = "sms_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True)
    phone_number = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    language = Column(Enum(Language), default=Language.HI, nullable=False)
    event_type = Column(String(50), default="BOOKING", nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.QUEUED, nullable=False)
    provider = Column(String(50), default="DEV_CONSOLE", nullable=False)
    provider_message_id = Column(String(100), nullable=True, index=True)
    failure_reason = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    appointment = relationship("Appointment", back_populates="sms_notifications")
