import os
from typing import List
from pydantic import BaseModel

# Load environment variables from backend/.env file if present
_env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
if os.path.exists(_env_file):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k, _v = _k.strip(), _v.strip().strip('"').strip("'")
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "JanSethu AI 2.0")
    VERSION: str = os.getenv("VERSION", "2.0.0")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    APP_ENV: str = os.getenv("APP_ENV", "development").lower()
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1") if os.getenv("APP_ENV", "development").lower() != "production" else False
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jansethu_ai_2_super_secret_key_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jansethu_v2.db")
    
    # Domain & Callback Base URL
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    
    # CORS Security
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
        ).split(",") if origin.strip()
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Webhook Security
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "development-secret-key-2026")
    
    # Telephony & SMS Providers
    TELEPHONY_PROVIDER: str = os.getenv("TELEPHONY_PROVIDER", "development").lower()
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "development").lower()
    
    # Twilio Credentials
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    MOCK_TELEPHONY_MODE: bool = os.getenv("MOCK_TELEPHONY_MODE", "True").lower() in ("true", "1")
    
    # Exotel Credentials (India Telephony Staging)
    EXOTEL_ACCOUNT_SID: str = os.getenv("EXOTEL_ACCOUNT_SID", "")
    EXOTEL_API_KEY: str = os.getenv("EXOTEL_API_KEY", "")
    EXOTEL_API_TOKEN: str = os.getenv("EXOTEL_API_TOKEN", "")
    EXOTEL_SUBDOMAIN: str = os.getenv("EXOTEL_SUBDOMAIN", "api.exotel.com")
    EXOTEL_CALLER_ID: str = os.getenv("EXOTEL_CALLER_ID", "")
    
    # MSG91 Credentials (India SMS Staging)
    MSG91_AUTH_KEY: str = os.getenv("MSG91_AUTH_KEY", "")
    MSG91_SENDER_ID: str = os.getenv("MSG91_SENDER_ID", "JANSTH")
    MSG91_TEMPLATE_ID: str = os.getenv("MSG91_TEMPLATE_ID", "")

    # LLM / NLU Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "development").lower()
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")

    # STT & TTS Providers
    STT_PROVIDER: str = os.getenv("STT_PROVIDER", "mock").lower()
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "mock").lower()
    
    # Location Provider
    LOCATION_PROVIDER: str = os.getenv("LOCATION_PROVIDER", "mock").lower()
    LOCATION_API_KEY: str = os.getenv("LOCATION_API_KEY", "")

    # Vonage Credentials
    VONAGE_API_KEY: str = os.getenv("VONAGE_API_KEY", "")
    VONAGE_API_SECRET: str = os.getenv("VONAGE_API_SECRET", "")
    VONAGE_PHONE_NUMBER: str = os.getenv("VONAGE_PHONE_NUMBER", "")

settings = Settings()
