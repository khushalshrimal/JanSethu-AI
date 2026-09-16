from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, crud
from database import engine, get_db, Base
import seed

# Create database tables automatically if not present
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JanSethu AI Healthcare Backend",
    description="Voice-first healthcare access platform backend API (DEMO/PROTOTYPE)",
    version="1.0.0"
)

# Enable CORS for PWA and Dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Seed DB on startup if empty
    db = next(get_db())
    if db.query(models.Facility).count() == 0:
        seed.seed_database()

# Health Check
@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "JanSethu AI Backend",
        "version": "1.0.0",
        "demo_mode": True,
        "disclaimer": "This is a healthcare access & navigation prototype. It does NOT provide medical diagnosis or treatment."
    }

# GET /facilities & GET /api/facilities
@app.get("/facilities", response_model=List[schemas.FacilityResponse])
@app.get("/api/facilities", response_model=List[schemas.FacilityResponse])
def read_facilities(
    city: Optional[str] = None,
    area: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    facilities = crud.get_facilities(db, city=city, area=area, service=service, search=search)
    return facilities

# GET /facilities/{id} & GET /api/facilities/{id}
@app.get("/facilities/{facility_id}", response_model=schemas.FacilityDetailResponse)
@app.get("/api/facilities/{facility_id}", response_model=schemas.FacilityDetailResponse)
def read_facility(facility_id: int, db: Session = Depends(get_db)):
    facility = crud.get_facility(db, facility_id=facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {facility_id} not found")
    return facility

# GET /facilities/{id}/slots & GET /api/facilities/{id}/slots
@app.get("/facilities/{facility_id}/slots", response_model=List[schemas.SlotResponse])
@app.get("/api/facilities/{facility_id}/slots", response_model=List[schemas.SlotResponse])
def read_facility_slots(
    facility_id: int,
    date: Optional[str] = None,
    only_available: bool = True,
    db: Session = Depends(get_db)
):
    facility = crud.get_facility(db, facility_id=facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {facility_id} not found")
    slots = crud.get_slots(db, facility_id=facility_id, only_available=only_available, date=date)
    return slots

# POST /appointments & POST /api/appointments
@app.post("/appointments", response_model=schemas.AppointmentResponse)
@app.post("/api/appointments", response_model=schemas.AppointmentResponse)
def create_new_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db)
):
    facility = crud.get_facility(db, facility_id=appointment.facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {appointment.facility_id} not found")
    
    created_apt = crud.create_appointment(db, appointment)
    response = schemas.AppointmentResponse.from_orm(created_apt)
    response.facility_name = facility.name
    return response

# GET /appointments & GET /api/appointments
@app.get("/appointments", response_model=List[schemas.AppointmentResponse])
@app.get("/api/appointments", response_model=List[schemas.AppointmentResponse])
def read_appointments(
    facility_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    apts = crud.get_appointments(db, facility_id=facility_id, status=status)
    result = []
    for apt in apts:
        fac = crud.get_facility(db, apt.facility_id)
        item = schemas.AppointmentResponse.from_orm(apt)
        item.facility_name = fac.name if fac else "Unknown Facility"
        result.append(item)
    return result

# GET /appointments/{id} & GET /api/appointments/{id}
@app.get("/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
@app.get("/api/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
def read_appointment(appointment_id: int, db: Session = Depends(get_db)):
    apt = crud.get_appointment(db, appointment_id=appointment_id)
    if not apt:
        raise HTTPException(status_code=404, detail=f"Appointment with ID {appointment_id} not found")
    fac = crud.get_facility(db, apt.facility_id)
    response = schemas.AppointmentResponse.from_orm(apt)
    response.facility_name = fac.name if fac else "Unknown Facility"
    return response

# PATCH /appointments/{id}/status & PATCH /api/appointments/{id}/status
@app.patch("/appointments/{appointment_id}/status")
@app.patch("/api/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    status: str = Query(..., pattern="^(pending|confirmed|rejected|rescheduled)$"),
    db: Session = Depends(get_db)
):
    updated = crud.update_appointment_status(db, appointment_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Appointment with ID {appointment_id} not found")
    return {"message": "Status updated successfully", "id": updated.id, "status": updated.status}

# Emergency Helpline Info
@app.get("/emergency", response_model=schemas.EmergencyInfo)
@app.get("/api/emergency", response_model=schemas.EmergencyInfo)
def get_emergency_info():
    return schemas.EmergencyInfo(
        message="For life-threatening medical emergencies, please call emergency ambulance services immediately.",
        message_hi="गंभीर आपातकालीन चिकित्सा के लिए कृपया तुरंत एम्बुलेंस सेवा 108 पर कॉल करें।",
        contacts=[
            schemas.EmergencyContact(
                title="National Emergency Ambulance",
                title_hi="राष्ट्रीय एम्बुलेंस सेवा",
                number="108",
                description="Toll-free emergency ambulance dispatcher",
                description_hi="निःशुल्क आपातकालीन एम्बुलेंस सेवा"
            ),
            schemas.EmergencyContact(
                title="National Health Helpline",
                title_hi="राष्ट्रीय स्वास्थ्य हेल्पलाइन",
                number="104",
                description="Medical advice and health helpline",
                description_hi="चिकित्सा परामर्श और स्वास्थ्य सहायता"
            ),
            schemas.EmergencyContact(
                title="Women & Child Emergency Helpline",
                title_hi="महिला एवं बाल हेल्पलाइन",
                number="181 / 1098",
                description="Specialized emergency assistance",
                description_hi="विशेष आपातकालीन सहायता"
            )
        ]
    )
