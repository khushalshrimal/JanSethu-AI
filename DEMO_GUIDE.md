# JanSethu AI 2.0 — SIH Grand Finale Master Demo Guide

**Last Updated**: September 21, 2026  
**System Status**: 100% Operational & Verified  
**Automated Backend Test Suite**: **331 / 331 Tests PASSING**

---

## 🚀 Quick Startup Commands

### 1. Start FastAPI Backend Server
```bash
cd backend
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. Start Vite React Frontend PWA
```bash
cd frontend
npm run dev
```
- **Hotline Phone Simulator**: [http://localhost:5174/phone-simulator](http://localhost:5174/phone-simulator)
- **My Appointments Dashboard**: [http://localhost:5174/my-appointments](http://localhost:5174/my-appointments)
- **Provider OPD Queue Dashboard**: [http://localhost:5174/provider/dashboard](http://localhost:5174/provider/dashboard)
- **Admin Console**: [http://localhost:5174/admin](http://localhost:5174/admin)

### 3. Run Automated Pytest Suite
```bash
cd backend
py -m pytest -v
```
*(All 331 tests pass in ~65 seconds)*

---

## 🔐 Verified Demo Accounts & Credentials

| Role | Phone / Email | Password | Access Channel |
| :--- | :--- | :--- | :--- |
| **Returning Patient** | `+919876543210` | N/A (Auto-recognized) | Phone Hotline & PWA |
| **New Patient (Auto-Reg)** | `+919999888877` | N/A (Auto-created) | Phone Hotline |
| **OPD Provider / Doctor** | `dr.sharma@baramatihosp.gov.in` | `DoctorPass123!` | Provider Queue Dashboard |
| **System Admin** | `admin@jansethu.gov.in` | `AdminPass123!` | Admin Console |

---

## 🎬 4 Master SIH Demonstration Scenarios

### Demo Flow A — Spoken Healthcare Discovery & Real Database Booking
1. Open **Phone Hotline Simulator** (`http://localhost:5174/phone-simulator`).
2. Click **[ CALL JANSETHU ]** with number `+919876543210`.
3. Speak or click quick hint: **"Mujhe fever hai."**
4. JanSethu asks for location. Speak or click: **"Malviya Nagar Jaipur"** (or pincode `302019`).
5. Select facility, doctor (**Dr. Amit Kulkarni**), and OPD time slot (**11:00 AM**).
6. Confirm booking -> JanSethu speaks and displays real Referral Code: **`JAN-REF-2026-XXXX`** / **`JS-2026-XXXXXX`**.
7. Open **My Appointments** (`http://localhost:5174/my-appointments`).
8. **Verify**: The appointment appears live in database records with matching referral code and status `CONFIRMED`.

---

### Demo Flow B — Conversational Barge-In (Speech Interruption)
1. Start a call on the **Phone Hotline Simulator**.
2. While assistant TTS is speaking prompt (*"Namaste, JanSethu mein aapka swagat hai..."*), speak out loud or click **[ ⚡ Interrupt ]**.
3. **Observe**:
   - Assistant speech halts instantly (`speechSynthesis.cancel()`).
   - Call phase status flashes `⚡ INTERRUPTED` -> `🗣️ USER_SPEAKING`.
   - Stale TTS callbacks are invalidated and user speech transcript is processed seamlessly.

---

### Demo Flow C — Emergency Safety Override & Location Capture
1. Start a call on the **Phone Hotline Simulator**.
2. Speak or click quick hint: **"Mujhe saans lene mein bahut dikkat ho rahi hai."** (or *"Seene mein bahut tez dard hai"*).
3. **Observe**:
   - Safety Engine activates `HIGH_CONFIDENCE_EMERGENCY` level with highest priority.
   - Normal healthcare booking flows are preempted (no appointment created).
   - Prompt requests location if missing: **"32 Prem Nagar Jaipur"**.
   - Phone screen displays live **Emergency Panel**:
     - 🚨 `EMERGENCY OVERRIDE ACTIVATED`
     - 📍 Location: `32 Prem Nagar, Jaipur`
     - 🆘 Assistance: `SIMULATION`
     - 📋 Request ID: **`AMB-MOCK-XXXXX`**
   - Assistant prompt explicitly states that ambulance connection is simulated in prototype mode and advises dialing 108 for real emergencies.

---

### Demo Flow D — Natural / Unpredictable Queries & Topic Switch
1. Ask: *"Hospital kitna door hai?"* or *"Hospital A mein Dr Lakshya available hain?"* -> Queries real DB schedule.
2. Ask: *"Mera referral ID kya hai?"* -> Queries user's active appointment.
3. Speak: *"Galti se emergency bola tha"* -> Resets active emergency status cleanly while preserving history.

---

## 🧩 Real vs Simulated (Mock) Transparency Matrix

| Component | Status | Operational Details |
| :--- | :--- | :--- |
| **FastAPI Backend Services** | REAL ✓ | 100% real Python FastAPI backend with ORM models. |
| **Database & Persistence** | REAL ✓ | SQLite/PostgreSQL database storing Users, Patients, Facilities, Doctors, Slots, Appointments, Audit Logs, and Notifications. |
| **Multi-Lingual NLU & Safety Engine**| REAL ✓ | Deterministic safety classifier and multi-lingual NLU parser (Hindi, Hinglish, Marathi, English). |
| **Stateful Conversation Manager** | REAL ✓ | Multi-turn entity merging, correction detection, and topic switching. |
| **Web Speech Voice Engine** | REAL ✓ | Web Speech API (`SpeechSynthesisUtterance` + `webkitSpeechRecognition`) with instant barge-in cancellation. |
| **PWA & Provider Queue Sync** | REAL ✓ | Live appointment sync between Phone Hotline, PWA `/my-appointments`, and `/provider` queue. |
| **SMS Telephony Integration** | SIMULATED (MOCK) ℹ️ | `DevelopmentSMSProvider` logs dispatched SMS notifications to console/inspectors (`[SIMULATED SMS]`). |
| **Ambulance Dispatch Integration** | SIMULATED (MOCK) ℹ️ | Generates mock request ID (`AMB-MOCK-XXXXX`) and displays simulated dispatch status. |

---

## 🔄 Demo Session Reset Procedure

To reset demo state during live presentations without losing database records:
1. In `PhoneSimulator.jsx`, click **[ END CALL ]**.
2. Or invoke `ConversationManager.clear_all_sessions()` via test helper.
3. Refresh browser tab to start a clean voice session.
