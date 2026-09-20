# JANSETHU AI — SIH PROTOTYPE AUDIT & TECHNICAL DOCUMENTATION

**Last Updated:** 2026-09-20  
**Target Scope:** SIH Healthcare-Access Prototype for Rural & Underserved Users in Maharashtra  
**Current Status:** ✅ 100% DEMO-READY PROTOTYPE! (Phases 1–6 Complete + SIH 19-Step Guided Pitch Wizard + Voice-First IVR Phone Simulator + Deterministic Token A-104 Data Consistency) | FastAPI Backend + SQLite DB (`jansethu.db`) | Tri-Lingual Marathi (`mr-IN`), Hindi (`hi-IN`) & English (`en-IN`) Support

---

## 1. Project Concept & Dual-Channel Architecture

JanSethu AI is a voice-first rural healthcare **ACCESS** and **NAVIGATION** platform designed to connect citizens in rural areas (specifically Maharashtra) with local healthcare facilities (PHCs, CHCs, Sub-District and District Hospitals).

### Access Channels
1. **Smartphone Users (PWA / Web)**:
   - Voice/text interaction in Marathi, Hindi, and English.
   - Healthcare facility search, interactive OpenStreetMap Leaflet map view.
   - Doctor slot selection, appointment booking, ticket generation (`Token A-104`).
   - 6-stage live appointment tracking timeline (`TrackAppointmentScreen.jsx`).
   - Emergency 108 access & non-diagnostic safety disclaimer.
   - Healthcare Provider / Admin management portal (`ProviderDashboardScreen.jsx`).
   - SIH Video Pitch Guided Demo Wizard (`SihDemoWizard.jsx`).
2. **Basic / Keypad Phone Users (Phone Call Channel - HERO FEATURE)**:
   - Voice-first IVR telephone call simulator (`PhoneSimulatorScreen.jsx`).
   - Web Speech Recognition (`window.SpeechRecognition`) for spoken input (`hi-IN`, `mr-IN`, `en-IN`).
   - Web Speech Synthesis (`window.SpeechSynthesis`) for spoken voice responses.
   - Demo Voice Mode (Simulated speech phrase picker for video recording).
   - DTMF keypad fallback (`1`=Hindi, `2`=Marathi, `3`=English).
   - Text input fallback for browsers without microphone access.
   - Real-time AI extraction panel & live conversation transcript.

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

## 3. SIH 3-5 Minute Pitch Video Script & Recording Guide

Use the **SIH DEMO WIZARD** banner at the top of the PWA or follow this exact step-by-step pitch script while recording:

