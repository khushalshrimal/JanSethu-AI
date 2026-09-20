import logging
import uuid
import asyncio
from datetime import datetime, timedelta, date
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from app.models.telephony import SMSNotification
from app.models.enums import NotificationStatus, Language, AppointmentStatus
from app.models.appointment import Appointment
from app.utils.phone_normalizer import normalize_phone_number
from app.core.templates import AppointmentNotificationContext, render_notification_template
from app.utils.timezone import get_today_ist

logger = logging.getLogger("jansethu.notifications")

class BaseNotificationProvider:
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str, Optional[str]]:
        raise NotImplementedError

class ConsoleSMSProvider(BaseNotificationProvider):
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str, Optional[str]]:
        provider_id = f"DEV-SMS-{uuid.uuid4().hex[:8].upper()}"
        norm_phone = normalize_phone_number(phone_number)
        logger.info(f"[DEV SMS] Queued & Dispatched for {norm_phone} (Ref ID: {provider_id}):\n{message}")
        print(f"\n================ [DEV SMS DISPATCH] ================\nTo: {norm_phone}\nRef: {provider_id}\nMessage:\n{message}\n====================================================\n")
        return True, provider_id, None

class NotificationService:
    provider = ConsoleSMSProvider()

    @staticmethod
    def _format_doc_name(raw_name: str) -> str:
        if not raw_name:
            return "Doctor"
        return raw_name if raw_name.startswith("Dr.") else f"Dr. {raw_name}"

    @classmethod
    def build_context(cls, apt: Appointment, lang: Language = Language.HI) -> AppointmentNotificationContext:
        doc_name = cls._format_doc_name(apt.doctor.name) if apt.doctor else "Doctor"
        fac_name = apt.facility.name if apt.facility else "Facility"
        dept_name = apt.department.name if apt.department else "OPD"
        patient_name = apt.patient.user.name if (apt.patient and apt.patient.user) else "Patient"
        start_str = apt.start_time.strftime("%H:%M") if hasattr(apt.start_time, "strftime") else str(apt.start_time)
        end_str = apt.end_time.strftime("%H:%M") if hasattr(apt.end_time, "strftime") else str(apt.end_time)

        return AppointmentNotificationContext(
            appointment_id=apt.id,
            patient_name=patient_name,
            doctor_name=doc_name,
            facility_name=fac_name,
            department_name=dept_name,
            appointment_date=str(apt.appointment_date),
            start_time=start_str,
            end_time=end_str,
            confirmation_code=apt.confirmation_code,
            cancellation_reason=apt.cancellation_reason or "Patient request",
            queue_token=apt.queue_token,
            language=lang
        )

    @classmethod
    def generate_booking_message(cls, apt: Appointment) -> str:
        ctx = cls.build_context(apt)
        return render_notification_template("APPOINTMENT_CONFIRMED", ctx)

    @classmethod
    def generate_cancellation_message(cls, apt: Appointment) -> str:
        ctx = cls.build_context(apt)
        return render_notification_template("APPOINTMENT_CANCELLED", ctx)

    @classmethod
    def generate_reschedule_message(cls, apt: Appointment) -> str:
        ctx = cls.build_context(apt)
        return render_notification_template("APPOINTMENT_RESCHEDULED", ctx)

    @classmethod
    def generate_reminder_message(cls, apt: Appointment) -> str:
        ctx = cls.build_context(apt)
        return render_notification_template("APPOINTMENT_REMINDER", ctx)

    @classmethod
    def send_appointment_notification(
        cls, db: Session, appointment: Appointment, event_type: str = "BOOKING", language: Optional[Language] = None
    ) -> Optional[SMSNotification]:
        """
        Create SMSNotification DB record and dispatch.
        RULE: Any exception here is caught so SMS failures NEVER corrupt or roll back the appointment.
        """
        try:
            recipient_phone = "+91-9999999999"
            user_id = None
            if appointment.patient and appointment.patient.user:
                recipient_phone = appointment.patient.user.phone_number
                user_id = appointment.patient.user.id

            norm_phone = normalize_phone_number(recipient_phone)
            lang = language or Language.HI

            ctx = cls.build_context(appointment, lang=lang)

            evt_upper = event_type.upper()
            if evt_upper == "CANCELLATION":
                msg_text = render_notification_template("APPOINTMENT_CANCELLED", ctx)
            elif evt_upper == "RESCHEDULE":
                msg_text = render_notification_template("APPOINTMENT_RESCHEDULED", ctx)
            elif evt_upper == "REMINDER":
                msg_text = render_notification_template("APPOINTMENT_REMINDER", ctx)
            elif evt_upper in ["CHECKIN", "CHECK_IN", "APPOINTMENT_CHECKIN"]:
                msg_text = render_notification_template("APPOINTMENT_CHECKIN", ctx)
            else:
                msg_text = render_notification_template("APPOINTMENT_CONFIRMED", ctx)

            sms_record = SMSNotification(
                user_id=user_id,
                appointment_id=appointment.id,
                phone_number=norm_phone,
                message=msg_text,
                language=lang,
                event_type=evt_upper,
                status=NotificationStatus.QUEUED,
                provider="DEV_CONSOLE",
                attempt_count=1,
                last_attempt_at=datetime.utcnow()
            )
            db.add(sms_record)
            db.commit()
            db.refresh(sms_record)

            # Update status to SENDING
            sms_record.status = NotificationStatus.SENDING
            db.commit()

            # Dispatch via custom provider if overridden, or via factory provider
            if type(cls.provider) != ConsoleSMSProvider:
                success, provider_msg_id, fail_reason = cls.provider.send_sms(norm_phone, msg_text)
                if success:
                    sms_record.status = NotificationStatus.SENT
                    sms_record.provider_message_id = provider_msg_id
                    sms_record.sent_at = datetime.utcnow()
                    sms_record.failure_reason = None
                else:
                    sms_record.status = NotificationStatus.FAILED
                    sms_record.failure_reason = fail_reason or "Provider dispatch failed"
            else:
                try:
                    from app.integrations.sms.factory import get_sms_provider
                    from app.integrations.sms.models import SMSRequest
                    provider_inst = get_sms_provider()
                    req = SMSRequest(to_number=norm_phone, message=msg_text, event_type=evt_upper)

                    # Execute provider send
                    if asyncio.iscoroutinefunction(provider_inst.send_sms):
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Running inside active loop
                                res = asyncio.run_coroutine_threadsafe(provider_inst.send_sms(req), loop).result(timeout=5)
                            else:
                                res = loop.run_until_complete(provider_inst.send_sms(req))
                        except Exception:
                            res = asyncio.run(provider_inst.send_sms(req))
                    else:
                        res = provider_inst.send_sms(req)

                    if res.status.value in ["SENT", "SENT_SIMULATED"]:
                        sms_record.status = NotificationStatus.SENT
                        sms_record.provider_message_id = res.provider_message_id
                        sms_record.provider = res.provider
                        sms_record.sent_at = datetime.utcnow()
                        sms_record.failure_reason = None
                    elif res.status.value == "DELIVERED":
                        sms_record.status = NotificationStatus.DELIVERED
                        sms_record.provider_message_id = res.provider_message_id
                        sms_record.provider = res.provider
                        sms_record.sent_at = datetime.utcnow()
                        sms_record.delivered_at = datetime.utcnow()
                        sms_record.failure_reason = None
                    else:
                        sms_record.status = NotificationStatus.FAILED
                        sms_record.failure_reason = res.error_message or "Provider dispatch failed"
                except Exception as pe:
                    # Fallback to default class provider
                    success, provider_msg_id, fail_reason = cls.provider.send_sms(norm_phone, msg_text)
                    if success:
                        sms_record.status = NotificationStatus.SENT
                        sms_record.provider_message_id = provider_msg_id
                        sms_record.sent_at = datetime.utcnow()
                        sms_record.failure_reason = None
                    else:
                        sms_record.status = NotificationStatus.FAILED
                        sms_record.failure_reason = fail_reason or str(pe)
                    sms_record.status = NotificationStatus.FAILED
                    sms_record.failure_reason = fail_reason or str(pe)

            db.commit()
            db.refresh(sms_record)
            return sms_record

        except Exception as e:
            logger.error(f"Failed to queue/send notification for appointment {appointment.id}: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None

    @classmethod
    def send_appointment_reminder(cls, db: Session, appointment_id: int) -> Optional[SMSNotification]:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt or apt.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW]:
            return None

        # Idempotency check: Do not resend if reminder_sent_at is set or active REMINDER notification exists
        if apt.reminder_sent_at is not None:
            return db.query(SMSNotification).filter(
                SMSNotification.appointment_id == appointment_id,
                SMSNotification.event_type == "REMINDER"
            ).order_by(SMSNotification.id.desc()).first()

        existing_rem = db.query(SMSNotification).filter(
            SMSNotification.appointment_id == appointment_id,
            SMSNotification.event_type == "REMINDER",
            SMSNotification.status.in_([NotificationStatus.QUEUED, NotificationStatus.SENDING, NotificationStatus.SENT, NotificationStatus.DELIVERED])
        ).first()

        if existing_rem:
            apt.reminder_sent_at = existing_rem.created_at
            db.commit()
            return existing_rem

        # Set idempotency marker
        apt.reminder_sent_at = datetime.utcnow()
        db.commit()

        return cls.send_appointment_notification(db, apt, event_type="REMINDER")

    @classmethod
    def process_daily_reminders(cls, db: Session, hours_ahead: int = 24) -> List[SMSNotification]:
        """
        Finds appointments scheduled within the next 24-hour window (Asia/Kolkata date) and dispatches reminders idempotently.
        """
        today_ist = get_today_ist()
        target_date = today_ist + timedelta(days=1)

        eligible_apts = db.query(Appointment).filter(
            Appointment.appointment_date == target_date,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED, AppointmentStatus.PENDING]),
            Appointment.reminder_sent_at.is_(None)
        ).all()

        reminders: List[SMSNotification] = []
        for apt in eligible_apts:
            res = cls.send_appointment_reminder(db, apt.id)
            if res:
                reminders.append(res)

        return reminders

    @classmethod
    def retry_failed_sms(cls, db: Session, sms_id: Optional[int] = None, max_attempts: int = 3) -> List[SMSNotification]:
        """
        Retries failed notifications. Ensures idempotency: SENT or DELIVERED messages are never retried.
        """
        if sms_id:
            targets = db.query(SMSNotification).filter(
                SMSNotification.id == sms_id,
                SMSNotification.status == NotificationStatus.FAILED,
                SMSNotification.attempt_count < max_attempts
            ).all()
        else:
            targets = db.query(SMSNotification).filter(
                SMSNotification.status == NotificationStatus.FAILED,
                SMSNotification.attempt_count < max_attempts
            ).all()

        results: List[SMSNotification] = []
        for sms in targets:
            # Idempotency safety check
            if sms.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]:
                results.append(sms)
                continue

            sms.attempt_count += 1
            sms.last_attempt_at = datetime.utcnow()
            sms.status = NotificationStatus.RETRYING
            db.commit()

            try:
                from app.integrations.sms.factory import get_sms_provider
                from app.integrations.sms.models import SMSRequest
                provider_inst = get_sms_provider()
                req = SMSRequest(to_number=sms.phone_number, message=sms.message, event_type=sms.event_type or "NOTIFICATION")

                if asyncio.iscoroutinefunction(provider_inst.send_sms):
                    try:
                        res = asyncio.run(provider_inst.send_sms(req))
                    except Exception:
                        success, provider_msg_id, fail_reason = cls.provider.send_sms(sms.phone_number, sms.message)
                        res = type('SMSResult', (), {'status': type('Status', (), {'value': 'SENT' if success else 'FAILED'})(), 'provider_message_id': provider_msg_id, 'provider': 'development', 'error_message': fail_reason})()
                else:
                    res = provider_inst.send_sms(req)

                if res.status.value in ["SENT", "SENT_SIMULATED"]:
                    sms.status = NotificationStatus.SENT
                    sms.provider_message_id = getattr(res, "provider_message_id", f"DEV-SMS-{uuid.uuid4().hex[:8]}")
                    sms.sent_at = datetime.utcnow()
                    sms.failure_reason = None
                elif res.status.value == "DELIVERED":
                    sms.status = NotificationStatus.DELIVERED
                    sms.provider_message_id = getattr(res, "provider_message_id", f"DEV-SMS-{uuid.uuid4().hex[:8]}")
                    sms.sent_at = datetime.utcnow()
                    sms.delivered_at = datetime.utcnow()
                    sms.failure_reason = None
                else:
                    sms.status = NotificationStatus.FAILED
                    sms.failure_reason = getattr(res, "error_message", None) or f"Retry failed (attempt {sms.attempt_count}/{max_attempts})"
            except Exception as e:
                sms.status = NotificationStatus.FAILED
                sms.failure_reason = f"Retry attempt {sms.attempt_count} failed: {e}"

            db.commit()
            db.refresh(sms)
            results.append(sms)

        return results
