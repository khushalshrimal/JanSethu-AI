from app.core.config import settings
from app.integrations.sms.base import SMSProvider
from app.integrations.sms.development_provider import DevelopmentSMSProvider
from app.integrations.sms.msg91_provider import MSG91SMSProvider

_sms_provider_instance = None

def get_sms_provider(override_name: str = None) -> SMSProvider:
    global _sms_provider_instance
    provider_name = (override_name or getattr(settings, "SMS_PROVIDER", "development")).lower()
    
    if override_name is None and _sms_provider_instance is not None:
        return _sms_provider_instance

    if provider_name == "msg91":
        instance = MSG91SMSProvider()
    else:
        instance = DevelopmentSMSProvider()

    if override_name is None:
        _sms_provider_instance = instance
    return instance

