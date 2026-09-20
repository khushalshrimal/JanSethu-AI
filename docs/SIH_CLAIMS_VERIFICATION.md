# JanSethu AI 2.0 — SIH Presentation Claims Verification Matrix

---

## 📌 Purpose
To prevent overclaiming during Smart India Hackathon (SIH) presentations and ensure all statements made in PPT slides, demonstration videos, and evaluator Q&A strictly match verified technical capabilities.

---

## 🔍 Claims Verification Matrix

| Presentation Claim | Technical Evidence | Current Verification Status | Statement Guidance for Presenter |
| :--- | :--- | :--- | :--- |
| **"Multilingual Voice Interaction"** | Natural Language Understanding pipeline (`VoiceUnderstandingService`), language detection, intent classification, entity extraction supporting Hindi (`HI`), Marathi (`MR`), English (`EN`). Automated tests in `test_phase13_demo.py` passing. | **VERIFIED ✓** | *"Supports Hindi, Marathi, and English voice and text interaction."* |
| **"Real Database Appointment Booking"** | FastAPI + SQLAlchemy + SQLite/PostgreSQL appointment domain model. Real slot generation, confirmation codes (`JS-2026-XXXX`), double-booking unique constraint. | **VERIFIED ✓** | *"Appointments are locked into a real database engine with double-booking constraint protection."* |
| **"Basic Phone / Keypad Compatibility"** | `CallSession` state machine, DTMF keypad digit handler (`1` to `9`), and Browser Development Phone Simulator (`/phone-simulator`). | **PROTOTYPE VERIFIED ✓** | *"Basic phone users can navigate via speech or keypad DTMF digits over telephone lines."* |
| **"Cross-Channel Synchronization"** | Appointments booked over Phone Simulator immediately reflect in Customer PWA (`/my-appointments`), Provider Console (`/provider`), and Admin Console (`/admin`). | **VERIFIED ✓** | *"The phone IVR and smartphone PWA connect to the exact same backend and database."* |
| **"Live PSTN Telephony Calls"** | Provider-neutral staging adapter (`ExotelTelephonyProvider`) for ExoML XML responses (`/webhooks/exotel/incoming`). External Indian Exophone number not provisioned. | **NOT YET LIVE (STAGING READY)** | *"The platform uses a Development Phone Simulator. The architecture is staging-ready to connect to an Exotel virtual number."* |
| **"SMS Notifications"** | Provider-neutral SMS adapter (`MSG91SMSProvider` & `DevelopmentSMSProvider`). In-memory log and status tracking active. | **SIMULATED / STAGING READY** | *"SMS dispatch is logged via development notifications. MSG91 DLT route integration is staging-ready."* |
| **"AI Medical Diagnosis"** | Bypassed. JanSethu intentionally does NOT diagnose or prescribe medical treatment. | **NOT APPLICABLE (BY DESIGN)** | *"JanSethu AI assists with intent understanding and appointment navigation. It explicitly does NOT diagnose patients."* |
| **"Deterministic Emergency Routing"** | Natural language intent parser routes emergency utterances directly to `EMERGENCY` state, returning 108 ambulance & casualty desk contacts. | **VERIFIED ✓** | *"Emergency routing is deterministic and provides immediate 108 ambulance information without diagnostic questions."* |
