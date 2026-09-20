# JanSethu AI 2.0 — Platform Architecture Document

---

## 🏗️ Architectural Overview

JanSethu AI 2.0 uses a **unified, multi-channel backend architecture** designed specifically for rural healthcare accessibility. Both access channels — **Basic Phone IVR** and **Smartphone PWA** — interface with the exact same FastAPI application server, business logic services, and PostgreSQL database.

```text
               JANSETHU AI 2.0 ARCHITECTURE
               ============================

       BASIC/KEYPAD PHONE                   SMARTPHONE
      (Voice / DTMF / SMS)                (React / PWA)
               │                                │
               ▼                                ▼
     Telephony Provider Layer          FastAPI REST API
  (Development / Exotel Adapter)       (JWT Auth + CORS)
               │                                │
               └────────────────┬───────────────┘
                                │
                                ▼
                   UNIFIED FASTAPI BACKEND
     ┌──────────────────────────┼──────────────────────────┐
     │                          │                          │
     ▼                          ▼                          ▼
Phone Session Service     Availability Engine     Appointment Service
 (CallSession State)      (Slot Generator)       (Lifecycle & Double-Booking)
     │                          │                          │
     └──────────────────────────┼──────────────────────────┘
                                │
                                ▼
                       DATABASE LAYER
           (PostgreSQL / SQLite + Alembic Migrations)
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
      Provider OPD Dashboard            Admin Operations Console
      (Queue & Consult State)           (Audit Logs & Telephony Monitor)
```

---

## 🔑 Core Architectural Principles

1. **Single Source of Truth**: There is no separate "phone backend" and "web backend". The `CallSession` state machine calls the same `AppointmentService` and `AvailabilityService` consumed by the PWA REST API.
2. **Provider-Neutral Abstraction**: `TelephonyProvider` and `SMSProvider` abstract base classes decouple business logic from third-party vendors. The system runs seamlessly on `DevelopmentTelephonyProvider` (Browser Phone Simulator) and `ExotelTelephonyProvider` (ExoML XML) via config-driven factories (`TELEPHONY_PROVIDER=exotel`).
3. **Double-Booking Protection**: Enforced at both application layer (`check_slot_availability`) and database layer (`UniqueConstraint("doctor_id", "appointment_date", "start_time", name="uq_doctor_date_time")`).
4. **Deterministic Emergency Handling**: Bypasses appointment queues immediately upon detecting emergency intent, providing 108 helpline info without diagnostic probing.
