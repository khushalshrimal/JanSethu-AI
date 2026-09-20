from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Header, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.models.telephony import CallSession
from app.models.audit import AuditLog
from app.api.deps import require_roles
from app.integrations.telephony.factory import get_telephony_provider
from app.integrations.telephony.webhook_service import TelephonyWebhookService, WebhookVerifier
from app.integrations.sms.webhook_service import SMSWebhookService
from app.utils.phone_normalizer import normalize_phone_number

router = APIRouter()

class DevIncomingCallRequest(BaseModel):
    from_number: str
    to_number: Optional[str] = "+911234567890"

class ProviderIncomingWebhookRequest(BaseModel):
    provider: str = "development"
    provider_call_id: Optional[str] = None
    from_number: str
    to_number: str = "+911234567890"
    provider_event_id: Optional[str] = None

class ProviderDTMFWebhookRequest(BaseModel):
    provider_call_id: str
    digits: str
    provider_event_id: Optional[str] = None

class ProviderVoiceWebhookRequest(BaseModel):
    provider_call_id: str
    text: str
    language: Optional[str] = "hi"
    provider_event_id: Optional[str] = None

class ProviderSMSStatusRequest(BaseModel):
    provider_message_id: str
    status: str
    error_message: Optional[str] = None
    provider_event_id: Optional[str] = None

class OutboundCallRequest(BaseModel):
    to_number: str
    appointment_id: Optional[int] = None

# --- SIMULATED DEVELOPMENT ENDPOINTS ---

@router.post("/dev/incoming-call")
async def simulate_incoming_call(
    req: DevIncomingCallRequest,
    db: Session = Depends(get_db)
):
    """
    Development simulator endpoint to start a simulated inbound telephony call session.
    """
    provider = get_telephony_provider()
    incoming_call = await provider.start_call(
        from_number=req.from_number,
        to_number=req.to_number or "+911234567890"
    )

    res = TelephonyWebhookService.process_incoming_call_webhook(
        db=db,
        from_number=incoming_call.from_number,
        to_number=incoming_call.to_number,
        provider="development",
        provider_call_id=incoming_call.provider_call_id
    )
    return res

# --- PROVIDER WEBHOOK ENDPOINTS ---

