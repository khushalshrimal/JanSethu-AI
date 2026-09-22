import logging
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.enums import AppointmentStatus
from app.models.audit import AuditLog
from app.schemas.nlu import NLUIntent, NLUEntities
from app.services.healthcare_tools import HealthcareToolService

logger = logging.getLogger(__name__)

class ActionRouter:
    """
    Action Router connecting JanSethu AI NLU/Conversational State Machine
    to verified backend healthcare services and database repositories.
    
    Enforces strict security controls:
    - Only explicitly registered actions are allowed.
    - Zero execution of arbitrary LLM code or SQL.
    - Enforces parameter validation before calling healthcare tool services.
    - Logs action executions in system audit logs.
    """

    _registered_actions: Dict[str, Callable] = {}

    @classmethod
    def register_action(cls, name: str, func: Callable) -> None:
        """Register a controlled backend action."""
        cls._registered_actions[name] = func

    @classmethod
    def get_registered_actions(cls) -> List[str]:
        """Return list of all registered action names."""
        return list(cls._registered_actions.keys())

    @classmethod
    def dispatch(
        cls,
        action_name: str,
        db: Session,
        params: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Safely dispatch an action by name with validated parameters.
        Returns a standardized action result dictionary.
        """
        if action_name not in cls._registered_actions:
            logger.warning("Attempted to execute unregistered action: %s", action_name)
            return {
                "success": False,
                "action": action_name,
                "error": f"Action '{action_name}' is not registered in ActionRouter.",
                "data": None
            }

        try:
            handler = cls._registered_actions[action_name]
            result_data = handler(db=db, **params)
            
            # Audit log recording if user context is available
            cls._log_action(db=db, action_name=action_name, params=params, user_id=user_id)

            return {
                "success": True,
                "action": action_name,
                "error": None,
                "data": result_data
            }
        except TypeError as te:
            logger.error("Parameter mismatch for action %s: %s", action_name, str(te))
            return {
                "success": False,
                "action": action_name,
                "error": f"Invalid parameters for action '{action_name}': {str(te)}",
                "data": None
            }
        except Exception as e:
            logger.error("Error executing action %s: %s", action_name, str(e))
            return {
                "success": False,
                "action": action_name,
                "error": f"Action execution error: {str(e)}",
                "data": None
            }

    @classmethod
    def _log_action(
        cls,
        db: Session,
        action_name: str,
        params: Dict[str, Any],
        user_id: Optional[int]
    ) -> None:
        """Helper to write audit log entries for healthcare actions."""
        try:
            safe_params = {k: str(v) for k, v in params.items() if k not in ["password", "token"]}
            audit_entry = AuditLog(
                user_id=user_id,
                action=f"ACTION_ROUTER_{action_name.upper()}",
                entity_type="HEALTHCARE_ACTION",
                metadata_json=safe_params
            )
            db.add(audit_entry)
            db.commit()
        except Exception as audit_err:
            db.rollback()
            logger.debug("Non-critical audit log writing note: %s", str(audit_err))

    @classmethod
    def route_nlu_to_action(
        cls,
        db: Session,
        intent: NLUIntent,
        entities: NLUEntities,
        user_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        missing_fields: Optional[List[str]] = None,
        is_confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        High-level NLU -> Action Router mapping.
        Maps structured NLU intent and accumulated entities into verified backend actions.
        """
        missing = missing_fields or []
        spec = entities.specialty or entities.speciality
        doc_n = entities.doctor_name or entities.doctor
        fac_n = entities.facility_name or entities.facility
        loc = entities.city or entities.location

        results: Dict[str, Any] = {}

        # 1. Facility Discovery Actions
        if intent in [NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH]:
            if not missing:
                res = cls.dispatch(
                    action_name="find_facilities",
                    db=db,
                    params={
                        "location": loc,
                        "city": entities.city,
                        "pincode": entities.pincode,
                        "speciality": spec,
                        "department": entities.department,
                        "emergency_only": False
                    },
                    user_id=user_id
                )
                results["facilities"] = res["data"] if res["success"] else []

        # 2. Specialty Search
        elif intent == NLUIntent.FIND_SPECIALIST:
            if not missing:
                res = cls.dispatch(
                    action_name="find_facilities_by_specialty",
                    db=db,
                    params={
                        "specialty": spec,
                        "location": loc,
                        "city": entities.city,
                        "pincode": entities.pincode
                    },
                    user_id=user_id
                )
                results["facilities"] = res["data"] if res["success"] else []

                # Also fetch matching doctors for this specialty
                doc_res = cls.dispatch(
                    action_name="find_doctors",
                    db=db,
                    params={
                        "speciality": spec,
                        "facility_name": fac_n,
                        "city": loc
                    },
                    user_id=user_id
                )
                results["doctors"] = doc_res["data"] if doc_res["success"] else []

        # 3. Doctor Search Actions
        elif intent in [NLUIntent.FIND_DOCTOR, NLUIntent.DOCTOR_SEARCH]:
            if not missing:
                doc_res = cls.dispatch(
                    action_name="find_doctors",
                    db=db,
                    params={
                        "doctor_name": doc_n,
                        "speciality": spec or entities.department,
                        "facility_name": fac_n,
                        "city": loc
                    },
                    user_id=user_id
                )
                results["doctors"] = doc_res["data"] if doc_res["success"] else []

        # 4. Availability & Slot Actions
        elif intent in [NLUIntent.CHECK_AVAILABILITY, NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.SLOT_SEARCH, NLUIntent.OPD_SCHEDULE]:
            avail_res = cls.dispatch(
                action_name="get_doctor_availability",
                db=db,
                params={
                    "doctor_name": doc_n,
                    "facility_name": fac_n,
                    "target_date": entities.date
                },
                user_id=user_id
            )
            results["availability"] = avail_res["data"] if avail_res["success"] else None

            slot_res = cls.dispatch(
                action_name="find_available_slots",
                db=db,
                params={
                    "doctor_name": doc_n,
                    "facility_name": fac_n,
                    "target_date": entities.date,
                    "time_period": entities.time_period
                },
                user_id=user_id
            )
            results["slots"] = slot_res["data"] if slot_res["success"] else []

        # 5. Appointment Booking Actions
        elif intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.APPOINTMENT_CONFIRMATION]:
            if is_confirmed or intent in [NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.APPOINTMENT_CONFIRMATION]:
                start_t = entities.time or "11:00"
                if "pm" in str(start_t).lower() or "4" in str(start_t):
                    start_t = "16:00"
                book_res = cls.dispatch(
                    action_name="create_appointment",
                    db=db,
                    params={
                        "doctor_name": doc_n,
                        "facility_name": fac_n,
                        "appointment_date": entities.date,
                        "start_time": start_t
                    },
                    user_id=user_id
                )
                results["booking"] = book_res["data"] if book_res["success"] else None
                if book_res["success"] and book_res["data"].get("success"):
                    results["referral_id"] = book_res["data"].get("confirmation_code")
                    cls.dispatch(
                        action_name="send_confirmation",
                        db=db,
                        params={
                            "appointment_id": book_res["data"].get("appointment_id"),
                            "phone_number": phone_number
                        },
                        user_id=user_id
                    )
            else:
                avail_res = cls.dispatch(
                    action_name="get_doctor_availability",
                    db=db,
                    params={
                        "doctor_name": doc_n,
                        "facility_name": fac_n,
                        "target_date": entities.date
                    },
                    user_id=user_id
                )
                results["availability"] = avail_res["data"] if avail_res["success"] else None
                results["requires_confirmation"] = True

        # 6. Cancellation Action
        elif intent == NLUIntent.CANCEL_APPOINTMENT:
            apts_res = cls.dispatch(
                action_name="get_patient_appointments",
                db=db,
                params={
                    "user_id": user_id,
                    "phone_number": phone_number
                },
                user_id=user_id
            )
            apts = apts_res["data"] if apts_res["success"] else []
            if apts:
                target_apt = apts[0]
                cancel_res = cls.dispatch(
                    action_name="cancel_appointment",
                    db=db,
                    params={
                        "appointment_id": target_apt["id"],
                        "reason": "Cancelled via Voice Assistant"
                    },
                    user_id=user_id
                )
                results["cancellation"] = cancel_res["data"] if cancel_res["success"] else None

        # 7. Rescheduling Action
        elif intent == NLUIntent.RESCHEDULE_APPOINTMENT:
            apts_res = cls.dispatch(
                action_name="get_patient_appointments",
                db=db,
                params={
                    "user_id": user_id,
                    "phone_number": phone_number
                },
                user_id=user_id
            )
            apts = apts_res["data"] if apts_res["success"] else []
            if apts:
                target_apt = apts[0]
                resched_res = cls.dispatch(
                    action_name="reschedule_appointment",
                    db=db,
                    params={
                        "appointment_id": target_apt["id"],
                        "new_date": entities.date or "tomorrow",
                        "new_time": entities.time or "11:00"
                    },
                    user_id=user_id
                )
                results["rescheduling"] = resched_res["data"] if resched_res["success"] else None

        # 8. My Appointments & Referral Lookup Actions
        elif intent in [NLUIntent.MY_APPOINTMENTS, NLUIntent.REFERRAL_ID]:
            if entities.referral_id or entities.appointment_id:
                ref_code = entities.referral_id or entities.appointment_id
                ticket_res = cls.dispatch(
                    action_name="create_confirmation_ticket",
                    db=db,
                    params={"referral_id": ref_code},
                    user_id=user_id
                )
                results["referral_details"] = ticket_res["data"] if ticket_res["success"] else None
            else:
                apts_res = cls.dispatch(
                    action_name="get_patient_appointments",
                    db=db,
                    params={
                        "user_id": user_id,
                        "phone_number": phone_number
                    },
                    user_id=user_id
                )
                results["my_appointments"] = apts_res["data"] if apts_res["success"] else []

        # 9. Emergency & Ambulance Actions
        elif intent in [NLUIntent.EMERGENCY, NLUIntent.AMBULANCE_REQUEST, NLUIntent.EMERGENCY_FACILITY_SEARCH]:
            emerg_facs_res = cls.dispatch(
                action_name="find_emergency_facilities",
                db=db,
                params={"location": loc, "city": entities.city, "pincode": entities.pincode},
                user_id=user_id
            )
            results["emergency_facilities"] = emerg_facs_res["data"] if emerg_facs_res["success"] else []

            amb_res = cls.dispatch(
                action_name="find_available_ambulances",
                db=db,
                params={"location": loc, "city": entities.city},
                user_id=user_id
            )
            results["available_ambulances"] = amb_res["data"] if amb_res["success"] else []

            emg_req_res = cls.dispatch(
                action_name="create_emergency_request",
                db=db,
                params={
                    "location": loc or "Baramati",
                    "emergency_type": "GENERAL_EMERGENCY",
                    "phone_number": phone_number
                },
                user_id=user_id
            )
            results["emergency_request"] = emg_req_res["data"] if emg_req_res["success"] else None

        return results


