# JANSETHU AI - PROJECT STATE

**Last Updated:** 2026-09-16  
**Current Phase:** Phase 2 (FastAPI + Database) Completed  
**Status:** Backend Database & REST API Active & Fully Connected to React PWA

---

## 1. Project Overview
JanSethu AI is a voice-first healthcare access platform designed for underserved and low-literacy users. It allows smartphone PWA users and feature phone callers to discover healthcare facilities, check slot availability, request appointments, and access emergency services.

> **CRITICAL ARCHITECTURAL RULE:** The SQLite database is the prototype's source of truth. AI components must NEVER invent hospital availability, doctor slots, or facility info.

---

## 2. Phase Tracker
| Phase | Title | Status | Description |
|-------|-------|--------|-------------|
| **Phase 1** | Foundation & PWA UI Screens | ✅ COMPLETED | Vite+React, Tailwind CSS, PWA config, 8 Core Screens with responsive mobile-first layout |
| **Phase 2** | FastAPI + Database Backend | ✅ COMPLETED | SQLite DB (`jansethu.db`), SQLAlchemy models (`facilities`, `slots`, `appointments`), REST APIs, seed data, frontend API wiring |
| **Phase 3** | Voice Assistant & Intent Engine | ⏳ NEXT | Web Speech API voice capture, intent parser (`find_facility`, `check_availability`, etc.), missing info dialog |
| **Phase 4** | Facility Discovery & Map View | 🔲 PENDING | Leaflet / OpenStreetMap integration, GPS location filter, interactive facility details |
| **Phase 5** | Provider Dashboard Workflow | 🔲 PENDING | Real-time appointment management, confirmation/rejection workflow, slot creation |
| **Phase 6** | Telephony / Voice Provider Integration | 🔲 PENDING | Telephony webhook handler for basic keypad phone voice calls |

---

## 3. Completed Work (Phase 2 FastAPI + Database)
- [x] Configured SQLite database with SQLAlchemy (`backend/database.py`).
- [x] Created database schema models (`Facility`, `Slot`, `Appointment`) in `backend/models.py`.
- [x] Implemented Pydantic validation schemas (`backend/schemas.py`).
- [x] Implemented query CRUD layer (`backend/crud.py`).
- [x] Developed database seed script (`backend/seed.py`) with 5 realistic DEMO facilities (District Hospital, PHCs, CHCs, Mobile Van) and doctor slots in Jaipur & Delhi.
- [x] Developed FastAPI backend application (`backend/main.py`) with CORS middleware.
- [x] Implemented & verified REST API endpoints:
  - `GET /facilities` (and `/api/facilities`): List facilities with city, area, service, search query filters.
  - `GET /facilities/{id}` (and `/api/facilities/{id}`): Facility detail by ID.
  - `GET /facilities/{id}/slots` (and `/api/facilities/{id}/slots`): Available doctor/OPD slots for a facility.
  - `POST /appointments` (and `/api/appointments`): Create appointment request and update slot availability.
  - `GET /appointments/{id}` (and `/api/appointments/{id}`): Get single appointment request by ID.
  - `GET /appointments` (and `/api/appointments`): List appointments for provider tracking.
  - `PATCH /appointments/{id}/status` (and `/api/appointments/{id}/status`): Status updates (`pending`, `confirmed`, `rejected`, `rescheduled`).
  - `GET /emergency` (and `/api/emergency`): National emergency helplines & advice.
- [x] Connected React PWA screens to backend APIs (`FacilityResultsScreen`, `SlotSelectionScreen`, `ConfirmationScreen`, `ProviderDashboardScreen`) with graceful mock fallback if offline.
- [x] Verified unit tests (`backend/test_backend.py`) — `All Phase 2 Backend API Tests Passed Cleanly!`.

---

## 4. Database Schema Structure (`jansethu.db`)

### 1. `facilities` Table
- `id`: INTEGER PRIMARY KEY
- `name`: VARCHAR (Hospital / Centre Name in English)
- `name_hi`: VARCHAR (Hindi Name)
- `city`: VARCHAR (City/District)
- `area`: VARCHAR (Area/Locality)
- `address`: TEXT (Full Address)
- `latitude`: FLOAT (GPS Latitude)
- `longitude`: FLOAT (GPS Longitude)
- `services`: TEXT (CSV string of services offered)
- `contact_phone`: VARCHAR (Contact Number)
- `facility_type`: VARCHAR (Hospital, PHC, CHC, Mobile Clinic)

