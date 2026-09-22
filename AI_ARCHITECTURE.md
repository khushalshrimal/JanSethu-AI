# JanSethu AI — AI & NLU Agent Architecture Specification

> **Phase 6 Delivery Architecture Document**  
> **Status**: PHASE 6 STATUS: COMPLETE (531 / 531 Pytest Tests Passing)  
> **Scope**: Natural Language Understanding (NLU), Spoken Voice & IVR Pipeline, Multi-lingual Conversational State Machine, Deterministic Safety Preemption, Action Router, Production Integration Provider Abstractions, Security Hardening, and Production Deployment Readiness.



---

## 1. System Architectural Overview

JanSethu AI implements a state-aware, multi-lingual AI agent architecture that translates unscripted natural human language (English, Hindi, Hinglish, Marathi) into structured healthcare intent and entity contracts.

```
                               ┌──────────────────────────────────────────────┐
                               │             USER INPUT (Text / Voice)        │
                               │  "Mujhe skin ka doctor chahiye Baramati mein"│
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │           SAFETY & EMERGENCY ENGINE          │
                               │  Scans for chest pain, breathing difficulty, │
                               │  accidents, severe bleeding, or 108 calls.    │
                               └──────────────┬────────────────┬──────────────┘
                                              │                │
                        [EMERGENCY DETECTED]  │                │  [NORMAL PATHWAY]
                                              │                │
                                              ▼                ▼
                     ┌───────────────────────────┐   ┌──────────────────────────────────────────┐
                     │ EMERGENCY DISPATCH PATH   │   │         LLM / NLU AGENT LAYER            │
                     │  High-priority response   │   │  Multi-Lingual Intent & Entity Extraction│
                     │  108 helpline guidance    │   │  Language Detection (HI, MR, EN)         │
                     │  Emergency ER & Ambulance │   │  Confidence & missing parameter analysis │
                     └───────────────────────────┘   └────────────────────┬─────────────────────┘
                                                                          │
                                                                          ▼
                                                     ┌──────────────────────────────────────────┐
                                                     │      STATEFUL CONVERSATION MANAGER       │
                                                     │  Accumulates turn memory across turns    │
                                                     │  Computes missing required entities      │
                                                     │  Dynamically asks targeted questions     │
                                                     └────────────────────┬─────────────────────┘
                                                                          │
                                                                [ALL ENTITIES PRESENT]
                                                                          │
                                                                          ▼
                                                     ┌──────────────────────────────────────────┐
                                                     │        CONTROLLED ACTION ROUTER          │
                                                     │  Dispatches 17 registered actions only   │
                                                     │  Validates parameters & logs to audit    │
                                                     └────────────────────┬─────────────────────┘
                                                                          │
                                                                          ▼
                                                     ┌──────────────────────────────────────────┐
                                                     │     VERIFIED DATABASE TOOL SERVICE       │
                                                     │  Executes parametrized SQL/ORM queries   │
                                                     │  Facilities, Doctors, Slots, Ambulances  │
                                                     └────────────────────┬─────────────────────┘
                                                                          │
                                                                          ▼
                                                     ┌──────────────────────────────────────────┐
                                                     │       NATURAL RESPONSE GENERATOR         │
                                                     │  Grounds response ONLY in DB results     │
                                                     │  Zero medical diagnoses / claims         │
                                                     │  Multi-lingual response generation       │
                                                     └──────────────────────────────────────────┘
```

---

## 2. Structured NLU Contracts & Schemas

All natural language inputs are parsed into language-neutral, strongly typed contracts defined in `app/schemas/nlu.py`.

### 2.1 Supported Intents (`NLUIntent`)

- **Core & Greeting**: `GENERAL_GREETING`, `PROVIDE_NAME`, `PROVIDE_LOCATION`, `LANGUAGE_CHANGE`, `THANK_YOU`, `GOODBYE`
- **Clinical & Search Queries**: `FIND_FACILITY`, `FIND_DOCTOR`, `FIND_SPECIALIST`, `CHECK_AVAILABILITY`, `OPD_SCHEDULE`, `SLOT_SEARCH`, `MEDICAL_HELP`, `SYMPTOM_REPORT`
- **Appointment Workflow**: `BOOK_APPOINTMENT`, `CONFIRM_APPOINTMENT`, `CANCEL_APPOINTMENT`, `RESCHEDULE_APPOINTMENT`, `MY_APPOINTMENTS`, `REFERRAL_LOOKUP`
- **Emergency & Ambulance**: `EMERGENCY`, `AMBULANCE_REQUEST`, `EMERGENCY_FACILITY_SEARCH`

### 2.2 Extracted Entities (`NLUEntities`)

