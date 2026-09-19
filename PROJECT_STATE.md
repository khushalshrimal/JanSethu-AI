# JANSETHU AI - PROJECT STATE & ARCHITECTURE AUDIT

**Last Updated:** 2026-09-19  
**Target Scope:** SIH Healthcare-Access Prototype for Rural & Underserved Users in Maharashtra  
**Current Status:** ✅ All 6 Phases Complete! (Phase 1 PWA, Phase 2 Feature Phone IVR Simulator, Phase 3 Smart Facility Routing Engine, Phase 4 End-to-End Journey & Token Generation, Phase 5 Provider/Admin Dashboard with Live Status Synchronization, Phase 6 Final Demo Polish & 1-Click Scenario Preset Switcher) | FastAPI Backend + SQLite DB (`jansethu.db`) | Tri-lingual Marathi (`mr`), Hindi (`hi`) & English (`en`) Support

---

## 1. Project Concept & Dual-Channel Architecture

JanSethu AI is a voice-first rural healthcare ACCESS and NAVIGATION platform designed to connect citizens in rural areas (specifically Maharashtra) with local healthcare facilities (PHCs, CHCs, Sub-District and District Hospitals).

### Access Channels
1. **Smartphone Users (PWA / Web)**:
   - Voice/text interaction in Marathi, Hindi, and English.
   - Healthcare facility search, interactive OpenStreetMap Leaflet map view.
   - Doctor slot selection, appointment booking, ticket generation (`A-104`).
   - 6-stage live appointment tracking timeline (`TrackAppointmentScreen.jsx`).
   - Emergency 108 access & safety disclaimer.
   - Provider/Admin management portal (`ProviderDashboardScreen.jsx`).
   - Demo Mode quick-trigger scenario bar (`DemoPresetBar.jsx`).
2. **Basic / Keypad Phone Users (Phone Call Channel)**:
   - Voice-first IVR telephone channel simulator (`PhoneSimulatorScreen.jsx`).
   - DTMF keypad fallback (Press 1 for Marathi/Hindi, 2 for English).
   - Natural speech intent extraction (`intent_engine.py`).
   - Automatic appointment booking & multi-lingual SMS confirmation.

### Unified Architecture (Single Source of Truth)
```
                    FastAPI Core
                         |
               Healthcare Database (jansethu.db)
                         |
        +----------------+----------------+
        |                |                |
        PWA          Phone Call        Provider
   (Smartphone)     (Feature Phone)    Dashboard
        |                |            (Role Switcher
        +--------+-------+             Status & Slots)
                 |
                SMS
```

> **CRITICAL ARCHITECTURAL ENFORCEMENT:** Both smartphone PWA users and feature-phone voice callers query and update the exact same SQLite database (`jansethu.db`) via FastAPI core. Phone-created appointments and PWA-created appointments share the identical ORM database model (`models.Appointment`). Zero fake or decoupled channels exist.

---

## 2. Project Entry Points

- **Backend Entry Point**: `backend/main.py` (FastAPI app running on Uvicorn server, default port 8000).
- **Frontend Entry Point**: `frontend/src/main.jsx` ➔ `frontend/src/App.jsx` (React 18 + Vite + Tailwind CSS).

---

## 3. Demo Presets & Execution Guide

The PWA header features a visible **DEMO MODE** bar allowing 1-click execution of 3 predefined real-world scenarios:

### 1. DEMO 1: Normal Rural Patient (Hindi)
- **User Prompt**: Hindi speech/input asking for fever doctor in Baramati (*"Mujhe Baramati me bukhar ke liye doctor dikhana hai"*).
- **Flow**: Smart routing ➔ Doctor (Dr. Sharma) ➔ Slot selection ➔ Booking confirmation token `A-104` ➔ Simulated SMS ➔ 6-Stage Tracking Timeline.

