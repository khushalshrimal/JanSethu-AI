from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class SMSDeliveryStatus(str, Enum):
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    SENT_SIMULATED = "SENT_SIMULATED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    REJECTED = "REJECTED"

class SMSRequest(BaseModel):
    to_number: str
    message: str
    event_type: str = "NOTIFICATION"
    metadata_json: Optional[Dict[str, Any]] = None

class SMSResult(BaseModel):
    provider: str = "development"
    provider_message_id: str
    status: SMSDeliveryStatus
    sent_at: datetime
    error_message: Optional[str] = None
    is_simulated: bool = False

    model_config = ConfigDict(from_attributes=True)
