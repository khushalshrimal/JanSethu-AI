from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    environment: Optional[str] = "development"
    telephony: Optional[str] = "mock"
    stt: Optional[str] = "mock"
    tts: Optional[str] = "mock"
    sms: Optional[str] = "mock"
    location: Optional[str] = "mock"
    llm: Optional[str] = "development"
