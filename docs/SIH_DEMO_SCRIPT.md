# JanSethu AI 2.0 — SIH Grand Finale Demo Script (2–3 Minute Blueprint)

---

## 🎯 Demonstration Objective
Demonstrate how **JanSethu AI 2.0** bridges the rural healthcare access divide in India by providing a unified healthcare booking platform accessible via **Basic/Keypad Phone (Voice + DTMF)** and **Smartphone PWA**, powered by a single real database backend.

---

## ⏱️ Step-by-Step Presenter Timeline (2 min 40 sec)

### 0:00 – 0:20 | The Problem
> **Presenter Action**: Stand in front of screen showing JanSethu Logo / Landing Page.  
> **Presenter Script**:  
> *"Over 500 million rural citizens in India do not own smartphones or reliable internet. Current digital health initiatives assume everyone has an app. JanSethu AI 2.0 provides healthcare access over basic keypad phones using voice, keypad DTMF fallback, and SMS, while providing a smartphone PWA for users who have internet. Both channels connect to the exact same backend and database."*

---

### 0:20 – 0:50 | Phone Channel Access & Voice NLU
> **Presenter Action**: Navigate to `http://localhost:5173/phone-simulator` (**Development Phone Simulator**).  
> **Presenter Action**: Click **[ START CALL ]** with number `+91-9876543210` (Rahul Pawar).  
> **System Plays Audio**: *"Namaste, JanSethu mein aapka swagat hai."*  
> **Presenter Action**: Press `1` or select **Hindi**.  
> **Presenter Action**: Speak or type voice utterance: **"Mujhe doctor ko dikhana hai."**  
> **Presenter Script**:  
> *"Notice how the system detects the user's intent as `BOOK_APPOINTMENT` in Hindi using our natural language engine, without requiring a smartphone or app download."*

---

### 0:50 – 1:20 | Real Appointment Booking
> **Presenter Action**: Follow voice prompts to select options:
> - Facility: **Baramati Government Hospital** (Press `1` or speak)
> - Department: **General Medicine** (Press `1` or speak)
> - Doctor: **Dr. Amit Kulkarni** (Press `1` or speak)
> - Date & Slot: Select next available OPD slot
> - Confirmation: Confirm booking  
> **System Screen Displays**: Appointment Confirmed ticket code (e.g. `JS-2026-XXXX`).  
> **Presenter Script**:  
> *"The booking is not a hardcoded demo screen. The appointment was generated live in our database with double-booking constraint protection and assigned a real ticket code."*

---

### 1:20 – 1:45 | Cross-Channel Data Synchronization
> **Presenter Action**: Open Customer PWA (`http://localhost:5173/my-appointments`) logged in as Rahul Pawar (`+91-9876543210`).  
> **Presenter Action**: Show the newly created appointment listed with matching confirmation code.  
> **Presenter Action**: Switch to Provider OPD Console (`http://localhost:5173/provider`) logged in as `dr.sharma@baramatihosp.gov.in`. Show patient queue.  
> **Presenter Action**: Switch to Admin Console (`http://localhost:5173/admin`) showing system audit logs.  
> **Presenter Script**:  
> *"The critical architectural innovation is that the basic phone IVR and smartphone PWA are not separate systems. They hit the exact same FastAPI backend, availability engine, and PostgreSQL database."*

---

### 1:45 – 2:05 | Keypad DTMF Fallback (No Speech Required)
> **Presenter Action**: Return to `/phone-simulator`, start a new call.  
> **Presenter Action**: Press `1` (Hindi) -> Press `1` (Book Appointment).  
> **Presenter Script**:  
> *"For noisy rural environments or users with speech impairments, the system provides full keypad DTMF navigation. No speech recognition is required."*

---

### 2:05 – 2:25 | Emergency Handling (Zero Medical Probing)
> **Presenter Action**: Start another call on `/phone-simulator`, select Hindi.  
> **Presenter Action**: Speak/type: **"Mujhe emergency help chahiye."**  
> **System Output**: Enters `EMERGENCY` state immediately, playing 108 Ambulance and Casualty helpline info.  
> **Presenter Script**:  
> *"Emergency handling is deterministic. The system immediately provides 108 ambulance dispatch information and casualty desk contacts without attempting medical diagnosis or asking unnecessary questions."*

---

### 2:25 – 2:40 | Closing Statement
> **Presenter Script**:  
> *"JanSethu AI 2.0 connects rural citizens to healthcare using the technology they already have in their pocket — basic phones, voice, keypad digits, or smartphones. Thank you!"*

---

## 🛡️ Backup & Fallback Instructions for Presenters

| Failure Scenario | Immediate Presenter Action |
| :--- | :--- |
| **Browser Speech Recognition Fails** | Type the exact sentence into the voice utterance text field: `"Mujhe doctor ko dikhana hai"` or `"मला डॉक्टरांना भेटायचे आहे."` |
| **Natural Language Parsing Fails** | Use DTMF keypad buttons directly (`1` -> `1` -> `1`). |
| **Target Slot Already Booked** | Select the next available 30-min OPD slot from the generated list. |
| **Database State Inconsistent** | Execute safe demo reset: `POST http://localhost:8000/api/v1/admin/demo-reset` (Admin token required). |
