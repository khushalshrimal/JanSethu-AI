# JANSETHU AI — SIH DEMONSTRATION RUNBOOK
**Smart India Hackathon (SIH) Jury Demonstration Guide**

---

## 1. Zero-Cost Demo Setup Instructions

To launch the complete JanSethu AI platform in offline zero-cost demo mode (with no paid cloud keys required):

### Step 1: Environment Preparation
Ensure your `.env` or system environment has the following parameters set:
```ini
APP_ENV=development
SECRET_KEY=demo_secret_key_jansethu_2026
TELEPHONY_PROVIDER=development
STT_PROVIDER=mock
TTS_PROVIDER=mock
SMS_PROVIDER=development
LOCATION_PROVIDER=mock
LLM_PROVIDER=development
DATABASE_URL=sqlite:///./jansethu_demo.db
```

### Step 2: Seed Healthcare Database
Run the seed script from the `backend/` folder to populate synthetic hospitals, doctors, and OPD schedules:
```bash
cd backend
py -m scripts.seed --force
```

### Step 3: Start Backend API & Voice Simulator
Launch the FastAPI application:
```bash
cd backend
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify the server is running by opening:
- API Documentation: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### Step 4: Launch Web Frontend
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in Google Chrome or Edge.

---

## 2. Step-by-Step SIH Live Demonstration Script

### Demo Phase 1: Rural Telephony / IVR Voice Call Simulation
1. Navigate to `http://127.0.0.1:8000/docs` or launch the interactive CLI simulator.
2. Select **Simulate Inbound Call** (`/api/v1/telephony/simulate-incoming-call`).
3. Speak / Type: *"Mujhe Baramati me chest pain ke liye doctor dikhana hai"* (Hindi).
4. Point out to Jury:
   - Automated language recognition (Hindi detected).
   - Instant emergency safety audit run before LLM processing.
   - Doctor search executed on relational database for Cardiology in Baramati.

### Demo Phase 2: Multi-turn Natural Context & Correction
1. Speak / Type: *"Nahi, Baramati nahi, Pune me chahiye"* (User correction).
2. Point out to Jury:
   - System seamlessly updates target location to **Pune** without asking the user to re-type symptoms.
   - Returns top matched government / private hospitals in Pune.

### Demo Phase 3: Emergency Override Protocol (108 Rescue)
1. Speak / Type: *"Bahut tez sine me dard hai, behosh ho raha hai"* (Severe emergency prompt).
2. Point out to Jury:
   - System immediately interrupts OPD booking flow.
   - Displays prominent **EMERGENCY OVERRIDE** banner.
   - Emits simulated 108 Emergency Ambulance dispatch request and displays nearest emergency trauma centre contact details.

### Demo Phase 4: Appointment Confirmation & Simulated SMS Delivery
1. Select an available doctor slot (e.g., Dr. Phase7 Cardiologist, 10:30 AM).
2. Enter patient details: **Rahul Sharma**, `9876543210`.
3. System responds with unique Confirmation Ticket Code (e.g., `JS-2026-X78A9B`).
4. Check simulated SMS output log showing instant confirmation dispatch to the user's phone.

---

## 3. Key Differentiators to Highlight for SIH Evaluators

1. **Inclusive Access**: Accessible via plain feature phone calls (voice/IVR), SMS, WhatsApp, or Progressive Web App (PWA).
2. **Language Sovereignty**: First-class support for rural Marathi, Hindi, Hinglish, and English code-switching.
3. **Deterministic Safety Layer**: Critical health safety checks run deterministically before LLM call, guaranteeing zero missed emergencies and zero false diagnoses.
4. **Offline Resilience**: Runs completely local during connectivity dropouts using embedded SQLite and local fallback models.
5. **Real-time Atomic Scheduling**: No double-booking vulnerabilities, ACID transactional guarantees on slot reservations.