### 2. DEMO 2: Emergency Risk Screening
- **User Prompt**: Exact prompt: *"Mere papa ko saans lene mein bahut dikkat ho rahi hai."*
- **Flow**: Safety engine detects respiratory distress ➔ Pauses routine OPD booking ➔ Displays `🚨 POTENTIAL EMERGENCY DETECTED` banner ➔ Provides `[CALL 108 EMERGENCY]` and `[FIND EMERGENCY FACILITY]` actions linking to Baramati Government Hospital Trauma Unit.

### 3. DEMO 3: Marathi Spoken Flow
- **User Prompt**: Spoken Marathi request (*"मला डॉक्टरांना भेटायचे आहे."*).
- **Flow**: Language auto-switches to Marathi (`mr`) ➔ Spoken Marathi voice response ➔ Facility search ➔ Marathi booking confirmation & Marathi SMS.

---

## 3.1 SIH 3-5 Minute Pitch Video Script & Recording Guide

Use the **SIH DEMO WIZARD** banner at the top of the PWA or follow this exact step-by-step pitch script while recording:

| Step | Target Screen / Route | Presenter Click / Action | Presenter Narration Script (Say Into Mic) | Expected System Output |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `home` (`HomeScreen.jsx`) | Show Landing Hero Page | *"Welcome to JanSethu AI, a voice-first healthcare access platform for rural users in Maharashtra."* | Hero banner, service categories, and voice search button |
| **2** | `home` (`HomeScreen.jsx`) | Point to Channel Badges | *"JanSethu AI connects users through two channels: smartphone PWA and feature phone IVR calls."* | PWA and basic feature phone architecture overview |
| **3** | `phone` (`PhoneSimulatorScreen.jsx`) | Click `[Start Call]` | *"Let us demonstrate a call from a basic feature phone. The user dials our toll-free hotline."* | Nokia phone simulator connects call |
| **4** | `phone` (`PhoneSimulatorScreen.jsx`) | Press `1` or select `Hindi` | *"The IVR greets the caller in Hindi. The user selects Hindi."* | IVR speaks Hindi welcome message |
| **5** | `phone` (`PhoneSimulatorScreen.jsx`) | Click `"Mujhe teen din se tez bukhar hai"` | *"The patient speaks naturally in Hindi: 'Mujhe teen din se tez bukhar hai in Baramati.'"* | Spoken text appears in transcript |
| **6** | `phone` (`PhoneSimulatorScreen.jsx`) | Point to Live AI Panel | *"JanSethu AI extracts key entities: Symptom = Fever, Duration = 3 days, Location = Baramati."* | Live AI Extraction panel populates |
| **7** | `phone` (`PhoneSimulatorScreen.jsx`) | Highlight Safety Engine | *"Our safety engine evaluates symptoms. Since fever is routine, it routes to General OPD."* | Non-diagnostic safety screening: Routine OPD |
| **8** | `facilities` (`FacilityResultsScreen.jsx`) | View Matching Facility | *"Smart Routing evaluates nearby facilities in Baramati based on service match and doctor availability."* | Baramati Government Hospital (95% Smart Score) |
| **9** | `slots` (`SlotSelectionScreen.jsx`) | View Slot Grid | *"The system displays live doctor availability for General OPD & Pediatrics."* | Available OPD slots grid |
| **10** | `slots` (`SlotSelectionScreen.jsx`) | Click `10:30 AM` Slot | *"Patient selects the 10:30 AM slot with Dr. Sharma."* | Slot selected and highlighted |
| **11** | `confirmation` (`ConfirmationScreen.jsx`) | Fill Patient Details | *"The patient confirms their details (Ramesh Pawar, Baramati)."* | Patient booking confirmation form |
| **12** | `confirmation` (`ConfirmationScreen.jsx`) | Click `[Confirm Booking]` | *"Appointment confirmed! Unique Token A-104 is generated in our SQLite database."* | Confirmed Ticket Card with Token `A-104` |
| **13** | `confirmation` (`ConfirmationScreen.jsx`) | Play Voice Confirmation | *"JanSethu AI speaks confirmation back to the patient: 'आपका अपॉइंटमेंट टोकन A-104 पक्का हो गया है।'"* | Audio voice confirmation synthesis |
| **14** | `confirmation` (`ConfirmationScreen.jsx`) | Show SMS Card | *"An SMS receipt is dispatched to the patient's phone containing Token A-104 and appointment time."* | Green SMS Confirmation receipt card |
| **15** | `track` (`TrackAppointmentScreen.jsx`) | View 6-Stage Timeline | *"The patient can track their appointment progress in real-time through a 6-stage status timeline."* | 6-stage tracking timeline showing Token `A-104` |
| **16** | `dashboard` (`ProviderDashboardScreen.jsx`) | Open Provider Dashboard | *"On the provider side, hospital staff view Token A-104 live in their table and update status."* | Provider dashboard showing Token `A-104` |
| **17** | `emergency` (`EmergencyScreen.jsx`) | Trigger Emergency Phrase | *"Now let us test an emergency scenario: 'Mere papa ko saans lene mein bahut dikkat ho rahi hai.'"* | Respiratory distress emergency trigger |
| **18** | `emergency` (`EmergencyScreen.jsx`) | Show Emergency Alert | *"JanSethu AI detects a potential emergency, pauses OPD booking, and routes to 108 ambulance & trauma care."* | `🚨 POTENTIAL EMERGENCY DETECTED` alert banner & 108 dial |
| **19** | `voice` (`VoiceAssistantScreen.jsx`) | Switch Language to `मराठी` | *"Finally, JanSethu AI provides first-class Marathi voice and UI support across rural Maharashtra."* | Tri-lingual Marathi UI & spoken response |