| Category | Field Name | Description & Type | Examples |
|---|---|---|---|
| **Demographic** | `patient_name` | `Optional[str]` | `"Ramesh"`, `"Rahul"`, `"Priya"` |
| | `patient_relation` | `Optional[str]` | `"self"`, `"father"`, `"mother"`, `"child"` |
| **Clinical** | `specialty` | `Optional[str]` | `"Dermatology"`, `"Pediatrics"`, `"Orthopedics"`, `"Gynecology"`, `"ENT"`, `"Cardiology"`, `"Ophthalmology"`, `"Dentistry"`, `"General Medicine"` |
| | `symptoms` | `List[str]` | `["fever", "chest pain", "skin allergy"]` |
| **Facility/Doctor**| `facility_name` | `Optional[str]` | `"Baramati Hospital"`, `"PHC Indapur"` |
| | `facility_type` | `Optional[str]` | `"PHC"`, `"CHC"`, `"DISTRICT_HOSPITAL"`, `"PRIVATE_HOSPITAL"` |
| | `doctor_name` | `Optional[str]` | `"Dr. Rajesh Sharma"` |
| **Location** | `location` / `city`| `Optional[str]` | `"Baramati"`, `"Pune"`, `"Indapur"`, `"Satara"`, `"Solapur"`, `"Nashik"`, `"Kolhapur"`, `"Sangavi"` |
| | `pincode` | `Optional[str]` | `"413106"`, `"413102"` |
| **Temporal** | `date` | `Optional[str]` | `"today"`, `"tomorrow"`, `"day_after_tomorrow"` |
| | `time` / `time_period`| `Optional[str]` | `"10:30"`, `"16:00"`, `"morning"`, `"afternoon"`, `"evening"` |

---

## 3. Multi-Lingual Processing Architecture

JanSethu AI natively processes four language modalities without requiring manual language toggling or separate pipelines:

1. **English (EN)**: `"I need a skin doctor in Baramati tomorrow"`
2. **Hindi (HI)**: `"मुझे बारामती में त्वचा के डॉक्टर की जरूरत है"`
3. **Hinglish (HI)**: `"Mujhe Baramati mein skin ka doctor chahiye kal"`
4. **Marathi (MR)**: `"मला उद्या बारामतीत त्वचारोग तज्ज्ञ हवा आहे"`

All four expressions cleanly map to identical contracts:
- `intent`: `NLUIntent.FIND_SPECIALIST`
- `entities.specialty`: `"Dermatology"`
- `entities.location`: `"Baramati"`
- `entities.date`: `"tomorrow"`

---

## 4. Deterministic Safety Engine & Preemption

The `SafetyEngine` (`app/services/safety_engine.py`) operates as a **zero-latency deterministic firewall** prior to LLM/NLU processing.

### Emergency Signal Triggers

- **Severe Shortness of Breath**: `"saans nahi aa rahi"`, `"श्वास घेण्यास त्रास"`, `"can't breathe"`
- **Chest Pain / Cardiac Signals**: `"seene mein tez dard"`, `"छातीत तीव्र दुखणे"`, `"chest pain"`
- **Severe Bleeding**: `"bahut khoon beh raha hai"`, `"रक्तस्राव"`, `"heavy bleeding"`
- **Unconsciousness**: `"patient behosh ho gaya"`, `"जाणीव नसणे"`, `"unconscious"`
- **Accidents / Trauma**: `"road accident near bus stand"`, `"अपघात झाला आहे"`
- **Explicit 108 / Ambulance Calls**: `"108 ambulance bhejo"`, `"रुग्णवाहिका पाठवा"`

### Safety Guarantees

1. **Preemption**: Bypasses normal appointment booking or administrative flows immediately.
2. **Zero Medical Diagnoses**: The system NEVER provides medical diagnoses, drug prescriptions, or treatment plans.
3. **Escalation**: Directs user to call emergency 108 helpline and locates nearest emergency-capable facility from verified DB records.

---

## 5. Grounded Database Tool Execution

JanSethu AI enforces strict **zero hallucination** principles. The LLM agent is strictly forbidden from creating synthetic doctor names, clinic locations, or appointment slots.

### Verified Backend Tools (`HealthcareToolService`)

1. `search_facilities(...)`: Queries `Facility` model filtered by city, pincode, type, department, and emergency capabilities.
2. `search_doctors(...)`: Queries `Doctor` model filtered by department, facility, city, and specialty.
3. `get_doctor_slots(...)`: Fetches active, unbooked persistent OPD slots from `OPDSlot` table.
4. `book_appointment(...)`: Atomically reserves slot, updates `OPDSlot.is_booked=True`, generates `Appointment` record and referral ticket `referral_id="JS-2026-XXXXXX"`.
5. `search_ambulances(...)`: Queries real-time `Ambulance` model status (AVAILABLE, DISPATCHED) with driver details and contact numbers.

---

## 6. Stateful Conversation Manager & Dynamic Clarification

The `ConversationManager` (`app/services/conversation_manager.py`) maintains turn memory across session interactions:

- **Entity Merging**: Retains patient name, location, and preferred doctor across multi-turn dialogs.
- **Dynamic Parameter Prompting**: Computes missing required fields dynamically. If a user requests `"I need a dermatologist"`, the system identifies `missing_fields=["location"]` and asks ONLY for location. Once the user replies `"In Baramati"`, both entities are satisfied and DB tools run immediately.
- **Correction Handling**: Detects user corrections (e.g., `"No, not Pune, I meant Baramati"`) and safely overwrites previous state attributes.

---

## 7. Model Configuration & Fallback Rules

- **Deterministic Fallback Parser (`DeterministicNLUParser`)**: High-speed, offline regex and rule-based parser handling 100+ patterns across HI, MR, and EN.
- **External LLM Service (`LLMService`)**: Configured via `app/core/config.py` supporting:
  - **Ollama**: Local `llama3` / `qwen2.5` inference for offline rural deployments.
  - **OpenAI / Gemini API**: Cloud LLM API integrations when online connectivity is available.
- **Automatic Fallback Pipeline**: If an external LLM call fails or times out, the system automatically falls back to `DeterministicNLUParser` without interrupting the user conversation.