| Step | Target Screen / Route | Presenter Click / Action | Presenter Narration Script (Say Into Mic) | Expected System Output |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `home` (`HomeScreen.jsx`) | Show Landing Hero Page | *"Welcome to JanSethu AI, a voice-first healthcare access platform for rural users in Maharashtra."* | Hero banner, service categories, and voice search button |
| **2** | `home` (`HomeScreen.jsx`) | Point to Channel Badges | *"JanSethu AI connects users through two channels: smartphone PWA and feature phone IVR calls."* | PWA and basic feature phone architecture overview |
| **3** | `phone` (`PhoneSimulatorScreen.jsx`) | Click `[Start Call]` | *"Let us demonstrate a call from a basic feature phone. The user dials our toll-free hotline."* | Nokia phone simulator connects call: `📞 JANSETHU AI - CALL CONNECTED` |
| **4** | `phone` (`PhoneSimulatorScreen.jsx`) | Press `1` or select `Hindi` | *"The IVR greets the caller in Hindi. The user selects Hindi."* | IVR speaks Hindi welcome message: `🔊 AI SPEAKING` |
| **5** | `phone` (`PhoneSimulatorScreen.jsx`) | Tap `[ 🎙️ TAP TO SPEAK ]` or Click Phrase | *"The patient speaks naturally in Hindi: 'Mujhe teen din se tez bukhar hai in Baramati.'"* | `🎙️ LISTENING` waveform ➔ Spoken text in transcript |
| **6** | `phone` (`PhoneSimulatorScreen.jsx`) | Point to Live AI Panel | *"JanSethu AI extracts key entities: Symptom = Fever, Duration = 3 days, Location = Baramati."* | Live AI Extraction panel populates |
| **7** | `phone` (`PhoneSimulatorScreen.jsx`) | Highlight Safety Engine | *"Our safety engine evaluates symptoms. Since fever is routine, it routes to General OPD without clinical diagnosis."* | Non-diagnostic safety screening: Routine OPD |
| **8** | `facilities` (`FacilityResultsScreen.jsx`) | View Matching Facility | *"Smart Routing evaluates nearby facilities in Baramati based on service match and doctor availability."* | Baramati Government Hospital (95% Smart Score) |
| **9** | `slots` (`SlotSelectionScreen.jsx`) | View Slot Grid | *"The system displays live doctor availability for General OPD & Pediatrics."* | Available OPD slots grid (`Dr. Sharma` 🟢 Available) |
| **10** | `slots` (`SlotSelectionScreen.jsx`) | Click `10:30 AM` Slot | *"Patient selects the 10:30 AM slot with Dr. Sharma."* | Slot selected and highlighted |
| **11** | `confirmation` (`ConfirmationScreen.jsx`) | Fill Patient Details | *"The patient confirms their details (Ramesh Pawar, Baramati)."* | Patient booking confirmation form |
| **12** | `confirmation` (`ConfirmationScreen.jsx`) | Click `[Confirm Booking]` | *"Appointment confirmed! Unique Token A-104 is generated in our SQLite database."* | Confirmed Ticket Card with Token `A-104` |
| **13** | `confirmation` (`ConfirmationScreen.jsx`) | Play Voice Confirmation | *"JanSethu AI speaks confirmation back to the patient: 'आपका अपॉइंटमेंट टोकन A-104 पक्का हो गया है।'"* | Audio voice confirmation synthesis playback |
| **14** | `confirmation` (`ConfirmationScreen.jsx`) | Show SMS Card | *"An SMS receipt is dispatched to the patient's phone containing Token A-104 and appointment time."* | Green SMS Confirmation receipt card (`Mock SMS Gateway`) |
| **15** | `track` (`TrackAppointmentScreen.jsx`) | View 6-Stage Timeline | *"The patient can track their appointment progress in real-time through a 6-stage status timeline."* | 6-stage tracking timeline showing Token `A-104` |
| **16** | `dashboard` (`ProviderDashboardScreen.jsx`) | Open Provider Dashboard | *"On the provider side, hospital staff view Token A-104 live in their table and update status."* | Provider dashboard showing Token `A-104` |
| **17** | `emergency` (`EmergencyScreen.jsx`) | Trigger Emergency Phrase | *"Now let us test an emergency scenario: 'Mere papa ko saans lene mein bahut dikkat ho rahi hai.'"* | Respiratory distress emergency trigger |
| **18** | `emergency` (`EmergencyScreen.jsx`) | Show Emergency Alert | *"JanSethu AI detects a potential emergency, pauses OPD booking, and routes to 108 ambulance & trauma care."* | `🚨 POTENTIAL EMERGENCY DETECTED` alert banner & 108 dial |
| **19** | `voice` (`VoiceAssistantScreen.jsx`) | Switch Language to `मराठी` | *"Finally, JanSethu AI provides first-class Marathi voice and UI support across rural Maharashtra."* | Tri-lingual Marathi UI (`mr-IN`) & spoken response |

---

## 4. Full Audit of JanSethu AI Prototype

### 1. Dual-Channel Access
- **Smartphone PWA**: Responsive React PWA with bottom navigation bar, voice input, facility maps, and appointment tracking.
- **Feature Phone IVR Call Channel**: Real-time simulated phone call UI (`PhoneSimulatorScreen.jsx`) with call connected header, speech recognition, speech synthesis, and live transcript.

### 2. Tri-Lingual Localization
- Full translation support for **Hindi (`hi-IN`)**, **Marathi (`mr-IN`)**, and **English (`en-IN`)** with audio synthesis playback.

### 3. Voice Input & Speech Engine (`speechEngine.js`)
- **Primary**: `[ 🎙️ TAP TO SPEAK ]` button utilizing browser `SpeechRecognition` API.
- **Demo Voice Mode**: 1-tap preset phrase picker for presentation recording (*"Mujhe teen din se tez bukhar hai in Baramati"*, *"Baramati"*, *"Mere papa ko saans lene mein bahut dikkat ho rahi hai"*, *"मला डॉक्टरांना भेटायचे आहे"*).
- **Fallback**: DTMF keypad (`1`=Hindi, `2`=Marathi, `3`=English) and text input fallback.

### 4. Deterministic Non-Diagnostic Safety Screening (`intent_engine.py`)
- Strictly enforces non-diagnostic policy: System categorizes symptoms for triage without issuing disease diagnoses or prescribing medications.
- Severe symptoms (*"saans lene mein bahut dikkat"*) pause routine OPD booking and trigger `🚨 POTENTIAL EMERGENCY DETECTED` with 1-tap `[CALL 108 EMERGENCY]` and `[FIND EMERGENCY FACILITY]`.

### 5. Smart Facility Routing Engine (`crud.py`)
- Ranks verified government hospitals (District Civil Hospital Baramati, PHCs, Sub-District Hospitals) using multi-criteria scoring: distance, service match, doctor availability, emergency capability, and operational status.