---

## 4. Existing Backend APIs (`backend/main.py`)

### System & Health
- `GET /health`, `GET /api/health`: Health status & disclaimer.

### Telephony & IVR Webhooks
- `GET /telephony/config`, `GET /api/telephony/config`: Provider setup status & credentials check.
- `POST /telephony/voice`, `POST /api/telephony/voice`: Handles incoming phone call welcome TwiML XML.
- `POST /telephony/gather`, `POST /api/telephony/gather`: Processes DTMF digits & spoken voice input.
- `POST /telephony/sms`, `POST /api/telephony/sms`: Triggers SMS notification dispatch.

### Voice AI Intent Engine
- `POST /voice/intent`, `POST /api/voice/intent`: Natural language query parser returning intent, response text (Marathi, Hindi, English), matched facilities, and open slots.

### Healthcare Facilities & Emergency
- `GET /facilities`, `GET /api/facilities`: Returns facilities (supports `city`, `area`, `service`, `search` query parameters).
- `GET /emergency/facilities`, `GET /api/emergency/facilities`: Returns hospitals with emergency/maternity wards.
- `GET /facilities/{facility_id}`, `GET /api/facilities/{facility_id}`: Returns facility details and available slots.
- `GET /facilities/{facility_id}/slots`, `GET /api/facilities/{facility_id}/slots`: Returns doctor slots for a facility.
- `POST /facilities/{facility_id}/slots`, `POST /api/facilities/{facility_id}/slots`: Adds a new doctor slot.

### Provider & Emergency Dispatch
- `GET /provider/emergency_cases`, `GET /api/provider/emergency_cases`: Returns active voice-triage emergency cases.

### Slots Management
- `PATCH /slots/{slot_id}/toggle`, `PATCH /api/slots/{slot_id}/toggle`: Toggles slot availability (`available: true/false`).
- `DELETE /slots/{slot_id}`, `DELETE /api/slots/{slot_id}`: Removes a doctor slot.

### Appointments & Status Synchronization
- `POST /appointments`, `POST /api/appointments`: Creates a new patient appointment request with token `A-104`.
- `GET /appointments`, `GET /api/appointments`: Lists appointments (supports `facility_id`, `status` filters).
- `GET /appointments/{appointment_id}`, `GET /api/appointments/{appointment_id}`: Gets appointment details.
- `PATCH /appointments/{appointment_id}/status`, `PATCH /api/appointments/{appointment_id}/status`: Updates status (`confirmed`, `waiting`, `consultation`, `completed`, `cancelled`, `rejected`, `rescheduled`).
- `PATCH /appointments/{appointment_id}/reschedule`, `PATCH /api/appointments/{appointment_id}/reschedule`: Reschedules appointment date/time.

