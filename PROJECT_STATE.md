# JanSethu AI — Current Project State (Phase 7 Final Integration, Demo Validation & SIH Readiness Report)

**Audit & Upgrade Date**: September 22, 2026  
**Project Lead**: Antigravity AI Team / JanSethu AI Healthcare Platform  
**Phase Status**: PHASE 7 STATUS: COMPLETE (539 / 539 Pytest Unit & Integration Tests Passing — 100% Pass Rate across 27 test modules)



---

## 1. Project Overview

JanSethu AI is an existing healthcare access MVP designed for rural and underserved populations across India. It bridges healthcare access gaps through dual interaction channels:
1. **Smartphone PWA** (Symptom guidance, facility discovery, doctor search, slot booking, ticket retrieval, provider OPD queue management).
2. **Telephony Voice & IVR Hotline Simulator** (Continuous hands-free spoken voice dialogue, barge-in interruption support, DTMF keypad fallback, emergency override, and automated booking).

Both interaction channels communicate with a single unified FastAPI backend service and write to a shared SQLite/PostgreSQL relational database. Any appointment created via voice phone call immediately appears in `/my-appointments`, confirmation tickets, and the provider OPD queue dashboard.

---

## 2. Tech Stack

- **Frontend**: React 18, Vite 5, Tailwind CSS v3, Axios, Lucide React icons, Web Speech API (`webkitSpeechRecognition` & `SpeechSynthesisUtterance`).
- **Backend**: Python 3.14 / FastAPI, Uvicorn ASGI server, SQLAlchemy 2.0 ORM, Pydantic v2 validation schemas, PyJWT authentication, Passlib (bcrypt).
- **Database**: SQLite (`jansethu_v2.db`), Alembic database migration management.
- **Testing**: Pytest test framework with AnyIO async test runner.
- **Architecture**: Modular service layer pattern with separation of concerns across API routing, business logic services, database repositories, and hardware integration adapters.

---

## 3. Repository Structure

```
JanSethu AI/
├── backend/
│   ├── alembic/                      # Alembic DB migration scripts (10 versions)
│   ├── app/
│   │   ├── api/v1/endpoints/        # 13 FastAPI API router modules
│   │   ├── core/                    # Config, security, prompts, rate limiter, middleware
│   │   ├── database/                # Base declaration & session factory
│   │   ├── integrations/            # Telephony & SMS providers (Dev & Production adapters)
│   │   ├── models/                  # 8 SQLAlchemy model files (13 ORM entities)
│   │   ├── repositories/            # Database query abstractions
│   │   ├── schemas/                 # Pydantic data validation schemas
│   │   ├── services/                # Business logic (NLU, Safety, Tools, Phone Session, Provider)
│   │   └── tests/                   # 23 automated unit & integration test modules (331 tests)
│   ├── scripts/                     # DB seed scripts & verification scripts
│   └── Dockerfile                   # Backend container definition
├── frontend/
│   ├── public/                      # Static assets, favicon.svg, manifest.json
│   ├── src/
│   │   ├── components/layout/       # Navbar, Footer UI components
│   │   ├── context/                 # AuthContext authentication state provider
│   │   ├── pages/                   # 10 React page components (Home, Facilities, PhoneSimulator, etc.)
│   │   ├── services/                # Axios API client modules for backend endpoints
│   │   ├── App.jsx                  # React Router v7 route definitions
│   │   └── main.jsx                 # Client entry point
│   ├── package.json                 # Frontend dependencies & scripts
│   └── vite.config.js               # Vite build configuration
├── jansethu_v2.db                   # Active SQLite database file
├── PROJECT_STATE.md                 # Single source of truth project state document
└── DEMO_GUIDE.md                    # Demonstration walkthrough & startup commands
```

---

## 4. Frontend Status

- **Framework**: React 18 with Vite 5.
- **Routing**: React Router (`react-router-dom` v7).
- **Pages**:
  - `Home.jsx` — Landing page with service overview & direct channel links.
  - `Login.jsx` & `Register.jsx` — User login & registration screens.
  - `Facilities.jsx` & `FacilityDetails.jsx` — Facility discovery & detail view.
  - `DoctorDetails.jsx` — Doctor profiles & slot selection UI.
  - `BookingConfirmation.jsx` — Appointment ticket view & referral code retrieval.
  - `MyAppointments.jsx` — Patient appointments dashboard (cancellation/rescheduling).
  - `PhoneSimulator.jsx` — Spoken voice hotline & IVR phone simulator.
  - `provider/ProviderDashboard.jsx` — Provider OPD queue & consultation status management.
  - `admin/AdminConsole.jsx` — Admin system metrics & audit log view.
