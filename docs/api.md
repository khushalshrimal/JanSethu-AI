# JanSethu AI 2.0 API Specification

## Base URL
`/api/v1`

## Endpoints Summary

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Public customer registration.
- `POST /api/v1/auth/login`: Authenticate via phone_number & password. Returns JWT token.
- `GET /api/v1/auth/me`: Retrieve current user profile (requires Bearer token).
- `POST /api/v1/auth/logout`: Stateless logout logging.

### Health
- `GET /api/v1/health`: Public system status check.

### Facilities & Departments
- `GET /api/v1/facilities/`: Public search facilities.
- `GET /api/v1/facilities/{id}`: Public facility details.
- `POST /api/v1/facilities/`: **ADMIN ONLY** Create facility.
- `POST /api/v1/facilities/{id}/departments`: **ADMIN ONLY** Add department.

### Doctors & Availability
- `GET /api/v1/doctors/?facility_id={id}`: Public list doctors.
- `GET /api/v1/doctors/{id}`: Public doctor details.
- `POST /api/v1/doctors/`: **ADMIN ONLY** Create doctor.
- `POST /api/v1/doctors/{id}/availability`: **ADMIN / PROVIDER ONLY** Configure availability schedule.

### Appointments
- `POST /api/v1/appointments/`: Book appointment (authenticated user).
- `GET /api/v1/appointments/{id}`: Retrieve appointment. **Object-Level Authorization Enforced** (Customer can only view own appointment; Provider can only view assigned facility/doctor appointments; Admin can view any appointment).
