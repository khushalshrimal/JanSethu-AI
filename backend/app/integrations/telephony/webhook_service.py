import hmac
import hashlib
from typing import Dict, Any, Optional, Set
from fastapi import HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.telephony import CallSession
from app.core.prompts import VoicePromptProvider
from app.services.phone_session_service import PhoneSessionService
from app.utils.phone_normalizer import normalize_phone_number
from app.models.audit import AuditLog

class WebhookVerifier:
    """
    Security verifier for external telephony & SMS webhooks.
    Validates signature / secret header to prevent unauthorized HTTP POST requests.
    """
    @staticmethod
    def verify_webhook_secret(
        secret_header: Optional[str] = Header(None, alias="X-Webhook-Secret"),
        expected_secret: Optional[str] = None
    ):
        target_secret = expected_secret or getattr(settings, "WEBHOOK_SECRET", "development-secret-key-2026")
        if not secret_header or secret_header != target_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing webhook authorization secret."
            )
        return True


class TelephonyWebhookService:
    """
    Provider-neutral webhook orchestration and idempotency service.
    """
    _processed_event_ids: Set[str] = set()

    @classmethod
    def is_duplicate_event(cls, provider_event_id: str) -> bool:
        if not provider_event_id:
            return False
        if provider_event_id in cls._processed_event_ids:
            return True
        cls._processed_event_ids.add(provider_event_id)
        return False

    @classmethod
    def process_incoming_call_webhook(
        cls,
        db: Session,
        from_number: str,
        to_number: str,
        provider: str = "development",
        provider_call_id: Optional[str] = None,
        provider_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if provider_event_id and cls.is_duplicate_event(provider_event_id):
            return {
                "status": "ALREADY_PROCESSED",
                "message": f"Duplicate event '{provider_event_id}' safely ignored."
            }

        norm_from = normalize_phone_number(from_number)
        norm_to = normalize_phone_number(to_number)

        session = PhoneSessionService.start_session(
            db=db,
            phone_number=norm_from,
            channel="IVR",
            provider=provider,
            provider_call_id=provider_call_id
        )

        audit = AuditLog(
            user_id=None,
            action="TELEPHONY_CALL_STARTED",
            entity_type="CallSession",
            entity_id=session.id,
            metadata_json={"caller": norm_from, "provider_call_id": session.provider_call_id}
        )
        db.add(audit)
        db.commit()

        greeting_text = VoicePromptProvider.get_prompt("GREETING", session.language)
        return {
            "call_session_id": session.id,
            "provider_call_id": session.provider_call_id,
            "prompt_text": greeting_text,
            "state": session.current_state,
            "language": session.language.value if hasattr(session.language, "value") else str(session.language)
        }

    @classmethod
    def process_dtmf_webhook(
        cls,
        db: Session,
        provider_call_id: str,
        digits: str,
        provider_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if provider_event_id and cls.is_duplicate_event(provider_event_id):
            return {
                "status": "ALREADY_PROCESSED",
                "message": f"Duplicate DTMF event '{provider_event_id}' safely ignored."
            }

        session = db.query(CallSession).filter(CallSession.provider_call_id == provider_call_id).first()
        if not session:
            session = db.query(CallSession).filter(CallSession.status == "ACTIVE").order_by(CallSession.id.desc()).first()

        if not session:
            raise HTTPException(status_code=404, detail="Active call session not found for provider call ID.")

        dtmf_resp = PhoneSessionService.process_dtmf_input(db=db, session_id=session.id, key=digits)
        return {
            "call_session_id": session.id,
            "provider_call_id": session.provider_call_id,
            "prompt": dtmf_resp.prompt_text,
            "state": dtmf_resp.current_state,
            "language": dtmf_resp.language.value if hasattr(dtmf_resp.language, "value") else str(dtmf_resp.language)
        }

    @classmethod
    async def process_voice_webhook(
        cls,
        db: Session,
        provider_call_id: str,
        speech_text: str,
        language: Optional[str] = None,
        provider_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if provider_event_id and cls.is_duplicate_event(provider_event_id):
            return {
                "status": "ALREADY_PROCESSED",
                "message": f"Duplicate voice event '{provider_event_id}' safely ignored."
            }

        session = db.query(CallSession).filter(CallSession.provider_call_id == provider_call_id).first()
        if not session:
            session = db.query(CallSession).filter(CallSession.status == "ACTIVE").order_by(CallSession.id.desc()).first()

        if not session:
            raise HTTPException(status_code=404, detail="Active call session not found for provider call ID.")

        session_resp, nlu_result = await PhoneSessionService.process_voice_input(
            db=db,
            session_id=session.id,
            utterance_or_audio=speech_text,
            language_hint=language
        )
        return {
            "call_session_id": session.id,
            "provider_call_id": session.provider_call_id,
            "prompt": session_resp.prompt_text,
            "state": session_resp.current_state,
            "nlu": {
                "intent": nlu_result.intent.value,
                "raw_text": nlu_result.raw_text,
                "entities": nlu_result.entities
            }
        }