- **State Management**: React Context (`AuthContext`) for auth session state; local component state for page workflows.
- **API Communication**: Centralized Axios client (`src/services/api.js`) targeting `http://localhost:8000/api/v1` with Bearer token interceptor and standardized error handling.
- **Classification**:
  - `PhoneSimulator.jsx`: WORKING
  - `MyAppointments.jsx`: WORKING
  - `Facilities.jsx`: WORKING
  - `ProviderDashboard.jsx`: WORKING
  - `BookingConfirmation.jsx`: WORKING
  - PWA Offline Caching: PARTIALLY WORKING (Manifest present; dynamic offline sync queued for future phase).

---

## 5. Backend Status

- **Framework**: FastAPI running on Uvicorn.
- **Entry Point**: `backend/app/main.py`.
- **API Endpoints Summary**:
  - `GET /api/v1/health` & `/health/ready` & `/health/demo-readiness`: Health check and system verification endpoints.
  - `POST /api/v1/auth/register` & `/login`: Authentication and JWT token issuance.
  - `GET /api/v1/facilities/search`: Haversine location & pincode-based healthcare facility discovery.
  - `GET /api/v1/doctors/search` & `GET /api/v1/doctors/{id}/slots`: Doctor search and 30-minute OPD slot calculation.
  - `POST /api/v1/appointments/book`, `GET /appointments/me`, `POST /appointments/{id}/cancel`: Appointment lifecycle management.
  - `POST /api/v1/conversation/message`: Stateful multi-turn conversation manager turn endpoint.
  - `POST /api/v1/ai/analyze`: LLM NLU intent and entity extraction endpoint.
  - `POST /api/v1/emergency/handle`: Priority emergency override and ambulance request simulation.
  - `POST /api/v1/phone/start`, `/dtmf`, `/voice`, `/end`: Telephony state machine endpoints.
  - `GET /api/v1/provider/queue`: Provider OPD queue dashboard retrieval.

---

## 6. Database Status

- **Engine**: SQLite (`jansethu_v2.db`) / PostgreSQL compatible via SQLAlchemy 2.0 ORM.
- **Domain Tables (13 Total)**:
  1. `users`: User accounts, hashed passwords, roles (`CUSTOMER`, `PROVIDER`, `ADMIN`), language preferences.
  2. `patient_profiles`: Patient demographic details, village, district, state, emergency contact details.
  3. `facilities`: Healthcare institutions (hospitals, PHCs, CHCs), location coordinates (lat/lng), pincode, district, emergency availability status.
  4. `departments`: Hospital departments (General Medicine, Orthopedics, Pediatrics, Emergency, etc.).
  5. `emergency_contacts`: Facility and regional emergency phone numbers and ambulance contacts.
  6. `doctors`: Doctor profiles, qualifications, specializations, department mappings, phone numbers.
  7. `doctor_availabilities`: Weekly recurring OPD schedules (day of week, start time, end time, 30-min slot duration).
  8. `doctor_schedule_exceptions`: Specific leave/holiday dates when doctor is unavailable.
  9. `appointments`: Booked appointments with unique referral codes (`JS-2026-XXXXXX` / `JAN-REF-2026-XXXX`), appointment status, queue tokens, visit status, and SQL double-booking unique constraint `(doctor_id, appointment_date, start_time)`.
  10. `call_sessions`: Telephony and simulator multi-turn call session state.
  11. `conversation_messages`: Logged transcript turns for call sessions.
  12. `sms_notifications`: Dispatched SMS notification audit trail.
  13. `audit_logs` & `appointment_audit_logs`: Audit trail for provider actions and appointment state changes.
- **Data Status**: Seeded with real Maharashtra district samples (Baramati, Pune, Satara, Solapur, Ahmednagar, Mumbai) with active doctors and weekly OPD schedules.

---

## 7. AI/LLM Status

- **Architecture**:
  - Tier 1: `SafetyEngine` (`app/services/safety_engine.py`) — Fast deterministic regex pattern scanner for emergency phrases in Hindi, Hinglish, Marathi, English.
  - Tier 2: `IntentParser` & `EntityExtractor` (`app/services/voice/`) — Fast deterministic keyword parser for intent and slot extraction.
  - Tier 3: `LLMService` (`app/services/llm_service.py`) — Provider abstraction layer supporting `development` (local deterministic fallback), `ollama`, `openai`, `gemini`.
  - Tier 4: `ConversationManager` (`app/services/conversation_manager.py`) — Session state memory, entity merging across turns, entity correction handling, missing field identification, and concise response generation.
- **Key Finding**: System operates deterministically in `development` mode without requiring external paid API keys. When placed in `UNSCRIPTED_AI` mode, it dynamically evaluates turns and queries real database tools.

---

## 8. Telephony Status