@router.post("/webhooks/incoming")
async def webhook_incoming_call(
    req: ProviderIncomingWebhookRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Provider-neutral incoming call webhook.
    Validates secret header, checks event idempotency, links/creates CallSession, and returns prompts.
    """
    WebhookVerifier.verify_webhook_secret(secret_header=x_webhook_secret)

    return TelephonyWebhookService.process_incoming_call_webhook(
        db=db,
        from_number=req.from_number,
        to_number=req.to_number,
        provider=req.provider,
        provider_call_id=req.provider_call_id,
        provider_event_id=req.provider_event_id
    )

@router.post("/webhooks/dtmf")
async def webhook_dtmf_input(
    req: ProviderDTMFWebhookRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Provider-neutral DTMF keypad input webhook.
    """
    WebhookVerifier.verify_webhook_secret(secret_header=x_webhook_secret)

    return TelephonyWebhookService.process_dtmf_webhook(
        db=db,
        provider_call_id=req.provider_call_id,
        digits=req.digits,
        provider_event_id=req.provider_event_id
    )

@router.post("/webhooks/voice")
async def webhook_voice_input(
    req: ProviderVoiceWebhookRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Provider-neutral voice utterance webhook (routes to VoiceUnderstandingService).
    """
    WebhookVerifier.verify_webhook_secret(secret_header=x_webhook_secret)

    return await TelephonyWebhookService.process_voice_webhook(
        db=db,
        provider_call_id=req.provider_call_id,
        speech_text=req.text,
        language=req.language,
        provider_event_id=req.provider_event_id
    )

@router.post("/webhooks/outbound")
async def initiate_outbound_call(
    req: OutboundCallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PROVIDER))
):
    """
    Initiate a simulated outbound call session (e.g. appointment reminder).
    """
    provider = get_telephony_provider()
    call = await provider.initiate_outbound_call(
        to_number=req.to_number,
        callback_url="/api/v1/telephony/webhooks/incoming",
        metadata={"appointment_id": req.appointment_id}
    )
    return {
        "provider": call.provider,
        "provider_call_id": call.provider_call_id,
        "to_number": call.to_number,
        "direction": call.direction,
        "status": call.status,
        "simulated": True
    }

@router.post("/webhooks/status")
@router.post("/webhooks/sms-status")
@router.post("/sms/status")
@router.post("/status")
async def sms_status_webhook(
    req: ProviderSMSStatusRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    SMS delivery status callback webhook. Updates SMSNotification record without blocking appointments.
    """
    WebhookVerifier.verify_webhook_secret(secret_header=x_webhook_secret)

    return SMSWebhookService.process_status_callback(
        db=db,
        provider_message_id=req.provider_message_id,
        status_str=req.status,
        error_message=req.error_message,
        provider_event_id=req.provider_event_id
    )

# --- EXOTEL EXOML REAL STAGING WEBHOOK ENDPOINTS ---

@router.post("/webhooks/exotel/incoming")
async def exotel_incoming_call(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exotel Incoming Call Webhook (Returns ExoML text/xml response).
    Exotel sends form-urlencoded data: CallSid, From, To, CallFrom, CallTo.
    """
    from fastapi.responses import Response
    from app.integrations.telephony.exotel_provider import ExotelTelephonyProvider
    from app.integrations.telephony.models import CallControlAction
    
    try:
        form_data = await request.form()
        payload = dict(form_data)
    except Exception:
        payload = dict(request.query_params)
    
    exotel_provider = ExotelTelephonyProvider()
    incoming = exotel_provider.parse_incoming_call(payload)
    
    res_dict = TelephonyWebhookService.process_incoming_call_webhook(
        db=db,
        from_number=incoming.from_number,
        to_number=incoming.to_number,
        provider="exotel",
        provider_call_id=incoming.provider_call_id
    )
    
    exoml_resp = exotel_provider.build_call_control_response(
        action=CallControlAction.COLLECT_DTMF,
        prompt_text=res_dict.get("prompt_text", "Welcome to JanSethu Healthcare."),
        gather_digits=True,
        num_digits=1
    )
    
    xml_str = exoml_resp.provider_payload.get("xml_response", "") if exoml_resp.provider_payload else ""
    return Response(content=xml_str, media_type="text/xml")

@router.post("/webhooks/exotel/dtmf")
async def exotel_dtmf_input(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exotel DTMF Keypress Callback Webhook (Returns ExoML text/xml response).
    Exotel sends form-urlencoded data: CallSid, Digits.
    """
    from fastapi.responses import Response
    from app.integrations.telephony.exotel_provider import ExotelTelephonyProvider
    from app.integrations.telephony.models import CallControlAction
    
    try:
        form_data = await request.form()
        payload = dict(form_data)
    except Exception:
        payload = dict(request.query_params)
    
    call_sid = payload.get("CallSid") or payload.get("call_id") or ""
    digits = payload.get("Digits") or payload.get("digits") or "1"
    
    exotel_provider = ExotelTelephonyProvider()
    
    res_dict = TelephonyWebhookService.process_dtmf_webhook(
        db=db,
        provider_call_id=call_sid,
        digits=digits
    )
    
    prompt = res_dict.get("prompt", "Thank you.")
    state = res_dict.get("state", "")
    
    action = CallControlAction.END_CALL if state in ["COMPLETED", "TERMINATED", "END"] else CallControlAction.COLLECT_DTMF
    
    exoml_resp = exotel_provider.build_call_control_response(
        action=action,
        prompt_text=prompt,
        gather_digits=(action != CallControlAction.END_CALL),
        num_digits=1
    )
    
    xml_str = exoml_resp.provider_payload.get("xml_response", "") if exoml_resp.provider_payload else ""
    return Response(content=xml_str, media_type="text/xml")

@router.post("/webhooks/msg91/status")
async def msg91_status_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    MSG91 Delivery Report Webhook callback.
    """
    from app.integrations.sms.msg91_provider import MSG91SMSProvider
    
    try:
        body = await request.json()
    except Exception:
        try:
            body = dict(await request.form())
        except Exception:
            body = dict(request.query_params)
    
    msg91_provider = MSG91SMSProvider()
    result = msg91_provider.parse_delivery_report(body)
    
    return SMSWebhookService.process_status_callback(
        db=db,
        provider_message_id=result.provider_message_id,
        status_str=result.status.value,
        error_message=result.error_message
    )



# --- ADMIN OPERATIONAL MONITORING ENDPOINTS ---

@router.get("/sessions")
def get_telephony_sessions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """
    Admin Telephony Operational View: Lists active and recent call sessions with masked numbers.
    """
    sessions = db.query(CallSession).order_by(CallSession.id.desc()).limit(limit).all()
    result = []
    for s in sessions:
        # Mask phone number for privacy
        phone = s.phone_number or ""
        masked_phone = f"{phone[:6]}****{phone[-2:]}" if len(phone) >= 10 else phone
        result.append({
            "id": s.id,
            "provider": s.provider,
            "provider_call_id": s.provider_call_id,
            "caller_phone_masked": masked_phone,
            "current_state": s.current_state,
            "is_active": (str(s.status) == "ACTIVE" or getattr(s.status, "value", str(s.status)) == "ACTIVE"),
            "language": s.language.value if hasattr(s.language, "value") else str(s.language),
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None
        })
    return result
