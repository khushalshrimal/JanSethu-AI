from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.models.enums import UserRole, Language
from app.schemas.user import UserResponse

class RegisterRequest(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    password: str
    preferred_language: Language = Language.HI
    village: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None

class LoginRequest(BaseModel):
    phone_number: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class CurrentUserResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None
    role: UserRole
    preferred_language: Language
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