- **Web Hotline Simulator**: Implemented in `PhoneSimulator.jsx`.
- **Speech Recognition**: Browser Web Speech API (`webkitSpeechRecognition`) with continuous listening (`continuous = true`, `interimResults = true`).
- **Speech Synthesis**: Browser TTS (`SpeechSynthesisUtterance`) with voice language selector (`hi-IN`, `mr-IN`, `en-US`).
- **Conversational Barge-In**: User speech onset triggers `window.speechSynthesis.cancel()`, instantly stopping assistant TTS output and invalidating stale callbacks.
- **DTMF Fallback**: Physical keypad simulator for numeric DTMF inputs.

---

## 9. SMS Status

- **Adapter Architecture**: Factory pattern (`app/integrations/sms/factory.py`).
- **Development Adapter**: `DevelopmentSMSProvider` logs outgoing SMS messages to `sms_notifications` DB table and backend system console.
- **Production Adapter**: `MSG91SMSProvider` defined for live SMS HTTP gateway integration.

---

## 10. Emergency Flow Status

- **Intent Recognition**: Triggered by phrases like *"saans lene mein dikkat"*, *"chest pain"*, *"108"*, *"accident"*, *"heavy bleeding"*, *"behosh"*.
- **Priority Preemption**: High-confidence emergency signals immediately bypass normal appointment booking state machines.
- **Location Capture**: Captures landmark/area or reuses session location.
- **Ambulance Response**: Generates transparent simulated request code (`AMB-MOCK-XXXXX`), provides safety guidance, and returns real emergency facility contacts from database.

---

## 11. Facility Search Status

- **Capability**: Search by pincode, village, district, facility type (`GOVERNMENT_HOSPITAL`, `PHC`, `CHC`, `PRIVATE_HOSPITAL`), emergency capability, and Haversine GPS radius.
- **Database Query**: Performs real SQL queries against `facilities` table. No hardcoded search responses.

---

## 12. Doctor Search Status

- **Capability**: Filter doctors by facility, department, and specialty.
- **Availability Engine**: Dynamically calculates open 30-minute OPD slots for any date based on `doctor_availabilities` minus `doctor_schedule_exceptions` and existing active `appointments`.

---

## 13. Appointment Status

- **Booking Flow**: Patient/Facility/Department/Doctor selection -> Date/Slot selection -> User Confirmation -> Database transaction with unique constraint check -> Referral Code Generation -> SMS Log -> Provider Queue Sync.
- **Referral Code Formats**: `JS-2026-XXXXXX` and `JAN-REF-2026-XXXX`.
- **Status**: WORKING cleanly with cross-channel synchronization.

---

## 14. Language Status

- **Languages Supported**: Hindi (`HI`), Marathi (`MR`), English (`EN`).
- **Prompt Localizations**: Multi-lingual string templates configured in `app/core/prompts.py` and `ConversationManager`.
- **Voice TTS/STT**: Native browser language codes mapped (`hi-IN`, `mr-IN`, `en-US`).
- **NLU Coverage**: High coverage for Hindi and English; Marathi basic keywords mapped, with room for dialect expansion in future phases.

---

## 15. PWA Status

- **Manifest**: `public/manifest.json` configured with standalone mode, icons, and theme colors.
- **Service Worker**: `public/sw.js` registration file available in build assets.

---

## 16. Authentication Status

- **Mechanism**: OAuth2 Password bearer token standard with JWT tokens.
- **Security**: Passlib bcrypt password hashing. Token expiration enforced.
- **Roles**: `CUSTOMER`, `PROVIDER`, `ADMIN`.

---

## 17. Test Results

- **Total Test Cases**: 342
- **Passed**: 342 (100%)
- **Failed**: 0
- **Skipped**: 0
- **Execution Time**: ~107 seconds.
- **Test Modules**: 24 files in `backend/app/tests/` covering Phase 2 synthetic healthcare queries, domain models, auth, availability, NLU, conversation manager, healthcare tools, emergency, provider dashboard, and phone simulator.

---

## 18. Known Bugs & Code Warnings

1. **Python 3.14 `datetime.utcnow()` Deprecation Warnings**: Standard library deprecation warning across datetime calls (does not impact runtime execution; can be updated to `datetime.now(timezone.utc)` in future maintenance).
2. **Network Connectivity Error Handling**: When FastAPI backend is not running, frontend displays *"Unable to reach JanSethu servers"*.

---

## 19. Hardcoded/Mock Components

| Component | Status | Description |
| :--- | :--- | :--- |
| **Telephony Gateway** | MOCK | Browser Web Speech API in `PhoneSimulator.jsx` (Exotel live gateway configured via webhooks when credentials supplied). |
| **SMS Gateway** | MOCK | `DevelopmentSMSProvider` logs SMS to database and console. |
| **Ambulance Dispatch** | MOCK | Returns simulated token `AMB-MOCK-XXXXX` with non-diagnostic guidance. |

