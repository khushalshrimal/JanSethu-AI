# JanSethu AI — Production Configuration & Security Specification

This reference manual documents environment variables, provider abstractions, security policies, and production safeguards for JanSethu AI.

---

## 1. Environment Variable Reference

| Variable | Mode | Default | Description |
|---|---|---|---|
| `APP_ENV` | All | `development` | Environment mode (`development`, `staging`, `production`) |
| `DEBUG` | All | `true` (dev) / `false` (prod) | FastAPI debug mode flag |
| `SECRET_KEY` | Production | *Required in Prod* | JWT token signing key (64+ chars) |
| `DATABASE_URL` | All | `sqlite:///./jansethu_v2.db` | SQLAlchemy DB URI (`sqlite:///...` or `postgresql://...`) |
| `CORS_ORIGINS` | All | `http://localhost:5173...` | Comma-separated trusted CORS origins |
| `TELEPHONY_PROVIDER` | Optional | `development` | Telephony backend (`development`, `twilio`, `exotel`, `vonage`) |
| `STT_PROVIDER` | Optional | `mock` | Speech-to-Text backend (`mock`, `local`, `whisper`) |
| `TTS_PROVIDER` | Optional | `mock` | Text-to-Speech backend (`mock`, `local`, `gtts`) |
| `SMS_PROVIDER` | Optional | `development` | SMS gateway (`development`, `msg91`, `twilio`) |
| `LOCATION_PROVIDER` | Optional | `mock` | Geocoding service (`mock`, `configured`) |
| `LLM_PROVIDER` | Optional | `development` | LLM parser (`development`, `openai`, `ollama`) |

---

## 2. Provider Abstraction Architecture

JanSethu AI uses factory functions to instantiate integration adapters dynamically. When external credentials are missing or unconfigured, factory functions automatically return fallback zero-cost local/mock instances.

### Provider Factory Mapping

```
TELEPHONY_PROVIDER ──► get_telephony_provider() ──► DevelopmentTelephonyProvider (fallback)
                                                 ──► TwilioTelephonyProvider
                                                 ──► ExotelTelephonyProvider
                                                 ──► VonageTelephonyProvider

SMS_PROVIDER       ──► get_sms_provider()       ──► DevelopmentSMSProvider (fallback)
                                                 ──► MSG91SMSProvider
                                                 ──► TwilioSMSProvider

STT_PROVIDER       ──► get_speech_provider()    ──► LocalSpeechInputProvider (fallback)
                                                 ──► ConfiguredSpeechInputProvider

TTS_PROVIDER       ──► get_tts_provider()       ──► LocalTTSProvider (fallback)
                                                 ──► ConfiguredTTSProvider

LOCATION_PROVIDER  ──► get_location_provider()  ──► MockLocationProvider (fallback)
                                                 ──► ConfiguredLocationProvider
```

---

## 3. Security Safeguards

1. **Secret Isolation**: Secrets are loaded exclusively from `.env` or system environment. No API keys or passwords are committed to source code.
2. **Medical Log Sanitization**: Full medical conversation transcripts are not stored in raw application logs.
3. **CORS Enforcement**: In production (`APP_ENV=production`), wildcards (`*`) are disallowed; exact origin whitelist is enforced.
4. **Atomic Concurrency Protection**: OPD appointment slot bookings re-check slot availability inside the database transaction block prior to committing to prevent double-booking under high load.
5. **Emergency & SMS Labelling**: When running without live SMS/ambulance gateways, all outbound alerts are explicitly labeled as `DEMO / SIMULATED`.
