# JanSethu AI — Database Schema Documentation (Phase 2 Healthcare Foundation Upgrade)

**Document Version**: 2.0  
**Updated Date**: September 22, 2026  
**Status**: Production / Synthetic Healthcare Foundation  
**Database System**: SQLite / PostgreSQL compatible SQLAlchemy 2.0 ORM  

---

## 1. Overview & Relational Architecture

The JanSethu AI database foundation is designed to represent a realistic rural/semi-urban healthcare ecosystem across Maharashtra, India (focusing on Baramati, Pune, Satara, Solapur, Nashik, Kolhapur, and staging locations).

The relational schema supports:
- **Hierarchical Healthcare Discovery**: Facilities -> Departments -> Doctors -> persistent 14-day 30-minute OPD Slots.
- **Facility Capabilities & Emergency Infrastructure**: Multi-tier facilities (PHC, CHC, Sub-Center, District Hospital, Medical College, Private Hospital) with emergency levels, ICU support, cardiac, pediatric, trauma support, 24x7 status, and ambulance availability.
- **Facility Services Mapping**: Explicit mapping of specialized clinical and administrative services (`FacilityService`) provided by each healthcare facility.
- **Ambulance Dispatch Infrastructure**: Vehicle fleet tracking (`Ambulance`) with location coordinates, ambulance types (`108_BASIC`, `108_ADVANCED`, `PATIENT_TRANSPORT`), operational status (`AVAILABLE`, `DISPATCHED`, `MAINTENANCE`), and phone numbers.
- **Persistent OPD Slot Management**: Pre-generated, persistent 30-minute appointment slots (`AppointmentSlot`) spanning 14 days into the future, supporting slot status transitions (`AVAILABLE`, `BOOKED`, `BLOCKED`, `RESERVED`, `CANCELLED`).
- **Unified Cross-Channel Appointments**: Shared appointment store supporting PWA, Telephony (DTMF/Voice), Telemedicine, and Walk-in booking channels with strict double-booking prevention.

---

## 2. ASCII Entity-Relationship Diagram

```
+------------------+         +----------------------+         +---------------------+
|      Users       | 1 --- 1 |   PatientProfile     | 1 --- * |    Appointments     |
+------------------+         +----------------------+         +---------------------+
| id (PK)          |         | id (PK)              |         | id (PK)             |
| phone_number     |         | user_id (FK)         |         | confirmation_code   |
| email            |         | district             |         | patient_id (FK)     |
| role             |         | state                |         | doctor_id (FK)      |
+------------------+         +----------------------+         | facility_id (FK)    |
                                                              | department_id (FK)  |
                                                              | slot_id (FK)        |
+------------------+         +----------------------+         | status              |
|    Facilities    | 1 --- * |     Departments      |         | booking_channel     |
+------------------+         +----------------------+         +---------------------+
| id (PK)          |         | id (PK)              |                    |
| name             |         | facility_id (FK)     |                    | 1
| facility_type    |         | name                 |                    |
| area, city       |         | code                 |                    v 1
| district, state  |         | status               |         +---------------------+
| emergency_level  |         +----------------------+         |   SMSNotifications   |
| icu_available    |                    | 1                   +---------------------+
| trauma_support   |                    |                     | id (PK)             |
| ambulance_avail  |                    v *                   | appointment_id (FK) |
+------------------+         +----------------------+         | recipient_phone     |
     | 1       | 1           |       Doctors        |         | status              |
     |         |             +----------------------+         +---------------------+
     v *       v *           | id (PK)              |
+----------+ +------------+  | facility_id (FK)     |
| Facility | | Ambulances |  | department_id (FK)   |         +---------------------+
| Service  | +------------+  | name, qualification  | 1 --- * |  AppointmentSlots   |
+----------+ | id (PK)    |  | experience_years     |         +---------------------+
| id (PK)  | | fac_id(FK) |  | status               |         | id (PK)             |
| fac_id   | | reg_no     |  +----------------------+         | doctor_id (FK)      |
| service  | | type,status|             | 1                   | facility_id (FK)    |
+----------+ +------------+             |                     | slot_date, time     |
                                        v *                   | status              |
                             +----------------------+         +---------------------+
                             | DoctorAvailability   |
                             +----------------------+
                             | id (PK)              |
                             | doctor_id (FK)       |
                             | day_of_week          |
                             | start_time, end_time |
                             +----------------------+
```

