from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    environment: Optional[str] = "development"
