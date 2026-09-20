from abc import ABC, abstractmethod
from typing import Optional
from app.integrations.sms.models import SMSRequest, SMSResult, SMSDeliveryStatus

class SMSProvider(ABC):
    @abstractmethod
    async def send_sms(self, req: SMSRequest) -> SMSResult:
        """Send an SMS message."""
        pass

    @abstractmethod
    async def get_delivery_status(self, provider_message_id: str) -> SMSDeliveryStatus:
        """Query SMS delivery status."""
        pass