---

## 5. Database Schema (`backend/jansethu.db`)

SQLite database managed via SQLAlchemy ORM (`models.py`, `schemas.py`, `crud.py`).

### Tables
1. **`facilities`**: `id`, `name`, `name_hi`, `city`, `area`, `address`, `latitude`, `longitude`, `services`, `contact_phone`, `facility_type`.
2. **`slots`**: `id`, `facility_id`, `date`, `time`, `available`, `doctor_name`, `department`.
3. **`appointments`**: `id`, `facility_id`, `service`, `date`, `time`, `patient_name`, `phone`, `status`, `token_number`, `doctor_name`, `created_at`.

---

## 6. Complete List of Completed Features (Phases 1-6)

1. **Dual-Channel Access**: Smartphone PWA & Keypad Phone IVR Simulator (`PhoneSimulatorScreen.jsx`).
2. **Tri-Lingual Localization**: Full Marathi (`mr`), Hindi (`hi`), and English (`en`) support with speech synthesis (`mr-IN`, `hi-IN`, `en-IN`).
3. **Deterministic Safety & Risk Screening Engine**: Detects severe respiratory distress (*"saans lene mein bahut dikkat"*) and pauses routine OPD booking to route to 108 emergency dispatch.
4. **Smart Facility Routing Engine**: Calculates score based on distance, service match, doctor availability, emergency capability, and facility status.
5. **Interactive OpenStreetMap (`FacilityMap.jsx`)**: Leaflet map rendering hospital pins, popups, and GPS navigation links.
6. **End-to-End Journey & Token Generation**: Slot picker, patient details input, DB slot locking, token generation (`A-104`), spoken voice confirmation, and simulated SMS receipt card.
7. **6-Stage Live Tracking Timeline**: Stage progression (`Submitted ➔ Confirmed ➔ Waiting in OPD Lobby ➔ In Doctor OPD ➔ Consultation Completed`) updated live from provider actions.
8. **Provider / Admin Dashboard**: Multi-role switcher (`Central Admin`, `OPD Desk`, `108 Dispatcher`), 4 statistics counters, appointment status transition table, doctor slot CRUD, and emergency 108 dispatch queue.
9. **Demo Mode Presets**: 1-click execution for Demo 1 (Normal Hindi), Demo 2 (Emergency), and Demo 3 (Marathi Spoken).

---

## 7. Environment Variables

Create a `backend/.env` file for optional external telephony credentials (Defaults to Mock Mode if omitted):

```ini
# Server Port
PORT=8000

# Telephony Credentials (Optional: Twilio / Exotel)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

EXOTEL_SID=
EXOTEL_TOKEN=
```

---

## 8. Startup & Execution Instructions

### Run Backend API:
```bash
cd backend
py -3 -m uvicorn main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`

### Run Backend Integration Tests (All 6 Suites):
```bash
cd backend
py -3 -m unittest test_backend.py test_phase2_phone.py test_phase3_routing.py test_phase4_journey.py test_phase5_provider.py test_phase6_demo.py
```

### Run Frontend PWA:
```bash
cd frontend
npm run dev
```
- Access App: `http://localhost:5173`

### Build Production Bundle:
```bash
cd frontend
npm run build
```

---

## 9. Known Limitations & Healthcare Safety Disclaimer

1. **Non-Diagnostic Policy**: JanSethu AI is an access and navigation platform only. It does **NOT** issue clinical diagnoses, prescribe medications, or replace human doctors.
2. **Mock Telephony Default**: Web telephony operates in simulated mode unless valid Twilio/Exotel credentials are supplied in `backend/.env`.
3. **Browser Web Speech Dependency**: Web Speech recognition relies on browser APIs (Chrome/Edge/Safari); a manual fallback text field is provided on screen.

---
*JanSethu AI — Empowering Rural Healthcare Access in Maharashtra through Voice & Simple Telephony.*