### 2. `slots` Table
- `id`: INTEGER PRIMARY KEY
- `facility_id`: INTEGER FOREIGN KEY -> `facilities.id`
- `date`: VARCHAR (YYYY-MM-DD or 'Today', 'Tomorrow')
- `time`: VARCHAR (HH:MM AM/PM)
- `available`: BOOLEAN (True = Open, False = Booked)
- `doctor_name`: VARCHAR (Assigned Doctor)
- `department`: VARCHAR (Department/OPD)

### 3. `appointments` Table
- `id`: INTEGER PRIMARY KEY
- `facility_id`: INTEGER FOREIGN KEY -> `facilities.id`
- `service`: VARCHAR (Requested Service/OPD)
- `date`: VARCHAR (Appointment Date)
- `time`: VARCHAR (Appointment Time)
- `patient_name`: VARCHAR (Patient Name)
- `phone`: VARCHAR (Patient Mobile Phone)
- `status`: VARCHAR ('pending', 'confirmed', 'rejected', 'rescheduled')
- `created_at`: DATETIME

---

## 5. Created / Modified Files Map
```
JanSethu AI/
├── PROJECT_STATE.md
├── backend/
│   ├── main.py             # FastAPI routes for /facilities, /slots, /appointments
│   ├── database.py         # SQLAlchemy engine & SQLite session
│   ├── models.py           # Facility, Slot, Appointment ORM models
│   ├── schemas.py          # Pydantic schemas
│   ├── crud.py             # Database query operations
│   ├── seed.py             # Demo data generator
│   ├── requirements.txt    # FastAPI, Uvicorn, SQLAlchemy, Pydantic, Pytest
│   └── test_backend.py     # Backend API unit tests
└── frontend/
    ├── package.json        # Dependencies (React, Vite, Tailwind, Lucide, Axios)
    ├── vite.config.js      # Vite dev server with /api proxy
    ├── tailwind.config.js  # Custom theme
    ├── postcss.config.js   # PostCSS config
    ├── index.html          # PWA container
    ├── public/
    │   ├── manifest.json   # Web App Manifest
    │   └── sw.js           # PWA Service Worker
    └── src/
        ├── main.jsx        # Entry point
        ├── index.css       # Tailwind directives
        ├── mockData.js     # Static/mock fallback data
        ├── api.js          # Connected API client with fallback
        ├── App.jsx         # App shell & router
        ├── components/
        │   ├── Header.jsx
        │   ├── Navigation.jsx
        │   ├── DemoBadge.jsx
        │   └── HealthStatus.jsx
        └── screens/
            ├── HomeScreen.jsx
            ├── VoiceAssistantScreen.jsx
            ├── SearchScreen.jsx
            ├── FacilityResultsScreen.jsx
            ├── SlotSelectionScreen.jsx
            ├── ConfirmationScreen.jsx
            ├── ProviderDashboardScreen.jsx
            └── EmergencyScreen.jsx
```

---

## 6. System Status Matrix
- **Database Status:** ✅ SQLite (`backend/jansethu.db`) active & seeded with DEMO data.
- **Backend APIs:** ✅ All endpoints functional and verified (`test_backend.py` passed with exit code 0).
- **Frontend Integration:** ✅ Connected React screens fetch live data from FastAPI backend with fallback.
- **PWA Status:** ✅ Service Worker & Manifest configured.

---

## 7. Exact Commands to Run

### Run Backend API (FastAPI + Uvicorn):
```bash
cd backend
py -3 -m uvicorn main:app --reload --port 8000
```
Interactive Swagger API docs: `http://localhost:8000/docs`

### Re-seed SQLite Database:
```bash
cd backend
py -3 seed.py
```

### Run Backend Unit Tests:
```bash
cd backend
py -3 test_backend.py
```

### Run Frontend Development Server:
```bash
cd frontend
npm run dev
```
URL: `http://localhost:3000`

### Build Frontend Production Bundle:
```bash
cd frontend
npm run build
```

---

## 8. Next Phase (Phase 3)
**Phase 3: Voice Assistant & Real Intent Engine**
- Browser Web Speech API (`SpeechRecognition` & `SpeechSynthesis`).
- Intent parsing (`find_facility`, `check_availability`, `appointment_request`, `facility_information`, `emergency_help`, `fallback`).
- Conversational state manager for missing parameters (City, Service, Date).

*Note: Development will proceed to Phase 3 upon explicit user instruction.*
