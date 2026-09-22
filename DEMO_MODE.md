# JanSethu AI — Zero-Cost Local Demonstration Guide (SIH Prototype)

JanSethu AI is designed to run **100% locally with zero paid external API dependencies**. All telephony, speech-to-text, text-to-speech, SMS notifications, geocoding, and LLM NLU features run using verified local mock adapters.

---

## 1. Quick Start Commands

### Backend Startup (Terminal 1)
```bash
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
py -m app.config.check_config
uvicorn app.main:app --reload --port 8000
```

### Frontend Startup (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## 2. Interactive Demo Walkthrough Scenarios

### Scenario A: Hands-Free Voice Simulator OPD Booking
1. Navigate to `/phone-simulator`.
2. Click **Start Call** or **Send Voice**.
3. Speak in Hindi: `"Namaste, mera naam Ramesh hai, mujhe doctor ko dikhana hai"`.
4. The system registers your phone caller identity, prompts for facility, accepts `"Baramati Sub-District Hospital"`, selects doctor, and issues a verified appointment ticket (`JS-2026-XXXXXX`).

### Scenario B: 108 Emergency Preemption
1. Open `/phone-simulator` or symptom checker.
2. Speak/Type: `"mujhe saans lene mein bohot takleef ho rahi hai emergency 108"`.
3. SafetyEngine triggers immediate priority override, requests location (`"Baramati"`), searches emergency facilities & ambulances, and issues a simulated dispatch code (`EMG-2026-XXXXXX`).

### Scenario C: Provider OPD Queue Management
1. Login as Provider (`provider@jansethu.gov.in` / `Provider@123`).
2. Open `/provider/dashboard`.
3. View real-time OPD patient queue, check-in tokens, and update consultation status (`IN_CONSULTATION`, `COMPLETED`, `NO_SHOW`).

---

## 3. Demo Readiness Audit Command

Verify backend readiness at any time:
```bash
py -m app.config.check_config
```
Or via HTTP GET request:
`http://localhost:8000/health/demo-readiness`
