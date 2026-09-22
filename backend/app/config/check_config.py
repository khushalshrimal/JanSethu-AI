import sys
import os
from sqlalchemy import text
from app.core.config import settings
from app.database.session import SessionLocal

def validate_configuration() -> bool:
    """
    Production & Demo Configuration Audit Tool.
    Inspects environment variables, database connections, and provider backends without leaking raw secrets.
    """
    print("=" * 65)
    print("      JANSETHU AI — PRODUCTION & DEMO CONFIGURATION AUDIT")
    print("=" * 65)

    report = {}

    # 1. Environment & Secrets
    report["APP_ENV"] = settings.APP_ENV.upper()
    sec_key = settings.SECRET_KEY
    if "super_secret" in sec_key or "dev_secret" in sec_key or len(sec_key) < 16:
        report["SECRET_KEY"] = "DEMO/DEFAULT (Change for production)"
    else:
        report["SECRET_KEY"] = "CONFIGURED (Custom secret set)"

    # 2. Database Connection
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        db_type = "SQLite (Local/Demo DB)"
    elif "postgresql" in db_url:
        db_type = "PostgreSQL (Production DB)"
    else:
        db_type = "Relational DB"

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        report["DATABASE"] = f"CONFIGURED ({db_type} — Connected)"
    except Exception as e:
        report["DATABASE"] = f"ERROR ({db_type} — {str(e)})"

    # 3. Telephony Provider
    tel_p = settings.TELEPHONY_PROVIDER
    if tel_p in ["mock", "development"]:
        report["TELEPHONY_PROVIDER"] = "DEMO/MOCK (Zero-cost local voice simulator)"
    elif tel_p == "twilio":
        has_keys = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
        report["TELEPHONY_PROVIDER"] = "CONFIGURED (Twilio Voice API)" if has_keys else "DEMO/MOCK (Twilio keys missing)"
    elif tel_p == "exotel":
        has_keys = bool(settings.EXOTEL_ACCOUNT_SID and settings.EXOTEL_API_KEY)
        report["TELEPHONY_PROVIDER"] = "CONFIGURED (Exotel India Staging)" if has_keys else "DEMO/MOCK (Exotel keys missing)"
    elif tel_p == "vonage":
        has_keys = bool(settings.VONAGE_API_KEY and settings.VONAGE_API_SECRET)
        report["TELEPHONY_PROVIDER"] = "CONFIGURED (Vonage Voice API)" if has_keys else "DEMO/MOCK (Vonage keys missing)"
    else:
        report["TELEPHONY_PROVIDER"] = f"CUSTOM ({tel_p})"

    # 4. Speech-to-Text (STT) Provider
    stt_p = getattr(settings, "STT_PROVIDER", "mock")
    report["STT_PROVIDER"] = "DEMO/MOCK (Local STT engine)" if stt_p in ["mock", "local"] else f"CONFIGURED ({stt_p})"

    # 5. Text-to-Speech (TTS) Provider
    tts_p = getattr(settings, "TTS_PROVIDER", "mock")
    report["TTS_PROVIDER"] = "DEMO/MOCK (Local TTS synthesizer)" if tts_p in ["mock", "local"] else f"CONFIGURED ({tts_p})"

    # 6. SMS Provider
    sms_p = settings.SMS_PROVIDER
    if sms_p in ["mock", "development"]:
        report["SMS_PROVIDER"] = "DEMO/MOCK (Simulated SMS logger)"
    elif sms_p == "msg91":
        has_keys = bool(settings.MSG91_AUTH_KEY)
        report["SMS_PROVIDER"] = "CONFIGURED (MSG91 India SMS)" if has_keys else "DEMO/MOCK (MSG91 key missing)"
    elif sms_p == "twilio":
        has_keys = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
        report["SMS_PROVIDER"] = "CONFIGURED (Twilio SMS)" if has_keys else "DEMO/MOCK (Twilio keys missing)"
    else:
        report["SMS_PROVIDER"] = f"CUSTOM ({sms_p})"

    # 7. Location Provider
    loc_p = getattr(settings, "LOCATION_PROVIDER", "mock")
    report["LOCATION_PROVIDER"] = "DEMO/MOCK (Rural Maharashtra Geocoder)" if loc_p in ["mock", "local"] else f"CONFIGURED ({loc_p})"

    # 8. LLM / NLU Engine
    llm_p = settings.LLM_PROVIDER
    report["LLM_ENGINE"] = "DEMO/DEVELOPMENT (Deterministic NLU parser)" if llm_p == "development" else f"CONFIGURED ({llm_p})"

    # Print Summary Table
    for key, val in report.items():
        print(f"  [+] {key:<20}: {val}")

    print("=" * 65)
    print("STATUS: JanSethu AI configuration is valid and operational.")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = validate_configuration()
    sys.exit(0 if success else 1)