---

## 3. Table Specifications & Columns

### 3.1 `facilities`
| Column Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto | Primary Key |
| `name` | String(150) | Not Null, Index | Facility official name |
| `facility_type` | Enum / String | Not Null | `PHC`, `CHC`, `SUB_CENTER`, `DISTRICT_HOSPITAL`, `MEDICAL_COLLEGE`, `PRIVATE_HOSPITAL` |
| `address` | String(255) | Not Null | Physical street address |
| `village` | String(100) | Nullable, Index | Village name |
| `area` | String(100) | Nullable | Locality/area |
| `city` | String(100) | Nullable | City |
| `district` | String(100) | Not Null, Index | District (e.g. Pune, Satara) |
| `state` | String(100) | Not Null, Default 'Maharashtra' | State |
| `pincode` | String(10) | Not Null, Index | 6-digit postal index code |
| `latitude` | Float | Nullable | GPS latitude coordinate |
| `longitude` | Float | Nullable | GPS longitude coordinate |
| `phone_number` | String(20) | Nullable | Facility contact phone |
| `email` | String(100) | Nullable | Facility email address |
| `is_24x7` | Boolean | Default True | 24x7 operational flag |
| `ambulance_available` | Boolean | Default True | Onsite/linked ambulance flag |
| `telemedicine_available` | Boolean | Default True | Tele-consultation capability flag |
| `emergency_level` | String(20) | Default 'BASIC' | Emergency tier: `BASIC`, `COMPREHENSIVE`, `ADVANCED_TRAUMA` |
| `icu_available` | Boolean | Default False | Intensive Care Unit capability |
| `trauma_support` | Boolean | Default False | Trauma care capability |
| `cardiac_support` | Boolean | Default False | Cardiac emergency capability |
| `pediatric_emergency` | Boolean | Default False | Pediatric emergency care capability |
| `status` | Enum / String | Default 'ACTIVE' | `ACTIVE`, `INACTIVE`, `TEMPORARILY_UNAVAILABLE` |
| `is_active` | Boolean | Default True | Active flag |
| `is_demo_data` | Boolean | Default True | Synthetic dataset marker |

---

### 3.2 `departments`
| Column Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto | Primary Key |
| `facility_id` | Integer | FK(`facilities.id`), Not Null | Parent facility |
| `name` | String(100) | Not Null, Index | Department name (e.g. General Medicine, Pediatrics) |
| `code` | String(20) | Nullable | Specialty code |
| `description` | String(255) | Nullable | Specialty scope description |
| `status` | Enum / String | Default 'ACTIVE' | `ACTIVE`, `INACTIVE`, `TEMPORARILY_UNAVAILABLE` |
| `is_active` | Boolean | Default True | Active status flag |

---

### 3.3 `doctors`
| Column Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto | Primary Key |
| `facility_id` | Integer | FK(`facilities.id`), Not Null | Primary facility affiliation |
| `department_id` | Integer | FK(`departments.id`), Not Null | Clinical specialty department |
| `name` | String(120) | Not Null, Index | Doctor full name |
| `qualification` | String(100) | Not Null | Medical degree (MBBS, MD, MS) |
| `specialization` | String(100) | Not Null | Primary clinical specialty |
| `experience_years` | Integer | Default 5 | Clinical experience in years |
| `languages` | String(100) | Default 'Hindi, Marathi, English' | Languages spoken |
| `gender` | String(10) | Default 'Male' | Gender |
| `consultation_fee` | Float | Default 0.0 | OPD fee in INR (0.0 for public PHC/CHC) |
| `slot_duration_minutes` | Integer | Default 30 | OPD slot interval in minutes |
| `status` | Enum / String | Default 'ACTIVE' | `ACTIVE`, `INACTIVE`, `ON_LEAVE` |
| `is_active` | Boolean | Default True | Active status flag |

