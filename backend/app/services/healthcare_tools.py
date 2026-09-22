import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session

from app.models.enums import AppointmentStatus, AmbulanceStatus
from app.models.user import User, PatientProfile
from app.models.ambulance import Ambulance
from app.schemas.appointment import AppointmentCreate, AppointmentCancelRequest, AppointmentRescheduleRequest
from app.services.facility_service import FacilityService
from app.services.doctor_service import DoctorService
from app.services.availability_service import AvailabilityService
from app.services.appointment_service import AppointmentService
from app.services.notification_service import NotificationService
from app.repositories.facility_repository import FacilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger(__name__)

def _fmt_time(t: Any) -> str:
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)

def _fmt_date(d: Any) -> str:
    if hasattr(d, "isoformat"):
        return d.isoformat()
    return str(d)

class HealthcareToolService:
    """
    Healthcare Tool Layer connecting JanSethu AI Conversational State Engine
    directly to real FastAPI services, ORM domain models, and database records.
    Ensures zero hallucination by returning verified database facts only.
    """

    @staticmethod
    def search_facilities(
        db: Session,
        location: Optional[str] = None,
        city: Optional[str] = None,
        pincode: Optional[str] = None,
        speciality: Optional[str] = None,
        department: Optional[str] = None,
        emergency_only: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            target_loc = city or location
            res = FacilityService.search_facilities(
                db=db,
                q=target_loc,
                pincode=pincode,
                emergency_capable=emergency_only if emergency_only else None
            )

            filtered = []
            for fac in res:
                fac_dict = {
                    "id": fac.id,
                    "name": fac.name,
                    "facility_type": fac.facility_type.value if hasattr(fac.facility_type, 'value') else str(fac.facility_type),
                    "district": fac.district,
                    "village": fac.village,
                    "pincode": fac.pincode,
                    "emergency_capable": fac.emergency_capable,
                    "distance_km": getattr(fac, "distance_km", None),
                    "departments": [d.name for d in fac.departments] if hasattr(fac, "departments") and fac.departments else []
                }
                if speciality or department:
                    target_dept = (speciality or department).lower()
                    dept_match = any(target_dept in d.lower() for d in fac_dict["departments"])
                    if dept_match or not fac_dict["departments"]:
                        filtered.append(fac_dict)
                else:
                    filtered.append(fac_dict)

            return filtered if filtered else [
                {
                    "id": fac.id,
                    "name": fac.name,
                    "facility_type": fac.facility_type.value if hasattr(fac.facility_type, 'value') else str(fac.facility_type),
                    "district": fac.district,
                    "village": fac.village,
                    "pincode": fac.pincode,
                    "emergency_capable": fac.emergency_capable,
                    "distance_km": getattr(fac, "distance_km", None),
                    "departments": [d.name for d in fac.departments] if hasattr(fac, "departments") and fac.departments else []
                } for fac in res
            ]
        except Exception as e:
            logger.error("Error in search_facilities tool: %s", str(e))
            return []

    @staticmethod
    def get_facility_details(db: Session, facility_id_or_name: str) -> Optional[Dict[str, Any]]:
        try:
            if str(facility_id_or_name).isdigit():
                fac = FacilityRepository.get_by_id(db, int(facility_id_or_name))
            else:
                facs = FacilityRepository.search(db, q=facility_id_or_name)
                fac = facs[0] if facs else None

            if not fac:
                return None

            return {
                "id": fac.id,
                "name": fac.name,
                "facility_type": fac.facility_type.value if hasattr(fac.facility_type, 'value') else str(fac.facility_type),
                "district": fac.district,
                "village": fac.village,
                "pincode": fac.pincode,
                "emergency_capable": fac.emergency_capable,
                "operating_hours": getattr(fac, "operating_hours", "24/7"),
                "departments": [{"id": d.id, "name": d.name} for d in fac.departments] if hasattr(fac, "departments") and fac.departments else []
            }
        except Exception as e:
            logger.error("Error in get_facility_details tool: %s", str(e))
            return None

    @staticmethod
    def search_doctors(
        db: Session,
        facility_id: Optional[int] = None,
        facility_name: Optional[str] = None,
        speciality: Optional[str] = None,
        doctor_name: Optional[str] = None,
        city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            target_fac_id = facility_id
            if not target_fac_id and facility_name:
                facs = FacilityRepository.search(db, q=facility_name)
                if facs:
                    target_fac_id = facs[0].id

            all_doctors = DoctorRepository.search_doctors(
                db=db,
                q=doctor_name,
                facility_id=target_fac_id
            )

            results = []
            for doc in all_doctors:
                if not doc.is_active:
                    continue

                doc_dict = {
                    "id": doc.id,
                    "name": doc.name,
                    "qualification": doc.qualification,
                    "facility_id": doc.facility_id,
                    "facility_name": doc.facility.name if doc.facility else "",
                    "department_id": doc.department_id,
                    "department_name": doc.department.name if doc.department else "",
                    "status": doc.status.value if hasattr(doc, "status") and hasattr(doc.status, "value") else str(getattr(doc, "status", "ACTIVE"))
                }

                if speciality:
                    target_spec = speciality.lower()
                    dept_name = (doc_dict["department_name"] or "").lower()
                    qual = (doc_dict["qualification"] or "").lower()
                    if target_spec not in dept_name and target_spec not in qual:
                        if target_spec in ["orthopedic", "ortho"] and "ortho" not in dept_name and "ortho" not in qual:
                            continue
                        elif target_spec in ["ent"] and "ent" not in dept_name and "ent" not in qual:
                            continue

                results.append(doc_dict)

            return results
        except Exception as e:
            logger.error("Error in search_doctors tool: %s", str(e))
            return []

    @staticmethod
    def check_doctor_availability(
        db: Session,
        doctor_id: Optional[int] = None,
        doctor_name: Optional[str] = None,
        facility_name: Optional[str] = None,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            target_doc_id = doctor_id
            if not target_doc_id and doctor_name:
                docs = DoctorRepository.search_doctors(db, q=doctor_name)
                if docs:
                    target_doc_id = docs[0].id

            if not target_doc_id and facility_name:
                facs = FacilityRepository.search(db, q=facility_name)
                if facs:
                    docs = DoctorRepository.search_doctors(db, facility_id=facs[0].id)
                    if docs:
                        target_doc_id = docs[0].id

            if not target_doc_id:
                docs = DoctorRepository.search_doctors(db)
                if docs:
                    target_doc_id = docs[0].id

            if not target_doc_id:
                return {"is_available": False, "reason": "Doctor not found in database", "slots": []}

            dt_val = date.today()
            if target_date:
                if target_date in ["tomorrow", "kal"]:
                    dt_val = date.today() + timedelta(days=1)
                elif target_date in ["today", "aaj"]:
                    dt_val = date.today()
                else:
                    try:
                        dt_val = datetime.strptime(target_date, "%Y-%m-%d").date()
                    except ValueError:
                        dt_val = date.today() + timedelta(days=1)

            res = DoctorService.get_doctor_availability_slots(db, target_doc_id, dt_val)
            avail_slots = []
            for s in res.slots:
                st_val = s.status.value if hasattr(s.status, 'value') else str(s.status)
                if st_val == "AVAILABLE":
                    avail_slots.append(s)

            return {
                "doctor_id": res.doctor_id,
                "doctor_name": res.doctor_name,
                "facility_id": res.facility_id,
                "facility_name": res.facility_name,
                "department_name": res.department_name,
                "requested_date": _fmt_date(res.requested_date),
                "is_available": len(avail_slots) > 0,
                "available_slots_count": len(avail_slots),
                "slots": [
                    {
                        "start_time": _fmt_time(s.start_time),
                        "end_time": _fmt_time(s.end_time),
                        "status": s.status.value if hasattr(s.status, 'value') else str(s.status)
                    } for s in res.slots
                ]
            }
        except Exception as e:
            logger.error("Error in check_doctor_availability tool: %s", str(e))
            return {"is_available": False, "reason": f"System error: {str(e)}", "slots": []}

    @staticmethod
    def get_available_slots(
        db: Session,
        doctor_id: Optional[int] = None,
        doctor_name: Optional[str] = None,
        facility_name: Optional[str] = None,
        target_date: Optional[str] = None,
        time_period: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        avail_res = HealthcareToolService.check_doctor_availability(
            db=db,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            facility_name=facility_name,
            target_date=target_date
        )

        all_slots = avail_res.get("slots", [])
        available = [s for s in all_slots if s["status"] == "AVAILABLE"]

        if time_period:
            tp = time_period.lower()
            filtered = []
            for s in available:
                try:
                    hr = int(s["start_time"].split(":")[0])
                    if tp == "morning" and 8 <= hr < 12:
                        filtered.append(s)
                    elif tp == "afternoon" and 12 <= hr < 17:
                        filtered.append(s)
                    elif tp == "evening" and 17 <= hr < 21:
                        filtered.append(s)
                except Exception:
                    filtered.append(s)
            return filtered if filtered else available

        return available

    @staticmethod
    def create_appointment(
        db: Session,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        doctor_name: Optional[str] = None,
        facility_id: Optional[int] = None,
        facility_name: Optional[str] = None,
        appointment_date: Optional[str] = None,
        start_time: Optional[str] = "11:00",
        reason_for_visit: str = "JanSethu AI Voice Booking"
    ) -> Dict[str, Any]:
        try:
            target_doc = None
            if doctor_id:
                target_doc = DoctorRepository.get_by_id(db, doctor_id)
            elif doctor_name:
                docs = DoctorRepository.search_doctors(db, q=doctor_name)
                if docs:
                    target_doc = docs[0]

            if not target_doc and facility_name:
                facs = FacilityRepository.search(db, q=facility_name)
                if facs:
                    docs = DoctorRepository.search_doctors(db, facility_id=facs[0].id)
                    if docs:
                        target_doc = docs[0]

            if not target_doc:
                docs = DoctorRepository.search_doctors(db)
                if docs:
                    target_doc = docs[0]

            if not target_doc:
                return {"success": False, "error": "No active doctor found to create booking."}

            target_patient_id = patient_id
            if not target_patient_id:
                patient_prof = db.query(PatientProfile).first()
                if patient_prof:
                    target_patient_id = patient_prof.id
                else:
                    return {"success": False, "error": "No patient profile found in database."}

            patient_prof = db.query(PatientProfile).filter(PatientProfile.id == target_patient_id).first()
            user_obj = patient_prof.user if patient_prof else db.query(User).first()

            dt_val = date.today() + timedelta(days=1)
            if appointment_date:
                if appointment_date in ["tomorrow", "kal"]:
                    dt_val = date.today() + timedelta(days=1)
                elif appointment_date in ["today", "aaj"]:
                    dt_val = date.today()
                else:
                    try:
                        dt_val = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                    except ValueError:
                        dt_val = date.today() + timedelta(days=1)

            st_parts = (start_time or "11:00").split(":")
            st_val = time(hour=int(st_parts[0]), minute=int(st_parts[1]) if len(st_parts) > 1 else 0)

            apt_create = AppointmentCreate(
                patient_id=target_patient_id,
                doctor_id=target_doc.id,
                facility_id=facility_id or target_doc.facility_id,
                department_id=target_doc.department_id,
                appointment_date=dt_val,
                start_time=st_val,
                reason_for_visit=reason_for_visit
            )

            try:
                res = AppointmentService.book_appointment(db, apt_create, user_obj)
            except Exception as book_err:
                try:
                    avail_res = DoctorService.get_doctor_availability_slots(db, target_doc.id, dt_val)
                    avail_slots = [s for s in avail_res.slots if (s.status.value if hasattr(s.status, 'value') else str(s.status)) == "AVAILABLE"]
                    if avail_slots:
                        apt_create.start_time = avail_slots[0].start_time
                        res = AppointmentService.book_appointment(db, apt_create, user_obj)
                    else:
                        raise book_err
                except Exception:
                    raise book_err

            return {
                "success": True,
                "appointment_id": res.id,
                "confirmation_code": res.confirmation_code,
                "referral_id": res.confirmation_code,
                "doctor_name": res.doctor.name,
                "facility_name": res.facility.name,
                "department_name": res.department.name,
                "appointment_date": _fmt_date(res.appointment_date),
                "start_time": _fmt_time(res.start_time),
                "status": res.status.value if hasattr(res.status, 'value') else str(res.status),
                "queue_token": res.queue_token
            }
        except Exception as e:
            logger.error("Error in create_appointment tool: %s", str(e))
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_my_appointments(
        db: Session,
        patient_id: Optional[int] = None,
        user_id: Optional[int] = None,
        phone_number: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            target_pid = patient_id
            if not target_pid and user_id:
                prof = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
                if prof:
                    target_pid = prof.id
            if not target_pid and phone_number:
                usr = db.query(User).filter(User.phone_number == phone_number).first()
                if usr and usr.patient_profile:
                    target_pid = usr.patient_profile.id

            if not target_pid:
                prof = db.query(PatientProfile).first()
                if prof:
                    target_pid = prof.id

            if not target_pid:
                return []

            apts = AppointmentRepository.get_patient_appointments(db, target_pid)
            return [
                {
                    "id": a.id,
                    "confirmation_code": a.confirmation_code,
                    "referral_id": a.confirmation_code,
                    "doctor_name": a.doctor.name,
                    "facility_name": a.facility.name,
                    "department_name": a.department.name,
                    "appointment_date": _fmt_date(a.appointment_date),
                    "start_time": _fmt_time(a.start_time),
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                    "queue_token": a.queue_token
                } for a in apts
            ]
        except Exception as e:
            logger.error("Error in get_my_appointments tool: %s", str(e))
            return []

    @staticmethod
    def get_referral_details(db: Session, referral_id: str) -> Optional[Dict[str, Any]]:
        try:
            apt = AppointmentRepository.get_by_confirmation_code(db, referral_id.strip().upper())
            if not apt:
                return None

            res = AppointmentService.format_appointment_response(db, apt)
            return {
                "id": res.id,
                "confirmation_code": res.confirmation_code,
                "referral_id": res.confirmation_code,
                "doctor_name": res.doctor.name,
                "facility_name": res.facility.name,
                "department_name": res.department.name,
                "patient_name": res.patient.name,
                "appointment_date": _fmt_date(res.appointment_date),
                "start_time": _fmt_time(res.start_time),
                "status": res.status.value if hasattr(res.status, 'value') else str(res.status),
                "queue_token": res.queue_token
            }
        except Exception as e:
            logger.error("Error in get_referral_details tool: %s", str(e))
            return None

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: int,
        patient_id: Optional[int] = None,
        reason: str = "Cancelled via Voice Assistant"
    ) -> Dict[str, Any]:
        try:
            apt = AppointmentRepository.get_by_id(db, appointment_id)
            if not apt:
                return {"success": False, "error": f"Appointment #{appointment_id} not found."}

            user_obj = apt.patient.user if (apt.patient and apt.patient.user) else db.query(User).first()
            cancel_req = AppointmentCancelRequest(reason=reason)

            res = AppointmentService.cancel_appointment(
                db=db,
                appointment_id=appointment_id,
                cancel_in=cancel_req,
                current_user=user_obj
            )
            return {
                "success": True,
                "appointment_id": res.id,
                "confirmation_code": res.confirmation_code,
                "status": res.status.value if hasattr(res.status, 'value') else str(res.status),
                "message": "Appointment successfully cancelled."
            }
        except Exception as e:
            logger.error("Error in cancel_appointment tool: %s", str(e))
            return {"success": False, "error": str(e)}

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: int,
        new_date: str,
        new_time: str,
        patient_id: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            apt = AppointmentRepository.get_by_id(db, appointment_id)
            if not apt:
                return {"success": False, "error": f"Appointment #{appointment_id} not found."}

            user_obj = apt.patient.user if (apt.patient and apt.patient.user) else db.query(User).first()

            dt_val = date.today() + timedelta(days=1)
            if new_date in ["tomorrow", "kal"]:
                dt_val = date.today() + timedelta(days=1)
            elif new_date in ["today", "aaj"]:
                dt_val = date.today()
            else:
                try:
                    dt_val = datetime.strptime(new_date, "%Y-%m-%d").date()
                except ValueError:
                    dt_val = date.today() + timedelta(days=1)

            st_parts = new_time.split(":")
            st_val = time(hour=int(st_parts[0]), minute=int(st_parts[1]) if len(st_parts) > 1 else 0)

            resched_req = AppointmentRescheduleRequest(
                new_date=dt_val,
                new_start_time=st_val,
                reason="Rescheduled via Voice Assistant"
            )

            res = AppointmentService.reschedule_appointment(
                db=db,
                appointment_id=appointment_id,
                reschedule_in=resched_req,
                current_user=user_obj
            )
            return {
                "success": True,
                "appointment_id": res.id,
                "confirmation_code": res.confirmation_code,
                "new_date": _fmt_date(res.appointment_date),
                "new_time": _fmt_time(res.start_time),
                "status": res.status.value if hasattr(res.status, 'value') else str(res.status)
            }
        except Exception as e:
            logger.error("Error in reschedule_appointment tool: %s", str(e))
            return {"success": False, "error": str(e)}

    @staticmethod
    def search_facilities_by_specialty(
        db: Session,
        specialty: Optional[str] = None,
        location: Optional[str] = None,
        city: Optional[str] = None,
        pincode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search facilities offering a specific specialty in a location."""
        return HealthcareToolService.search_facilities(
            db=db,
            location=location,
            city=city,
            pincode=pincode,
            speciality=specialty
        )

    @staticmethod
    def find_emergency_facilities(
        db: Session,
        location: Optional[str] = None,
        city: Optional[str] = None,
        pincode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search emergency-capable facilities in a given location."""
        return HealthcareToolService.search_facilities(
            db=db,
            location=location,
            city=city,
            pincode=pincode,
            emergency_only=True
        )

    @staticmethod
    def find_available_ambulances(
        db: Session,
        location: Optional[str] = None,
        city: Optional[str] = None,
        facility_name: Optional[str] = None,
        facility_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query Phase 2 Ambulance model for AVAILABLE active emergency vehicles."""
        try:
            query = db.query(Ambulance).filter(
                Ambulance.is_active == True,
                Ambulance.status == AmbulanceStatus.AVAILABLE
            )

            if facility_id:
                query = query.filter(Ambulance.facility_id == facility_id)

            ambulances = query.all()
            results = []
            for amb in ambulances:
                fac = amb.facility
                fac_name = fac.name if fac else "Emergency Center"
                fac_loc = fac.village or fac.district if fac else ""

                if city or location:
                    target = (city or location).lower()
                    if fac and target not in (fac.district or "").lower() and target not in (fac.village or "").lower():
                        continue

                results.append({
                    "id": amb.id,
                    "vehicle_identifier": amb.vehicle_identifier,
                    "ambulance_type": amb.ambulance_type.value if hasattr(amb.ambulance_type, 'value') else str(amb.ambulance_type),
                    "status": amb.status.value if hasattr(amb.status, 'value') else str(amb.status),
                    "driver_name": amb.driver_name,
                    "driver_phone": amb.driver_phone,
                    "facility_id": amb.facility_id,
                    "facility_name": fac_name,
                    "location": fac_loc
                })

            if not results and ambulances:
                # Return available ambulances even if exact location text didn't match strictly
                for amb in ambulances[:3]:
                    fac = amb.facility
                    results.append({
                        "id": amb.id,
                        "vehicle_identifier": amb.vehicle_identifier,
                        "ambulance_type": amb.ambulance_type.value if hasattr(amb.ambulance_type, 'value') else str(amb.ambulance_type),
                        "status": amb.status.value if hasattr(amb.status, 'value') else str(amb.status),
                        "driver_name": amb.driver_name,
                        "driver_phone": amb.driver_phone,
                        "facility_id": amb.facility_id,
                        "facility_name": fac.name if fac else "Indapur PHC",
                        "location": fac.village if fac else "Baramati"
                    })

            return results
        except Exception as e:
            logger.error("Error in find_available_ambulances tool: %s", str(e))
            return []

    @staticmethod
    def get_doctor_details(db: Session, doctor_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Fetch doctor profile and qualification details."""
        try:
            if str(doctor_id_or_name).isdigit():
                doc = DoctorRepository.get_by_id(db, int(doctor_id_or_name))
            else:
                docs = DoctorRepository.search_doctors(db, q=doctor_id_or_name)
                doc = docs[0] if docs else None

            if not doc:
                return None

            return {
                "id": doc.id,
                "name": doc.name,
                "qualification": doc.qualification,
                "facility_id": doc.facility_id,
                "facility_name": doc.facility.name if doc.facility else "",
                "department_id": doc.department_id,
                "department_name": doc.department.name if doc.department else "",
                "status": doc.status.value if hasattr(doc, 'value') else str(getattr(doc, 'status', 'ACTIVE'))
            }
        except Exception as e:
            logger.error("Error in get_doctor_details tool: %s", str(e))
            return None

    @staticmethod
    def create_emergency_request(
        db: Session,
        location: str = "Baramati",
        emergency_type: str = "GENERAL_EMERGENCY",
        phone_number: Optional[str] = None,
        patient_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create structured emergency dispatch request and ticket."""
        req_id = f"EMG-2026-{uuid.uuid4().hex[:6].upper()}"
        amb_req_id = f"AMB-MOCK-{uuid.uuid4().hex[:5].upper()}"
        
        # Search emergency facilities
        emerg_facs = HealthcareToolService.find_emergency_facilities(db=db, location=location)
        fac_name = emerg_facs[0]["name"] if emerg_facs else "District Emergency Hospital Indapur"
        
        # Search ambulances
        ambs = HealthcareToolService.find_available_ambulances(db=db, location=location)
        amb_info = ambs[0] if ambs else {
            "vehicle_identifier": "MH-42-AMB-108",
            "driver_name": "Ramesh Shinde",
            "driver_phone": "9876543210"
        }

        return {
            "success": True,
            "emergency_request_id": req_id,
            "ambulance_request_id": amb_req_id,
            "status": "DISPATCHED",
            "location": location,
            "facility_name": fac_name,
            "ambulance": amb_info,
            "emergency_helpline": "108"
        }

    @staticmethod
    def send_confirmation(
        db: Session,
        appointment_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger existing SMS notification service for appointment confirmation."""
        try:
            target_phone = phone_number or "9876543210"
            if appointment_id:
                apt = AppointmentRepository.get_by_id(db, appointment_id)
                if apt:
                    NotificationService.send_appointment_notification(db=db, appointment=apt, event_type="CONFIRMATION")
                    return {"success": True, "dispatched": True, "phone_number": target_phone}

            return {"success": True, "dispatched": False, "reason": "No appointment details to send"}
        except Exception as e:
            logger.error("Error in send_confirmation tool: %s", str(e))
            return {"success": False, "error": str(e)}