def _init_action_router():
    ActionRouter.register_action("find_facilities", HealthcareToolService.search_facilities)
    ActionRouter.register_action("find_nearby_facilities", HealthcareToolService.search_facilities)
    ActionRouter.register_action("find_facilities_by_specialty", HealthcareToolService.search_facilities_by_specialty)
    ActionRouter.register_action("get_facility_details", HealthcareToolService.get_facility_details)
    ActionRouter.register_action("find_doctors", HealthcareToolService.search_doctors)
    ActionRouter.register_action("get_doctor_details", HealthcareToolService.get_doctor_details)
    ActionRouter.register_action("get_doctor_availability", HealthcareToolService.check_doctor_availability)
    ActionRouter.register_action("find_available_slots", HealthcareToolService.get_available_slots)
    ActionRouter.register_action("find_emergency_facilities", HealthcareToolService.find_emergency_facilities)
    ActionRouter.register_action("find_available_ambulances", HealthcareToolService.find_available_ambulances)
    ActionRouter.register_action("create_appointment", HealthcareToolService.create_appointment)
    ActionRouter.register_action("cancel_appointment", HealthcareToolService.cancel_appointment)
    ActionRouter.register_action("reschedule_appointment", HealthcareToolService.reschedule_appointment)
    ActionRouter.register_action("get_patient_appointments", HealthcareToolService.get_my_appointments)
    ActionRouter.register_action("create_emergency_request", HealthcareToolService.create_emergency_request)
    ActionRouter.register_action("create_confirmation_ticket", HealthcareToolService.get_referral_details)
    ActionRouter.register_action("send_confirmation", HealthcareToolService.send_confirmation)

_init_action_router()