---

### 3.4 `appointment_slots`
| Column Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto | Primary Key |
| `doctor_id` | Integer | FK(`doctors.id`), Not Null | Doctor offering slot |
| `facility_id` | Integer | FK(`facilities.id`), Not Null | Facility location |
| `department_id` | Integer | FK(`departments.id`), Not Null | Department |
| `slot_date` | Date | Not Null, Index | Date of OPD slot |
| `start_time` | Time | Not Null | Slot start time |
| `end_time` | Time | Not Null | Slot end time |
| `status` | Enum / String | Default 'AVAILABLE', Index | `AVAILABLE`, `BOOKED`, `BLOCKED`, `RESERVED`, `CANCELLED` |
| `max_capacity` | Integer | Default 1 | Capacity per slot |
| `booked_count` | Integer | Default 0 | Current booking count |

---

### 3.5 `ambulances`
| Column Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto | Primary Key |
| `facility_id` | Integer | FK(`facilities.id`), Not Null | Base station facility |
| `registration_number` | String(30) | Unique, Not Null | Vehicle registration (e.g. MH-12-PA-1001) |
| `ambulance_type` | Enum / String | Default '108_BASIC' | `108_BASIC`, `108_ADVANCED`, `PATIENT_TRANSPORT` |
| `status` | Enum / String | Default 'AVAILABLE', Index | `AVAILABLE`, `DISPATCHED`, `MAINTENANCE`, `OFF_DUTY` |
| `contact_number` | String(20) | Not Null | Driver/dispatch phone |
| `current_latitude` | Float | Nullable | Live GPS latitude |
| `current_longitude` | Float | Nullable | Live GPS longitude |
| `is_24x7` | Boolean | Default True | 24x7 service flag |

---

### 3.6 `facility_services`
| Column Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto | Primary Key |
| `facility_id` | Integer | FK(`facilities.id`), Not Null | Target facility |
| `service_name` | String(100) | Not Null, Index | Service title (e.g. Immunization, OPD, Emergency 108) |
| `service_code` | String(50) | Nullable | Standard service classification code |
| `description` | String(255) | Nullable | Service description |
| `is_available` | Boolean | Default True | Availability flag |

---

## 4. Key Synthetic Dataset Metrics

- **Total Healthcare Facilities**: 29 active facilities (PHCs, CHCs, Sub-Centers, District Hospitals, Medical Colleges, Private Hospitals).
- **Total Departments**: 412 active specialty departments.
- **Total Doctors**: 417 qualified medical doctors across 17 clinical specialties.
- **Total Persistent Appointment Slots**: 4,480 30-minute OPD slots pre-generated across a rolling 14-day horizon.
- **Total Ambulances**: 20 active 108 Emergency and Patient Transport ambulances with registration numbers and dispatch contacts.

---

## 5. Representative SQL Queries

### 5.1 Nearby Emergency Facility & Ambulance Discovery
```sql
SELECT f.name, f.facility_type, f.district, f.phone_number, a.registration_number, a.contact_number, a.status
FROM facilities f
JOIN ambulances a ON a.facility_id = f.id
WHERE f.district = 'Pune' AND f.emergency_level != 'NONE' AND a.status = 'AVAILABLE'
ORDER BY f.id ASC;
```

### 5.2 Persistent OPD Slot Search for Doctor Availability
```sql
SELECT d.name AS doctor_name, d.specialization, s.slot_date, s.start_time, s.end_time, s.status
FROM appointment_slots s
JOIN doctors d ON d.id = s.doctor_id
WHERE s.facility_id = 1 AND s.department_id = 1 AND s.slot_date >= CURRENT_DATE AND s.status = 'AVAILABLE'
ORDER BY s.slot_date ASC, s.start_time ASC
LIMIT 10;
```
