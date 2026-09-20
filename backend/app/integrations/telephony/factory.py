from app.core.config import settings
from app.integrations.telephony.base import TelephonyProvider
from app.integrations.telephony.development_provider import DevelopmentTelephonyProvider
from app.integrations.telephony.exotel_provider import ExotelTelephonyProvider

_telephony_provider_instance = None

def get_telephony_provider(override_name: str = None) -> TelephonyProvider:
    global _telephony_provider_instance
    provider_name = (override_name or getattr(settings, "TELEPHONY_PROVIDER", "development")).lower()
    
    if override_name is None and _telephony_provider_instance is not None:
        return _telephony_provider_instance

    if provider_name == "exotel":
        instance = ExotelTelephonyProvider()
    else:
        instance = DevelopmentTelephonyProvider()

    if override_name is None:
        _telephony_provider_instance = instance
    return instance

