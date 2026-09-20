# JanSethu AI 2.0 — Rural & Underserved Healthcare Access Platform

**JanSethu AI 2.0** is a voice-first healthcare access platform designed for rural and underserved communities in India. It bridges the digital and linguistic divide by providing:

1. **Phone Channel (IVR)**: Natural language voice interaction & DTMF keypad fallback over telephone lines (Hindi, Marathi, English) with provider-neutral telephony integration.
2. **Smartphone PWA**: Modern responsive web application for facility search, doctor OPD availability, appointment queue tracking, provider management, and admin operations.

Both channels converge on a single, shared, database-backed FastAPI engine with JWT authentication, role-based access control, dynamic slot generation, and double-booking protection.

---

## 🔍 Core Platform Architecture & Capabilities

- **Provider-Neutral Telephony & SMS**: Abstract base classes `TelephonyProvider` and `SMSProvider` supporting cloud providers (Twilio/Exotel) and `DevelopmentTelephonyProvider` / `DevelopmentSMSProvider` for local testing without paid API accounts.
- **Facility Discovery & Dynamic Slot Engine**: Haversine distance search, discrete 30-min OPD slot generation from doctor recurring schedules and schedule exceptions.
- **Voice & Multilingual NLU Engine**: Multilingual prompt system (Hindi `HI`, Marathi `MR`, English `EN`) with Voice & DTMF fallback.
- **Provider OPD Console**: Real-time queue metrics, consultation state machine (`BOOKED` -> `IN_PROGRESS` -> `COMPLETED` / `NO_SHOW` / `CANCELLED`), and doctor leave exception creation.
- **Admin Operations Console**: Onboard facilities/doctors, manage emergency service directory, monitor audit trails, and inspect live telephony sessions and SMS logs.

---

## 🚀 Quick Start Instructions

### 1. Database Setup & Seeding

```bash
cd backend

# Run Alembic migrations
python -c "from alembic.config import main; main()" upgrade head

# Seed demo data (Facilities, Doctors, Schedules, Exceptions & Appointments)
python scripts/seed.py
```

### 2. Start FastAPI Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- **Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Interactive OpenAPI Specs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Telephony Webhooks**: `POST http://localhost:8000/api/v1/telephony/webhooks/incoming`

### 3. Start Frontend App

```bash
cd frontend
npm run dev
```

- **Customer PWA**: [http://localhost:5173](http://localhost:5173)
- **Feature Phone Simulator**: [http://localhost:5173/phone-simulator](http://localhost:5173/phone-simulator)
- **Provider Console**: [http://localhost:5173/provider](http://localhost:5173/provider)
- **Admin Console**: [http://localhost:5173/admin](http://localhost:5173/admin)

---

## 📚 SIH Grand Finale Documentation & Presenter Resources

- 📜 **Presenter Script**: [docs/SIH_DEMO_SCRIPT.md](file:///c:/Users/khush/OneDrive/Desktop/JanSethu%20AI/docs/SIH_DEMO_SCRIPT.md) — Step-by-step 2-3 minute demo timeline and voice/DTMF backup flows.
- 📹 **Video Recording Checklist**: [docs/SIH_VIDEO_RECORDING_CHECKLIST.md](file:///c:/Users/khush/OneDrive/Desktop/JanSethu%20AI/docs/SIH_VIDEO_RECORDING_CHECKLIST.md) — Pre-recording setup and video rules.
- 🏗️ **Platform Architecture**: [docs/SIH_ARCHITECTURE.md](file:///c:/Users/khush/OneDrive/Desktop/JanSethu%20AI/docs/SIH_ARCHITECTURE.md) — Unified backend architecture diagram and domain model.
- 📋 **Claims Verification Matrix**: [docs/SIH_CLAIMS_VERIFICATION.md](file:///c:/Users/khush/OneDrive/Desktop/JanSethu%20AI/docs/SIH_CLAIMS_VERIFICATION.md) — Technical evidence matrix for presentation claims.

---

## 🧪 Running Automated Tests

```bash
cd backend
py -m pytest app/tests/ -v
```
- **Total Tests**: **91/91 (100%) passing**



