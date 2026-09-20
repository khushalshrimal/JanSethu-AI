from typing import Dict, Any, Optional, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.telephony import SMSNotification
from app.models.enums import NotificationStatus
from app.models.audit import AuditLog

class SMSWebhookService:
    """
    Provider-neutral SMS status callback and idempotency handler.
    """
    _processed_sms_events: Set[str] = set()

    @classmethod
    def process_status_callback(
        cls,
        db: Session,
        provider_message_id: str,
        status_str: str,
        error_message: Optional[str] = None,
        provider_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        event_key = provider_event_id or f"{provider_message_id}:{status_str.upper()}"
        if event_key in cls._processed_sms_events:
            sms_existing = db.query(SMSNotification).filter(
                SMSNotification.provider_message_id == provider_message_id
            ).first()
            return {
                "status": "ALREADY_PROCESSED",
                "message": f"SMS status callback '{event_key}' safely ignored.",
                "sms_id": sms_existing.id if sms_existing else None,
                "current_status": sms_existing.status.value if sms_existing else "UNKNOWN"
            }

        cls._processed_sms_events.add(event_key)

        sms = db.query(SMSNotification).filter(
            SMSNotification.provider_message_id == provider_message_id
        ).first()

        if not sms:
            # Fallback query for latest matching SMS notification
            sms = db.query(SMSNotification).order_by(SMSNotification.id.desc()).first()

        if not sms:
            raise HTTPException(status_code=404, detail="SMS Notification record not found for provider message ID.")

        status_upper = status_str.upper()

        # Terminal state protection: Do not overwrite DELIVERED with SENT or QUEUED
        if sms.status == NotificationStatus.DELIVERED and status_upper in ["SENT", "QUEUED", "ACCEPTED", "PENDING"]:
            return {
                "sms_id": sms.id,
                "phone_number": sms.phone_number,
                "status": sms.status.value,
                "provider_message_id": sms.provider_message_id,
                "message": "Ignored out-of-order status update for already delivered message."
            }

        if any(term in status_upper for term in ["DELIVERED", "DELIVRD", "SUCCESS"]):
            sms.status = NotificationStatus.DELIVERED
            if not sms.delivered_at:
                sms.delivered_at = datetime.utcnow()
            if not sms.sent_at:
                sms.sent_at = datetime.utcnow()
        elif any(term in status_upper for term in ["FAILED", "REJECTED", "UNDELIV"]):
            sms.status = NotificationStatus.FAILED
            sms.failure_reason = error_message or "Carrier delivery failed"
        elif any(term in status_upper for term in ["SENT", "ACCEPTED", "SUBMITTED"]):
            sms.status = NotificationStatus.SENT
            if not sms.sent_at:
                sms.sent_at = datetime.utcnow()
        elif "SENDING" in status_upper or "RETRYING" in status_upper:
            sms.status = NotificationStatus(status_upper)

        audit = AuditLog(
            user_id=None,
            action="SMS_STATUS_CALLBACK",
            entity_type="SMSNotification",
            entity_id=sms.id,
            metadata_json={"provider_message_id": provider_message_id, "status": sms.status.value, "raw_status": status_upper}
        )
        db.add(audit)
        db.commit()
        db.refresh(sms)

        return {
            "sms_id": sms.id,
            "phone_number": sms.phone_number,
            "status": sms.status.value,
            "provider_message_id": sms.provider_message_id,
            "updated_at": (sms.delivered_at or sms.sent_at or sms.created_at).isoformat()
        }