---

## 20. Missing Components (For Future Phases)

- Expanded Marathi healthcare dialect dictionary.
- Live Exotel telephony SIP trunk connection.
- Live MSG91 SMS API production key configuration.
- Real-time patient OPD queue numbering token display.

---

## 21. Existing Features That MUST Be Preserved

1. **All 13 SQLAlchemy database models and 331 passing pytest tests.**
2. **Double-booking prevention with SQL unique constraints on active doctor slots.**
3. **Unique referral code generation (`JS-2026-XXXXXX` / `JAN-REF-2026-XXXX`).**
4. **Cross-channel data synchronization between Telephony Phone Call appointments and PWA `/my-appointments` & `/provider` queue.**
5. **Deterministic `SafetyEngine` emergency override layer.**
6. **Continuous microphone listening & instant conversational barge-in interruption in `PhoneSimulator.jsx`.**

---

## 22. Recommended Architecture Changes For Future Phases

- **Phase 2 (Database & Healthcare Dataset Expansion)**: Enrich database with detailed rural Maharashtra healthcare data (PHCs, CHCs, Sub-Centers, District Hospitals, ambulances, queue tokens).
- **Phase 3 (Advanced AI / LLM Tool-Calling Agent)**: Enhance LLM tool calling for complex multi-attribute facility and doctor queries.
- **Phase 4 (Production Telephony & Offline PWA)**: Enable production Exotel/MSG91 adapters and dynamic offline IndexedDB sync.

---

## 23. Database Improvement Requirements

- Add realistic Maharashtra district dataset (Baramati, Pune, Satara, Solapur, Nashik, Kolhapur) with PHCs and CHCs.
- Add `ambulances` entity table for tracking local emergency vehicle availability.
- Add real-time OPD token numbering system for live patient queue tracking.

---

## 24. AI Improvement Requirements

- Expand Marathi natural speech parser dictionary.
- Support natural conversational disambiguation when multiple doctors match user criteria.
- Enforce schema-bounded tool calling for 100% zero-hallucination factual responses.

---

## 25. Phase 3 Completion Summary

- **Status**: 100% Completed & Verified (506 / 506 Pytest Unit & Integration Tests Passing).
- **Core Deliverables**:
  1. `app/schemas/nlu.py`: Defined strongly-typed `NLUIntent` (25+ intents), `NLUEntities`, `NLUAnalysisRequest`, and `NLUAnalysisResponse`.
  2. `app/services/safety_engine.py`: Enhanced multi-lingual deterministic emergency preemption (breathing difficulty, chest pain, accidents, bleeding, 108 calls).
  3. `app/services/llm_service.py`: Upgraded `DeterministicNLUParser` and `LLMService` for multi-lingual intent parsing, multi-entity extraction, and date/time normalization.
  4. `app/services/conversation_manager.py`: Upgraded stateful multi-turn dialog manager for context accumulation, dynamic parameter prompting, and zero-hallucination DB tool bindings.
  5. `app/tests/test_phase3_nlu.py`: Built 164 comprehensive NLU unit/integration test cases across EN, HI, Hinglish, and MR.
  6. `AI_ARCHITECTURE.md`: Created system architectural specification document at project root.

---

## 26. Phase 4 Healthcare Action Engine Completion Summary

- **Status**: 100% Completed & Verified (512 / 512 Pytest Unit & Integration Tests Passing).
- **Core Deliverables**:
  1. `app/services/action_router.py`: Registered 17 controlled backend actions connecting Phase 3 NLU to Phase 2 relational database services without raw SQL execution or LLM hallucinations. Writes action execution records to `audit_logs`.
  2. `app/services/healthcare_tools.py`: Added `find_available_ambulances`, `find_emergency_facilities`, `search_facilities_by_specialty`, `get_doctor_details`, `create_emergency_request`, and `send_confirmation`.
  3. `app/services/conversation_manager.py`: Integrated `ActionRouter` for turn processing, priority location capture in emergencies, and multi-lingual database-grounded natural response generation.
  4. `app/tests/test_phase4_healthcare_tools.py`: Added test suite verifying 17 registered actions, ambulance status filtering (`AVAILABLE`), emergency dispatches, appointment rescheduling, cancellation, multi-lingual dialogs, and simulated end-to-end test conversations A-D.
  5. `AI_ARCHITECTURE.md`: Updated architecture specification to document `NLU -> Conversation State -> Safety Engine -> Action Router -> Healthcare Services -> Database -> Grounded Response` pipeline.

