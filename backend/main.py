from fastapi import FastAPI, Depends, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, crud
from database import engine, get_db, Base
import seed
import intent_engine
import telephony

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

# =========================================================
# PHASE 7 TELEPHONY / KEYPAD PHONE CHANNEL API ENDPOINTS
# =========================================================

@app.get("/telephony/config")
@app.get("/api/telephony/config")
def get_telephony_config():
    """Returns telephony provider status and credential configuration requirements."""
    return {
        "twilio_configured": bool(telephony.TWILIO_ACCOUNT_SID and telephony.TWILIO_AUTH_TOKEN),
        "exotel_configured": bool(telephony.EXOTEL_SID and telephony.EXOTEL_TOKEN),
        "mock_mode": True,
        "voice_webhook_url": "http://<YOUR_HOST>/api/telephony/voice",
        "sms_webhook_url": "http://<YOUR_HOST>/api/telephony/sms",
        "instructions": "For production telephony, set environment variables TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER."
    }

@app.post("/telephony/voice", response_model=schemas.TelephonyResponse)
@app.post("/api/telephony/voice", response_model=schemas.TelephonyResponse)
def handle_incoming_call(
    call_payload: Optional[schemas.TelephonyCallPayload] = None,
    db: Session = Depends(get_db)
):
    if not call_payload:
        call_payload = schemas.TelephonyCallPayload()
    return telephony.handle_telephony_call(call_payload, db)

@app.post("/telephony/gather", response_model=schemas.TelephonyResponse)
@app.post("/api/telephony/gather", response_model=schemas.TelephonyResponse)
def handle_telephony_gather(
    call_payload: schemas.TelephonyCallPayload,
    db: Session = Depends(get_db)
):
    return telephony.handle_telephony_call(call_payload, db)

@app.post("/telephony/sms")
@app.post("/api/telephony/sms")
def send_telephony_sms(
    phone: str = Query(...),
    text: str = Query(...),
):
    sent = telephony.send_sms_confirmation(phone, text)
    return {"message": "SMS processed", "sent": sent, "phone": phone, "body": text}


# =========================================================
# PHASE 4 VOICE ASSISTANT INTENT ENDPOINT
# =========================================================

@app.post("/voice/intent", response_model=schemas.VoiceResponse)
@app.post("/api/voice/intent", response_model=schemas.VoiceResponse)
def handle_voice_intent(
    voice_req: schemas.VoiceRequest,
    db: Session = Depends(get_db)
):
    return intent_engine.process_voice_intent(voice_req, db)


# =========================================================
# CORE FACILITY & APPOINTMENT REST ENDPOINTS
# =========================================================

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

@app.get("/emergency/facilities", response_model=List[schemas.FacilityResponse])
@app.get("/api/emergency/facilities", response_model=List[schemas.FacilityResponse])
def read_emergency_facilities(db: Session = Depends(get_db)):
    facilities = crud.get_emergency_facilities(db)
    return facilities

@app.get("/facilities/{facility_id}", response_model=schemas.FacilityDetailResponse)
@app.get("/api/facilities/{facility_id}", response_model=schemas.FacilityDetailResponse)
def read_facility(facility_id: int, db: Session = Depends(get_db)):
    facility = crud.get_facility(db, facility_id=facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {facility_id} not found")
    return facility

@app.get("/facilities/{facility_id}/slots", response_model=List[schemas.SlotResponse])
@app.get("/api/facilities/{facility_id}/slots", response_model=List[schemas.SlotResponse])
def read_facility_slots(
    facility_id: int,
    date: Optional[str] = None,
    only_available: bool = False,
    db: Session = Depends(get_db)
):
    facility = crud.get_facility(db, facility_id=facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {facility_id} not found")
    slots = crud.get_slots(db, facility_id=facility_id, only_available=only_available, date=date)
    return slots

@app.post("/facilities/{facility_id}/slots", response_model=schemas.SlotResponse)
@app.post("/api/facilities/{facility_id}/slots", response_model=schemas.SlotResponse)
def add_facility_slot(
    facility_id: int,
    slot_data: schemas.SlotCreate,
    db: Session = Depends(get_db)
):
    facility = crud.get_facility(db, facility_id=facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {facility_id} not found")
    slot_data.facility_id = facility_id
    created_slot = crud.create_slot(db, slot_data)
    return created_slot

@app.patch("/slots/{slot_id}/toggle", response_model=schemas.SlotResponse)
@app.patch("/api/slots/{slot_id}/toggle", response_model=schemas.SlotResponse)
def toggle_slot(slot_id: int, db: Session = Depends(get_db)):
    updated_slot = crud.toggle_slot_availability(db, slot_id)
    if not updated_slot:
        raise HTTPException(status_code=404, detail=f"Slot with ID {slot_id} not found")
    return updated_slot

@app.delete("/slots/{slot_id}")
@app.delete("/api/slots/{slot_id}")
def remove_slot(slot_id: int, db: Session = Depends(get_db)):
    success = crud.delete_slot(db, slot_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Slot with ID {slot_id} not found")
    return {"message": "Slot deleted successfully", "id": slot_id}

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

@app.patch("/appointments/{appointment_id}/reschedule", response_model=schemas.AppointmentResponse)
@app.patch("/api/appointments/{appointment_id}/reschedule", response_model=schemas.AppointmentResponse)
def reschedule_patient_appointment(
    appointment_id: int,
    reschedule_data: schemas.AppointmentReschedule,
    db: Session = Depends(get_db)
):
    rescheduled = crud.reschedule_appointment(db, appointment_id, reschedule_data.new_date, reschedule_data.new_time)
    if not rescheduled:
        raise HTTPException(status_code=404, detail=f"Appointment with ID {appointment_id} not found")
    fac = crud.get_facility(db, rescheduled.facility_id)
    response = schemas.AppointmentResponse.from_orm(rescheduled)
    response.facility_name = fac.name if fac else "Unknown Facility"
    return response

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