### 6. Doctor Availability & Slot Management
- Displays doctor status (`Dr. Sharma` 🟢 Available, `Dr. Patel` 🔴 Unavailable).
- Slot grid (09:00 AM, 10:30 AM, 11:45 AM, 02:00 PM) stored in SQLite DB (`jansethu.db`).

### 7. End-to-End Booking & Token Generation
- Confirms booking and generates unique Token `A-104` stored in `appointments` table.

### 8. Voice & SMS Confirmation
- Spoken confirmation via `SpeechSynthesis` (*"Your appointment token A-104 is confirmed..."*).
- Simulated SMS receipt card labeled `Mock SMS Gateway`.

### 9. 6-Stage Live Tracking Timeline (`TrackAppointmentScreen.jsx`)
- Interactive status timeline: `Submitted ➔ Confirmed (A-104) ➔ Hospital OPD Desk Notified ➔ Waiting in Lobby ➔ In OPD Consultation ➔ Completed`.

### 10. Healthcare Provider Dashboard (`ProviderDashboardScreen.jsx`)
- Multi-role switcher (`Central Admin`, `Hospital OPD Desk`, `108 Control Dispatcher`).
- 4 overview statistics counters (`Appointments: 42`, `Available Doctors: 8`, `Facilities: 5`, `Emergency Cases: 3`).
- Interactive appointment table with status transition buttons (`Confirm`, `Waiting`, `In OPD`, `Done`, `Cancel`). Updates in Provider Dashboard sync live to patient tracking timeline.
- Doctor slot CRUD and emergency 108 dispatch queue.

### 11. Deterministic Data Consistency
- All screens share the identical dataset for the demo journey:
  - **Appointment ID**: `JS-2026-001`
  - **Token Number**: `A-104`
  - **Patient Name**: `Ramesh Pawar (DEMO)` / `Demo Patient` (`+91-9876543210`)
  - **Facility**: `Government Sub-District Hospital, Baramati (DEMO)`
  - **Doctor**: `Dr. Sharma` (General OPD & Pediatrics)
  - **Time**: `10:30 AM`

---

## 5. Existing Backend APIs (`backend/main.py`)

### Health & Telephony
- `GET /health`, `GET /api/health`: System health & disclaimer.
- `GET /telephony/config`, `GET /api/telephony/config`: Provider setup status.
- `POST /telephony/voice`, `POST /api/telephony/voice`: Incoming call TwiML webhook.
- `POST /telephony/gather`, `POST /api/telephony/gather`: Processes spoken speech & DTMF digits.
- `POST /telephony/sms`, `POST /api/telephony/sms`: Triggers SMS dispatch.

### Voice AI Intent Engine
- `POST /voice/intent`, `POST /api/voice/intent`: NLP query parser returning intent, response text, matched facilities, and open slots.

### Healthcare Facilities & Emergency
- `GET /facilities`, `GET /api/facilities`: Ranks facilities by location, service, and emergency flags.
- `GET /emergency/facilities`, `GET /api/emergency/facilities`: Emergency casualty wards directory.
- `GET /facilities/{facility_id}/slots`: Doctor slot availability list.
- `POST /facilities/{facility_id}/slots`: Adds doctor slot.

### Provider & Emergency Dispatch
- `GET /provider/emergency_cases`: Returns active emergency triage queue.

### Appointments & Status Synchronization
- `POST /appointments`: Creates new appointment with Token `A-104`.
- `GET /appointments`: Returns appointment list (supports `facility_id`, `phone`, `status` filters).
- `PATCH /appointments/{id}/status`: Updates status (`confirmed`, `waiting`, `consultation`, `completed`, `cancelled`).

---

## 6. Database Schema (`backend/jansethu.db`)

SQLite database managed via SQLAlchemy ORM (`models.py`, `schemas.py`, `crud.py`).

- **`facilities`**: `id`, `name`, `name_hi`, `city`, `area`, `address`, `latitude`, `longitude`, `services`, `contact_phone`, `facility_type`.
- **`slots`**: `id`, `facility_id`, `date`, `time`, `available`, `doctor_name`, `department`.
- **`appointments`**: `id`, `facility_id`, `service`, `date`, `time`, `patient_name`, `phone`, `status`, `token_number`, `doctor_name`, `created_at`.

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
py -3 seed.py
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
3. **Browser Web Speech Dependency**: Web Speech recognition relies on browser APIs (Chrome/Edge/Safari); an inline text input fallback and Demo Voice Mode are provided on screen.

---
*JanSethu AI — Empowering Rural Healthcare Access in Maharashtra through Voice & Simple Telephony.*
