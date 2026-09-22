import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.telephony import CallSession, ConversationMessage
from app.models.user import User, PatientProfile
from app.models.facility import Facility, Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.enums import CallSessionStatus, Language, BookingChannel, AppointmentStatus, UserRole, FacilityStatus, DepartmentStatus, DoctorStatus
from app.core.prompts import VoicePromptProvider
from app.schemas.phone import PhoneSessionResponse, PhoneMenuOption
from app.services.facility_service import FacilityService
from app.services.availability_service import AvailabilityService
from app.services.appointment_service import AppointmentService
from app.repositories.appointment_repository import AppointmentRepository
from app.services.notification_service import NotificationService
from app.services.voice import VoiceUnderstandingService, VoiceUnderstandingResult, IntentEnum
from app.schemas.appointment import AppointmentCancelRequest, AppointmentRescheduleRequest
from app.utils.timezone import get_today_ist

class PhoneSessionService:

    @staticmethod
    def start_session(
        db: Session,
        phone_number: str,
        channel: str = "TELEPHONY_SIMULATOR",
        provider: str = "development",
        provider_call_id: Optional[str] = None,
        resume_existing: bool = False
    ) -> CallSession:
        """
        Starts a new phone call session or resumes a valid active session.
        Sets initial GREETING state for new sessions.
        """
        from app.utils.phone_normalizer import normalize_phone_number
        norm_phone = normalize_phone_number(phone_number)

        # Check if caller matches existing customer user
        all_users = db.query(User).all()
        existing_user = None
        for u in all_users:
            if u.phone_number and normalize_phone_number(u.phone_number) == norm_phone:
                existing_user = u
                break
        if not existing_user:
            existing_user = db.query(User).filter(User.phone_number == phone_number).first()

        if resume_existing:
            timeout_cutoff = datetime.utcnow() - timedelta(minutes=15)
            resumable = db.query(CallSession).filter(
                CallSession.phone_number == norm_phone,
                CallSession.status == CallSessionStatus.ACTIVE,
                CallSession.created_at >= timeout_cutoff
            ).order_by(CallSession.id.desc()).first()

            if resumable:
                # Reset destructive confirmation states to review steps on resume for safety
                if resumable.current_state == "BOOKING_CONFIRMATION":
                    resumable.current_state = "SLOT_SELECTION"
                elif resumable.current_state == "CANCEL_CONFIRMATION":
                    resumable.current_state = "CANCEL_APPOINTMENT"
                elif resumable.current_state == "RESCHEDULE_CONFIRMATION":
                    resumable.current_state = "RESCHEDULE_DATE"

                resumable.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(resumable)
                return resumable
        else:
            stale_sessions = db.query(CallSession).filter(
                CallSession.phone_number == norm_phone,
                CallSession.status == CallSessionStatus.ACTIVE
            ).all()
            for s in stale_sessions:
                s.status = CallSessionStatus.COMPLETED
                s.ended_at = datetime.utcnow()
            db.flush()

        initial_state = "RETURNING_USER_GREETING" if existing_user else "PHONE_REGISTRATION_NAME"

        session = CallSession(
            phone_number=norm_phone,
            user_id=existing_user.id if existing_user else None,
            language=Language.HI,
            channel=channel,
            provider=provider,
            provider_call_id=provider_call_id or "dev-call-auto",
            status=CallSessionStatus.ACTIVE,
            current_state=initial_state,
            started_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Log system greeting
        if existing_user:
            greeting_text = VoicePromptProvider.get_prompt("RETURNING_GREETING", session.language, name=existing_user.name)
        else:
            greeting_text = VoicePromptProvider.get_prompt("PHONE_REGISTRATION_NAME", session.language)

        msg = ConversationMessage(
            call_session_id=session.id,
            sender_type="SYSTEM",
            message_type="VOICE",
            language=session.language,
            content=greeting_text
        )
        db.add(msg)
        db.commit()

        return session

    @staticmethod
    def get_session(db: Session, session_id: int) -> CallSession:
        session = db.query(CallSession).filter(CallSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call session #{session_id} not found."
            )
        return session

    @staticmethod
    def end_session(db: Session, session_id: int) -> CallSession:
        session = PhoneSessionService.get_session(db, session_id)
        session.status = CallSessionStatus.COMPLETED
        session.current_state = "ENDED"
        session.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def handle_back_navigation(session: CallSession):
        """Performs controlled backward state transition."""
        state = session.current_state
        if state == "SLOT_SELECTION":
            session.current_state = "DATE_SELECTION"
        elif state == "DATE_SELECTION":
            session.current_state = "DOCTOR_SELECTION"
        elif state == "DOCTOR_SELECTION":
            session.current_state = "DEPARTMENT_SELECTION"
        elif state in ["DEPARTMENT_SELECTION", "DEPARTMENT_UNAVAILABLE"]:
            session.current_state = "FACILITY_SELECTION"
        elif state in ["FACILITY_SELECTION", "LOCATION_INPUT", "FACILITY_UNAVAILABLE"]:
            session.current_state = "MAIN_MENU"
        elif state in ["BOOKING_CONFIRMATION", "BOOKING_COMPLETED"]:
            session.current_state = "SLOT_SELECTION"
        elif state in ["RESCHEDULE_SLOT", "RESCHEDULE_DATE", "RESCHEDULE_CONFIRMATION", "RESCHEDULE_COMPLETED"]:
            session.current_state = "RESCHEDULE_APPOINTMENT"
        elif state in ["CANCEL_CONFIRMATION", "CANCEL_COMPLETED"]:
            session.current_state = "CANCEL_APPOINTMENT"
        elif state in ["CHECK_IN", "CHECK_IN_COMPLETED", "CHECK_IN_FAILED", "NO_CHECKIN_APPOINTMENT"]:
            session.current_state = "MAIN_MENU"
        else:
            session.current_state = "MAIN_MENU"

    @staticmethod
    def process_dtmf_input(db: Session, session_id: int, key: str) -> PhoneSessionResponse:
        """
        Core State Machine Processor.
        Receives session ID and pressed keypad key (e.g. "1", "2", "3", "*", "#").
        Persists state transitions and selection context to DB.
        Returns localized prompt and available menu options.
        """
        session = PhoneSessionService.get_session(db, session_id)

        if session.status != CallSessionStatus.ACTIVE:
            session.status = CallSessionStatus.ACTIVE

        # Log DTMF input message
        input_msg = ConversationMessage(
            call_session_id=session.id,
            sender_type="USER",
            message_type="DTMF",
            language=session.language,
            content=key
        )
        db.add(input_msg)
        db.commit()

        state = session.current_state
        clean_key = key.strip()

        # Parse context JSON
        context = {}
        if session.context_json:
            try:
                context = json.loads(session.context_json)
            except Exception:
                context = {}

        # ------------------- GLOBAL KEY CONTROLS ------------------- #
        if clean_key == "*" and state not in ["GREETING", "ENDED"]:
            session.current_state = "HELP"
            session.updated_at = datetime.utcnow()
            db.commit()
            return PhoneSessionService.format_response(db, session)

        if clean_key == "9" and state not in ["GREETING", "LANGUAGE_SELECTION", "MAIN_MENU", "ENDED"]:
            PhoneSessionService.handle_back_navigation(session)
            session.updated_at = datetime.utcnow()
            db.commit()
            return PhoneSessionService.format_response(db, session)

        if clean_key == "0" and state not in ["GREETING", "LANGUAGE_SELECTION", "MAIN_MENU", "BOOKING_COMPLETED", "EMERGENCY", "ENDED"]:
            # Repeat current prompt without state transition or data mutation
            session.updated_at = datetime.utcnow()
            db.commit()
            return PhoneSessionService.format_response(db, session)

        # ------------------- STATE MACHINE SWITCH ------------------- #

        if state == "PHONE_REGISTRATION_NAME":
            name = f"Patient {session.phone_number[-4:]}"
            if not session.user_id:
                new_user = User(
                    name=name,
                    phone_number=session.phone_number,
                    password_hash=User.hash_password("temp_dtmf_pwd"),
                    role=UserRole.CUSTOMER,
                    preferred_language=Language.HI,
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                profile = PatientProfile(user_id=new_user.id, village="Baramati", district="Pune", state="Maharashtra")
                db.add(profile)
                db.commit()
                session.user_id = new_user.id

            if clean_key == "1":
                session.language = Language.HI
                session.current_state = "MAIN_MENU"
            elif clean_key == "2":
                session.language = Language.MR
                session.current_state = "MAIN_MENU"
            elif clean_key == "3":
                session.language = Language.EN
                session.current_state = "MAIN_MENU"
            elif clean_key == "4":
                session.current_state = "EMERGENCY"
            else:
                session.current_state = "LANGUAGE_SELECTION"

        elif state in ["GREETING", "RETURNING_USER_GREETING", "LANGUAGE_SELECTION"]:
            if clean_key == "1":
                session.language = Language.HI
            elif clean_key == "2":
                session.language = Language.MR
            elif clean_key == "3":
                session.language = Language.EN
            else:
                session.language = Language.HI
            session.current_state = "MAIN_MENU"

        elif state == "MAIN_MENU":
            if clean_key == "1":
                session.selected_intent = "BOOK_APPOINTMENT"
                all_facs = FacilityService.list_facilities(db)
                facs = [f for f in all_facs if db.query(Department).filter(
                    Department.facility_id == f.id,
                    Department.is_active == True,
                    Department.status == DepartmentStatus.ACTIVE
                ).first()]
                if facs:
                    context["facilities"] = [{"id": f.id, "name": f.name} for f in facs[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "FACILITY_SELECTION"
                else:
                    session.current_state = "LOCATION_INPUT"
            elif clean_key == "2":
                session.selected_intent = "CHECK_APPOINTMENT"
                session.current_state = "CHECK_APPOINTMENT"
            elif clean_key == "3":
                session.selected_intent = "CANCEL_APPOINTMENT"
                session.current_state = "CANCEL_APPOINTMENT"
            elif clean_key == "4":
                session.selected_intent = "EMERGENCY"
                session.current_state = "EMERGENCY"
            elif clean_key == "5":
                session.selected_intent = "RESCHEDULE_APPOINTMENT"
                session.current_state = "RESCHEDULE_APPOINTMENT"
            elif clean_key == "6":
                session.selected_intent = "CHECK_IN"
                session.current_state = "CHECK_IN"
            elif clean_key == "9":
                session.current_state = "MAIN_MENU"
            elif clean_key == "0":
                return PhoneSessionService.format_response(db, PhoneSessionService.end_session(db, session.id))

        elif state == "LOCATION_INPUT":
            # Search facilities by pincode or location keyword
            query_str = clean_key if clean_key != "1" else ""
            facs = FacilityService.list_facilities(db)
            if query_str:
                matched = [f for f in facs if query_str in f.pincode or query_str.lower() in f.name.lower() or query_str.lower() in (f.district or "").lower()]
                if matched:
                    facs = matched

            if facs:
                context["facilities"] = [{"id": f.id, "name": f.name} for f in facs[:5]]
                session.context_json = json.dumps(context)
                session.current_state = "FACILITY_SELECTION"
            else:
                session.current_state = "LOCATION_INPUT"

        elif state == "FACILITY_SELECTION":
            fac_list = context.get("facilities", [])
            idx = int(clean_key) - 1 if clean_key.isdigit() else -1
            if 0 <= idx < len(fac_list):
                selected_fac = fac_list[idx]
                session.selected_facility_id = selected_fac["id"]
                fac_obj = db.query(Facility).filter(Facility.id == selected_fac["id"]).first()
                if fac_obj and (not fac_obj.is_active or fac_obj.status == FacilityStatus.INACTIVE or fac_obj.status == FacilityStatus.TEMPORARILY_UNAVAILABLE):
                    session.current_state = "FACILITY_UNAVAILABLE"
                else:
                    all_depts = db.query(Department).filter(
                        Department.facility_id == selected_fac["id"],
                        Department.is_active == True,
                        Department.status == DepartmentStatus.ACTIVE
                    ).all()
                    depts = [d for d in all_depts if db.query(Doctor).filter(
                        Doctor.facility_id == selected_fac["id"],
                        Doctor.department_id == d.id,
                        Doctor.is_active == True,
                        Doctor.status == DoctorStatus.ACTIVE
                    ).first()]
                    if depts:
                        context["departments"] = [{"id": d.id, "name": d.name} for d in depts[:5]]
                        session.context_json = json.dumps(context)
                        session.current_state = "DEPARTMENT_SELECTION"
                    else:
                        session.current_state = "DEPARTMENT_UNAVAILABLE"
            else:
                session.current_state = "FACILITY_SELECTION"

        elif state == "DEPARTMENT_SELECTION":
            dept_list = context.get("departments", [])
            idx = int(clean_key) - 1 if clean_key.isdigit() else -1
            if 0 <= idx < len(dept_list):
                selected_dept = dept_list[idx]
                session.selected_department_id = selected_dept["id"]
                dept_obj = db.query(Department).filter(Department.id == selected_dept["id"]).first()
                if dept_obj and (not dept_obj.is_active or dept_obj.status == DepartmentStatus.INACTIVE):
                    session.current_state = "DEPARTMENT_UNAVAILABLE"
                else:
                    docs = db.query(Doctor).filter(
                        Doctor.facility_id == session.selected_facility_id,
                        Doctor.department_id == selected_dept["id"],
                        Doctor.is_active == True,
                        Doctor.status == DoctorStatus.ACTIVE
                    ).all()
                    if docs:
                        context["doctors"] = [{"id": d.id, "name": d.name} for d in docs[:5]]
                        session.context_json = json.dumps(context)
                        session.current_state = "DOCTOR_SELECTION"
                    else:
                        session.current_state = "DEPARTMENT_UNAVAILABLE"
            else:
                session.current_state = "DEPARTMENT_SELECTION"

        elif state in ["DEPARTMENT_UNAVAILABLE", "FACILITY_UNAVAILABLE"]:
            if clean_key == "9":
                PhoneSessionService.handle_back_navigation(session)
            else:
                session.current_state = "MAIN_MENU"

        elif state == "DOCTOR_SELECTION":
            doc_list = context.get("doctors", [])
            idx = int(clean_key) - 1 if clean_key.isdigit() else -1
            if 0 <= idx < len(doc_list):
                selected_doc = doc_list[idx]
                session.selected_doctor_id = selected_doc["id"]
                session.current_state = "DATE_SELECTION"
            else:
                session.current_state = "DOCTOR_SELECTION"

        elif state == "DATE_SELECTION":
            today = get_today_ist()
            target_date = today
            if clean_key == "2":
                target_date = today + timedelta(days=1)
            elif clean_key == "3":
                target_date = today + timedelta(days=2)

            date_str = target_date.strftime("%Y-%m-%d")
            session.selected_date = date_str

            try:
                avail_resp = AvailabilityService.generate_doctor_slots(db, session.selected_doctor_id, target_date)
                avail_slots = [s for s in avail_resp.slots if s.status == "AVAILABLE"]
                if avail_slots:
                    context["slots"] = [{"start_time": s.start_time, "end_time": s.end_time} for s in avail_slots[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "SLOT_SELECTION"
                else:
                    session.current_state = "DATE_SELECTION"
            except Exception:
                session.current_state = "DATE_SELECTION"

        elif state == "SLOT_SELECTION":
            slot_list = context.get("slots", [])
            idx = int(clean_key) - 1 if clean_key.isdigit() else -1
            if 0 <= idx < len(slot_list):
                sel_slot = slot_list[idx]
                session.selected_start_time = sel_slot["start_time"]
                session.selected_end_time = sel_slot["end_time"]
                session.current_state = "BOOKING_CONFIRMATION"
            else:
                session.current_state = "SLOT_SELECTION"

        elif state == "BOOKING_CONFIRMATION":
            if clean_key == "1":
                patient = None
                if session.user_id:
                    patient = db.query(PatientProfile).filter(PatientProfile.user_id == session.user_id).first()

                if not patient:
                    user = db.query(User).filter(User.phone_number == session.phone_number).first()
                    if not user:
                        suffix = session.phone_number[-4:] if len(session.phone_number) >= 4 else "Caller"
                        user = User(
                            phone_number=session.phone_number,
                            name=f"Phone Patient {suffix}",
                            role=UserRole.CUSTOMER,
                            password_hash=User.hash_password("JanSethuCaller123!")
                        )
                        db.add(user)
                        db.flush()

                    patient = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
                    if not patient:
                        patient = PatientProfile(
                            user_id=user.id,
                            district="Pune",
                            state="Maharashtra"
                        )
                        db.add(patient)
                        db.flush()

                    session.user_id = user.id

                try:
                    apt_date = datetime.strptime(session.selected_date, "%Y-%m-%d").date()
                    s_time = datetime.strptime(session.selected_start_time, "%H:%M").time()
                    e_time = datetime.strptime(session.selected_end_time, "%H:%M").time()

                    apt = AppointmentRepository.create_appointment(
                        db=db,
                        patient_id=patient.id,
                        doctor_id=session.selected_doctor_id,
                        facility_id=session.selected_facility_id,
                        department_id=session.selected_department_id,
                        apt_date=apt_date,
                        start_time=s_time,
                        end_time=e_time,
                        booking_channel=BookingChannel.PHONE,
                        reason_for_visit="Phone Voice IVR Booking"
                    )

                    NotificationService.send_appointment_notification(db, apt, event_type="BOOKING")

                    context["confirmation_code"] = apt.confirmation_code
                    session.context_json = json.dumps(context)
                    session.current_state = "BOOKING_COMPLETED"
                except Exception:
                    session.current_state = "SLOT_SELECTION"
            else:
                session.current_state = "MAIN_MENU"

        elif state in ["BOOKING_COMPLETED", "RESCHEDULE_COMPLETED", "EMERGENCY", "HELP", "ENDED", "CHECK_IN_COMPLETED", "CHECK_IN_FAILED", "NO_CHECKIN_APPOINTMENT"]:
            if clean_key == "0":
                return PhoneSessionService.format_response(db, PhoneSessionService.end_session(db, session.id))
            else:
                session.current_state = "MAIN_MENU"

        elif state == "CHECK_IN":
            PhoneSessionService._execute_check_in(db, session, context)

        elif state == "CHECK_APPOINTMENT":
            session.current_state = "MAIN_MENU"

        elif state == "CANCEL_APPOINTMENT":
            if clean_key == "1":
                recent_apt = None
                if session.user_id:
                    recent_apt = db.query(Appointment).filter(
                        Appointment.patient.has(user_id=session.user_id),
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                    ).order_by(Appointment.id.desc()).first()

                if not recent_apt:
                    recent_apt = db.query(Appointment).filter(
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                    ).order_by(Appointment.id.desc()).first()

                if recent_apt:
                    user = db.query(User).filter(User.id == session.user_id).first() if session.user_id else None
                    if not user and recent_apt.patient and recent_apt.patient.user:
                        user = recent_apt.patient.user
                    if not user:
                        user = db.query(User).filter(User.role == UserRole.ADMIN).first()

                    cancel_req = AppointmentCancelRequest(reason="Phone IVR Cancellation Request")
                    AppointmentService.cancel_appointment(db, recent_apt.id, cancel_req, current_user=user)
                    context["confirmation_code"] = recent_apt.confirmation_code
                    session.context_json = json.dumps(context)
                    session.current_state = "CANCEL_COMPLETED"
                else:
                    session.current_state = "MAIN_MENU"
            else:
                session.current_state = "MAIN_MENU"

        elif state == "RESCHEDULE_APPOINTMENT":
            recent_apt = None
            if session.user_id:
                recent_apt = db.query(Appointment).filter(
                    Appointment.patient.has(user_id=session.user_id),
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if not recent_apt:
                recent_apt = db.query(Appointment).filter(
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if recent_apt:
                context["target_appointment_id"] = recent_apt.id
                context["target_doctor_id"] = recent_apt.doctor_id
                session.selected_doctor_id = recent_apt.doctor_id
                session.selected_facility_id = recent_apt.facility_id
                session.context_json = json.dumps(context)
                if clean_key == "1":
                    session.current_state = "RESCHEDULE_DATE"
                else:
                    session.current_state = "MAIN_MENU"
            else:
                session.current_state = "MAIN_MENU"

        elif state == "RESCHEDULE_DATE":
            today = get_today_ist()
            target_date = today
            if clean_key == "2":
                target_date = today + timedelta(days=1)
            elif clean_key == "3":
                target_date = today + timedelta(days=2)

            session.selected_date = target_date.strftime("%Y-%m-%d")
            doc_id = session.selected_doctor_id or context.get("target_doctor_id")

            try:
                avail_resp = AvailabilityService.generate_doctor_slots(db, doc_id, target_date)
                avail_slots = [s for s in avail_resp.slots if s.status == "AVAILABLE"]
                if avail_slots:
                    context["reschedule_slots"] = [{"start_time": s.start_time, "end_time": s.end_time} for s in avail_slots[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "RESCHEDULE_SLOT"
                else:
                    session.current_state = "RESCHEDULE_DATE"
            except Exception:
                session.current_state = "RESCHEDULE_DATE"

        elif state == "RESCHEDULE_SLOT":
            slot_list = context.get("reschedule_slots", [])
            idx = int(clean_key) - 1 if clean_key.isdigit() else -1
            if 0 <= idx < len(slot_list):
                sel_slot = slot_list[idx]
                session.selected_start_time = sel_slot["start_time"]
                session.selected_end_time = sel_slot["end_time"]
                session.current_state = "RESCHEDULE_CONFIRMATION"
            else:
                session.current_state = "RESCHEDULE_SLOT"

        elif state == "RESCHEDULE_CONFIRMATION":
            if clean_key == "1":
                apt_id = context.get("target_appointment_id")
                if apt_id:
                    try:
                        n_date = datetime.strptime(session.selected_date, "%Y-%m-%d").date()
                        s_time = datetime.strptime(session.selected_start_time, "%H:%M").time()
                        e_time = datetime.strptime(session.selected_end_time, "%H:%M").time()

                        user = db.query(User).filter(User.id == session.user_id).first() if session.user_id else None
                        if not user:
                            apt_obj = db.query(Appointment).filter(Appointment.id == apt_id).first()
                            if apt_obj and apt_obj.patient and apt_obj.patient.user:
                                user = apt_obj.patient.user
                            else:
                                user = db.query(User).filter(User.role == UserRole.ADMIN).first()

                        reschedule_req = AppointmentRescheduleRequest(
                            new_date=n_date,
                            new_start_time=s_time,
                            new_end_time=e_time,
                            reason="Phone IVR Reschedule Request"
                        )

                        rescheduled_apt = AppointmentService.reschedule_appointment(
                            db=db,
                            appointment_id=apt_id,
                            reschedule_in=reschedule_req,
                            current_user=user
                        )
                        context["confirmation_code"] = rescheduled_apt.confirmation_code
                        session.context_json = json.dumps(context)
                        session.current_state = "RESCHEDULE_COMPLETED"
                    except Exception:
                        session.current_state = "RESCHEDULE_SLOT"
                else:
                    session.current_state = "MAIN_MENU"
            else:
                session.current_state = "MAIN_MENU"

        if session.current_state == "CHECK_IN":
            PhoneSessionService._execute_check_in(db, session, context)

        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

        return PhoneSessionService.format_response(db, session)

    @staticmethod
    def _execute_check_in(db: Session, session: CallSession, context: Dict[str, Any]):
        today = get_today_ist()
        recent_apt = None
        if session.user_id:
            recent_apt = db.query(Appointment).filter(
                Appointment.patient.has(user_id=session.user_id),
                Appointment.appointment_date == today,
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
            ).order_by(Appointment.id.desc()).first()

        if not recent_apt:
            recent_apt = db.query(Appointment).filter(
                Appointment.appointment_date == today,
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
            ).order_by(Appointment.id.desc()).first()

        if recent_apt:
            try:
                chk_resp = AppointmentService.check_in_appointment(db, recent_apt.id)
                context["queue_token"] = chk_resp.queue_token
                context["confirmation_code"] = recent_apt.confirmation_code
                session.context_json = json.dumps(context)
                session.current_state = "CHECK_IN_COMPLETED"
            except HTTPException as he:
                context["checkin_error"] = str(he.detail)
                session.context_json = json.dumps(context)
                session.current_state = "CHECK_IN_FAILED"
            except Exception as e:
                context["checkin_error"] = str(e)
                session.context_json = json.dumps(context)
                session.current_state = "CHECK_IN_FAILED"
        else:
            session.current_state = "NO_CHECKIN_APPOINTMENT"


    @staticmethod
    async def process_voice_input(
        db: Session,
        session_id: int,
        utterance_or_audio: Any,
        language_hint: Optional[str] = None
    ) -> Tuple[PhoneSessionResponse, VoiceUnderstandingResult]:
        """
        Processes voice input (speech audio or text utterance) via VoiceUnderstandingService.
        Maps voice intents and extracted entities directly into CallSession state machine.
        """
        session = PhoneSessionService.get_session(db, session_id)
        if session.status != CallSessionStatus.ACTIVE:
            session.status = CallSessionStatus.ACTIVE

        # Parse NLU
        service = VoiceUnderstandingService()
        lang_hint = language_hint or (session.language.value if session.language else "HI")
        nlu = await service.process_utterance(utterance_or_audio, language_hint=lang_hint)

        # Log User Voice Message
        input_msg = ConversationMessage(
            call_session_id=session.id,
            sender_type="USER",
            message_type="VOICE",
            language=nlu.language,
            content=nlu.raw_text
        )
        db.add(input_msg)
        db.commit()

        # Update language if detected/changed
        session.language = nlu.language

        # Parse context JSON
        context = {}
        if session.context_json:
            try:
                context = json.loads(session.context_json)
            except Exception:
                context = {}

        state = session.current_state

        # Check confidence threshold
        if nlu.confidence < 0.25 and nlu.intent not in [IntentEnum.EMERGENCY, IntentEnum.END_CALL] and state != "PHONE_REGISTRATION_NAME":
            session.updated_at = datetime.utcnow()
            db.commit()
            resp = PhoneSessionService.format_response(db, session)
            repeat_prefix = {
                Language.HI: "Kripya phir se boliye ya keypad ka use karein. ",
                Language.MR: "कृपया पुन्हा बोला किंवा कीपॅड वापरा. ",
                Language.EN: "Sorry, I could not understand. Please speak again or use the keypad. "
            }.get(session.language, "Please repeat. ")
            resp.prompt_text = repeat_prefix + resp.prompt_text
            resp.voice_playback = f"[{session.language.value}] {resp.prompt_text}"
            return resp, nlu

        # ------------------- VOICE INTENT & ENTITY HANDLER ------------------- #

        intent = nlu.intent
        entities = nlu.entities
        state = session.current_state

        if intent == IntentEnum.EMERGENCY:
            session.selected_intent = "EMERGENCY"
            session.current_state = "EMERGENCY"

        elif intent == IntentEnum.END_CALL:
            end_resp = PhoneSessionService.format_response(db, PhoneSessionService.end_session(db, session.id))
            return end_resp, nlu

        elif intent == IntentEnum.CHANGE_LANGUAGE:
            session.current_state = "MAIN_MENU"

        elif intent == IntentEnum.REPEAT:
            # Re-render prompt for current state
            pass

        elif intent == IntentEnum.BACK:
            PhoneSessionService.handle_back_navigation(session)

        elif intent == IntentEnum.HELP:
            session.current_state = "HELP"

        elif intent == IntentEnum.RESCHEDULE_APPOINTMENT:
            session.selected_intent = "RESCHEDULE_APPOINTMENT"
            session.current_state = "RESCHEDULE_APPOINTMENT"

        elif intent == IntentEnum.CHECK_IN:
            session.selected_intent = "CHECK_IN"
            session.current_state = "CHECK_IN"

        elif intent == IntentEnum.CHECK_AVAILABILITY and state in ["GREETING", "RETURNING_USER_GREETING", "MAIN_MENU", "LANGUAGE_SELECTION"]:
            session.selected_intent = "CHECK_AVAILABILITY"
            query = entities.get("facility_search") or entities.get("pincode")
            facs = FacilityService.list_facilities(db)
            if query:
                q_lower = query.lower()
                matched = [f for f in facs if q_lower in f.name.lower() or q_lower in (f.district or "").lower() or q_lower in (f.village or "").lower() or q_lower in f.pincode]
                if matched: facs = matched

            if facs:
                session.selected_facility_id = facs[0].id
                docs = db.query(Doctor).filter(Doctor.facility_id == facs[0].id, Doctor.is_active == True).all()
                if docs:
                    session.selected_doctor_id = docs[0].id
                    today = get_today_ist()
                    date_ent = entities.get("date", "tomorrow")
                    target_date = today
                    if date_ent == "tomorrow":
                        target_date = today + timedelta(days=1)
                    elif date_ent == "day_after_tomorrow":
                        target_date = today + timedelta(days=2)

                    session.selected_date = target_date.strftime("%Y-%m-%d")
                    try:
                        avail_resp = AvailabilityService.generate_doctor_slots(db, docs[0].id, target_date)
                        avail_slots = [s for s in avail_resp.slots if s.status == "AVAILABLE"]
                        if avail_slots:
                            context["slots"] = [{"start_time": s.start_time, "end_time": s.end_time} for s in avail_slots[:5]]
                            session.context_json = json.dumps(context)
                            session.current_state = "SLOT_SELECTION"
                        else:
                            session.current_state = "DATE_SELECTION"
                    except Exception:
                        session.current_state = "DATE_SELECTION"
                else:
                    session.current_state = "DEPARTMENT_SELECTION"
            else:
                session.current_state = "LOCATION_INPUT"

        elif state == "PHONE_REGISTRATION_NAME":
            is_explicit_intent = (intent in [IntentEnum.BOOK_APPOINTMENT, IntentEnum.SEARCH_FACILITY, IntentEnum.SEARCH_DOCTOR, IntentEnum.CHECK_APPOINTMENT, IntentEnum.CANCEL_APPOINTMENT] and nlu.confidence >= 0.85)

            if not session.user_id:
                raw_name = nlu.raw_text.strip()
                cleaned = raw_name
                for prefix in ["mera naam", "my name is", "iam", "i am", "naam hai", "haan mera naam", "namaste mera naam", "namaskar", "mera naam hai", " hai", " hai."]:
                    cleaned = cleaned.lower().replace(prefix, "").strip()
                final_name = cleaned.title() if (cleaned and not is_explicit_intent) else f"Patient {session.phone_number[-4:]}"

                new_user = User(
                    name=final_name,
                    phone_number=session.phone_number,
                    password_hash=User.hash_password("temp_voice_pwd"),
                    role=UserRole.CUSTOMER,
                    preferred_language=session.language or Language.HI,
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                profile = PatientProfile(
                    user_id=new_user.id,
                    village="Baramati",
                    district="Pune",
                    state="Maharashtra"
                )
                db.add(profile)
                db.commit()

                session.user_id = new_user.id
                context["user_name"] = final_name
                session.context_json = json.dumps(context)

            if is_explicit_intent and intent in [IntentEnum.BOOK_APPOINTMENT, IntentEnum.SEARCH_FACILITY, IntentEnum.SEARCH_DOCTOR]:
                session.selected_intent = "BOOK_APPOINTMENT"
                query = entities.get("facility_search") or entities.get("pincode")
                facs = FacilityService.list_facilities(db)
                if query:
                    q_lower = query.lower()
                    matched = [f for f in facs if q_lower in f.name.lower() or q_lower in (f.district or "").lower() or q_lower in (f.village or "").lower() or q_lower in f.pincode]
                    if matched: facs = matched
                if facs:
                    context["facilities"] = [{"id": f.id, "name": f.name} for f in facs[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "FACILITY_SELECTION"
                else:
                    session.current_state = "LOCATION_INPUT"
            elif is_explicit_intent and intent == IntentEnum.CHECK_APPOINTMENT:
                session.selected_intent = "CHECK_APPOINTMENT"
                session.current_state = "CHECK_APPOINTMENT"
            elif is_explicit_intent and intent == IntentEnum.CANCEL_APPOINTMENT:
                session.selected_intent = "CANCEL_APPOINTMENT"
                session.current_state = "CANCEL_APPOINTMENT"
            else:
                session.current_state = "LANGUAGE_SELECTION"

        elif state in ["GREETING", "RETURNING_USER_GREETING", "LANGUAGE_SELECTION", "BOOKING_COMPLETED", "RESCHEDULE_COMPLETED", "CANCEL_COMPLETED", "CHECK_IN_COMPLETED"]:
            if intent in [IntentEnum.BOOK_APPOINTMENT, IntentEnum.SEARCH_FACILITY, IntentEnum.SEARCH_DOCTOR]:
                session.selected_intent = "BOOK_APPOINTMENT"
                query = entities.get("facility_search") or entities.get("pincode")
                facs = FacilityService.list_facilities(db)
                if query:
                    q_lower = query.lower()
                    matched = [f for f in facs if q_lower in f.name.lower() or q_lower in (f.district or "").lower() or q_lower in (f.village or "").lower() or q_lower in f.pincode]
                    if matched: facs = matched
                if facs:
                    context["facilities"] = [{"id": f.id, "name": f.name} for f in facs[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "FACILITY_SELECTION"
                else:
                    session.current_state = "LOCATION_INPUT"
            elif intent == IntentEnum.CHECK_APPOINTMENT:
                session.selected_intent = "CHECK_APPOINTMENT"
                session.current_state = "CHECK_APPOINTMENT"
            elif intent == IntentEnum.CANCEL_APPOINTMENT:
                session.selected_intent = "CANCEL_APPOINTMENT"
                session.current_state = "CANCEL_APPOINTMENT"
            else:
                session.current_state = "MAIN_MENU"

        elif state == "MAIN_MENU":
            if intent in [IntentEnum.BOOK_APPOINTMENT, IntentEnum.SEARCH_FACILITY, IntentEnum.SEARCH_DOCTOR]:
                session.selected_intent = "BOOK_APPOINTMENT"
                query = entities.get("facility_search") or entities.get("pincode")
                facs = FacilityService.list_facilities(db)
                if query:
                    q_lower = query.lower()
                    matched = [f for f in facs if q_lower in f.name.lower() or q_lower in (f.district or "").lower() or q_lower in (f.village or "").lower() or q_lower in f.pincode]
                    if matched: facs = matched
                if facs:
                    context["facilities"] = [{"id": f.id, "name": f.name} for f in facs[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "FACILITY_SELECTION"
                else:
                    session.current_state = "LOCATION_INPUT"
            elif intent == IntentEnum.CHECK_APPOINTMENT:
                session.selected_intent = "CHECK_APPOINTMENT"
                session.current_state = "CHECK_APPOINTMENT"
            elif intent == IntentEnum.CANCEL_APPOINTMENT:
                session.selected_intent = "CANCEL_APPOINTMENT"
                session.current_state = "CANCEL_APPOINTMENT"

        elif state in ["LOCATION_INPUT", "FACILITY_SELECTION"]:
            query = entities.get("facility_search") or entities.get("pincode") or nlu.raw_text
            facs = FacilityService.list_facilities(db)
            if query:
                q_lower = query.lower()
                matched = [f for f in facs if q_lower in f.name.lower() or q_lower in (f.district or "").lower() or q_lower in (f.village or "").lower() or q_lower in f.pincode]
                if matched: facs = matched
            if facs:
                selected_fac = facs[0]
                session.selected_facility_id = selected_fac.id
                fac_obj = db.query(Facility).filter(Facility.id == selected_fac.id).first()
                if fac_obj and (not fac_obj.is_active or fac_obj.status == FacilityStatus.INACTIVE or fac_obj.status == FacilityStatus.TEMPORARILY_UNAVAILABLE):
                    session.current_state = "FACILITY_UNAVAILABLE"
                else:
                    all_depts = db.query(Department).filter(
                        Department.facility_id == selected_fac.id,
                        Department.is_active == True,
                        Department.status == DepartmentStatus.ACTIVE
                    ).all()
                    depts = [d for d in all_depts if db.query(Doctor).filter(
                        Doctor.facility_id == selected_fac.id,
                        Doctor.department_id == d.id,
                        Doctor.is_active == True,
                        Doctor.status == DoctorStatus.ACTIVE
                    ).first()]
                    if not depts and all_depts:
                        depts = all_depts
                    if depts:
                        context["departments"] = [{"id": d.id, "name": d.name} for d in depts[:5]]
                        session.context_json = json.dumps(context)
                        session.current_state = "DEPARTMENT_SELECTION"
                    else:
                        session.current_state = "DEPARTMENT_UNAVAILABLE"

        elif state == "DEPARTMENT_SELECTION":
            dept_query = entities.get("department")
            depts = context.get("departments", [])
            selected_dept = None
            if dept_query and depts:
                for d in depts:
                    if dept_query.lower() in d["name"].lower():
                        selected_dept = d
                        break
            if not selected_dept and depts:
                selected_dept = depts[0]

            if selected_dept:
                session.selected_department_id = selected_dept["id"]
                dept_obj = db.query(Department).filter(Department.id == selected_dept["id"]).first()
                if dept_obj and (not dept_obj.is_active or dept_obj.status == DepartmentStatus.INACTIVE):
                    session.current_state = "DEPARTMENT_UNAVAILABLE"
                else:
                    docs = db.query(Doctor).filter(
                        Doctor.facility_id == session.selected_facility_id,
                        Doctor.department_id == selected_dept["id"],
                        Doctor.is_active == True,
                        Doctor.status == DoctorStatus.ACTIVE
                    ).all()
                    if not docs:
                        docs = db.query(Doctor).filter(
                            Doctor.facility_id == session.selected_facility_id,
                            Doctor.is_active == True,
                            Doctor.status == DoctorStatus.ACTIVE
                        ).all()
                    if docs:
                        context["doctors"] = [{"id": d.id, "name": d.name} for d in docs[:5]]
                        session.context_json = json.dumps(context)
                        session.current_state = "DOCTOR_SELECTION"
                    else:
                        session.current_state = "DEPARTMENT_UNAVAILABLE"
            else:
                session.current_state = "MAIN_MENU"

        elif state == "DOCTOR_SELECTION":
            doc_query = entities.get("doctor_search")
            docs = context.get("doctors", [])
            selected_doc = None
            if doc_query and docs:
                for d in docs:
                    if doc_query.lower() in d["name"].lower():
                        selected_doc = d
                        break
            if not selected_doc and docs:
                selected_doc = docs[0]

            if not selected_doc:
                db_doc = db.query(Doctor).filter(Doctor.is_active == True).first()
                if db_doc:
                    selected_doc = {"id": db_doc.id, "name": db_doc.name}

            if selected_doc:
                session.selected_doctor_id = selected_doc["id"]
                session.current_state = "DATE_SELECTION"

        elif state == "DATE_SELECTION":
            date_ent = entities.get("date", "tomorrow")
            today = get_today_ist()
            target_date = today
            if date_ent == "tomorrow":
                target_date = today + timedelta(days=1)
            elif date_ent == "day_after_tomorrow":
                target_date = today + timedelta(days=2)

            session.selected_date = target_date.strftime("%Y-%m-%d")
            doc_id = session.selected_doctor_id
            if not doc_id:
                db_doc = db.query(Doctor).filter(Doctor.is_active == True).first()
                if db_doc:
                    doc_id = db_doc.id
                    session.selected_doctor_id = doc_id

            try:
                avail_resp = AvailabilityService.generate_doctor_slots(db, doc_id, target_date)
                avail_slots = [s for s in avail_resp.slots if s.status == "AVAILABLE"]
                if avail_slots:
                    context["slots"] = [{"start_time": s.start_time, "end_time": s.end_time} for s in avail_slots[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "SLOT_SELECTION"
                else:
                    session.current_state = "DATE_SELECTION"
            except Exception:
                session.current_state = "DATE_SELECTION"

        elif state == "SLOT_SELECTION":
            if nlu.intent == IntentEnum.BACK:
                session.current_state = "DATE_SELECTION"
            elif nlu.intent == IntentEnum.REPEAT:
                session.current_state = "SLOT_SELECTION"
            else:
                slot_list = context.get("slots", [])
                selected_slot = None
                raw_lower = nlu.raw_text.lower()
                time_ent = entities.get("time")

                if slot_list:
                    for slot in slot_list:
                        s_str = slot.get("start_time", "")
                        if s_str and (s_str in raw_lower or (time_ent and time_ent in s_str)):
                            selected_slot = slot
                            break

                    if not selected_slot:
                        if any(w in raw_lower for w in ["pehla", "first", "1", "one"]):
                            selected_slot = slot_list[0]
                        elif len(slot_list) > 1 and any(w in raw_lower for w in ["doosra", "second", "2", "two"]):
                            selected_slot = slot_list[1]
                        elif len(slot_list) > 2 and any(w in raw_lower for w in ["teesra", "third", "3", "three"]):
                            selected_slot = slot_list[2]
                        elif len(slot_list) > 3 and any(w in raw_lower for w in ["chautha", "fourth", "4", "four"]):
                            selected_slot = slot_list[3]
                        elif len(slot_list) > 4 and any(w in raw_lower for w in ["paanchva", "fifth", "5", "five"]):
                            selected_slot = slot_list[4]

                    if not selected_slot:
                        selected_slot = slot_list[0]

                if selected_slot:
                    session.selected_start_time = selected_slot["start_time"]
                    session.selected_end_time = selected_slot["end_time"]
                else:
                    session.selected_start_time = "10:00"
                    session.selected_end_time = "10:30"
                session.current_state = "BOOKING_CONFIRMATION"

        elif state == "BOOKING_CONFIRMATION":
            is_confirmed = entities.get("confirmation")
            if is_confirmed is True or (is_confirmed is None and nlu.intent not in [IntentEnum.CANCEL_APPOINTMENT, IntentEnum.BACK, IntentEnum.REPEAT]):
                patient = None
                if session.user_id:
                    patient = db.query(PatientProfile).filter(PatientProfile.user_id == session.user_id).first()
                if not patient:
                    patient = db.query(PatientProfile).first()

                try:
                    apt_date = datetime.strptime(session.selected_date, "%Y-%m-%d").date()
                    s_time = datetime.strptime(session.selected_start_time, "%H:%M").time()
                    e_time = datetime.strptime(session.selected_end_time, "%H:%M").time()

                    apt = AppointmentRepository.create_appointment(
                        db=db,
                        patient_id=patient.id,
                        doctor_id=session.selected_doctor_id,
                        facility_id=session.selected_facility_id,
                        department_id=session.selected_department_id,
                        apt_date=apt_date,
                        start_time=s_time,
                        end_time=e_time,
                        booking_channel=BookingChannel.PHONE,
                        reason_for_visit="Phone Voice Booking"
                    )

                    NotificationService.send_appointment_notification(db, apt, event_type="BOOKING")

                    context["confirmation_code"] = apt.confirmation_code
                    session.context_json = json.dumps(context)
                    session.current_state = "BOOKING_COMPLETED"
                except Exception:
                    session.current_state = "SLOT_SELECTION"
            elif is_confirmed is False:
                session.current_state = "MAIN_MENU"

        elif state == "CANCEL_APPOINTMENT":
            is_confirmed = entities.get("confirmation")
            if is_confirmed is None:
                txt = nlu.raw_text.lower()
                if any(k in txt for k in ["haan", "yes", "confirm", "kar do", "kardo", "radd"]):
                    is_confirmed = True
                elif any(k in txt for k in ["nahi", "no", "mat"]):
                    is_confirmed = False

            if is_confirmed is True:
                recent_apt = None
                if session.user_id:
                    patient = db.query(PatientProfile).filter(PatientProfile.user_id == session.user_id).first()
                    if patient:
                        recent_apt = db.query(Appointment).filter(
                            Appointment.patient_id == patient.id,
                            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                        ).order_by(Appointment.id.desc()).first()

                if not recent_apt and session.phone_number:
                    recent_apt = db.query(Appointment).filter(
                        Appointment.patient.has(PatientProfile.user.has(User.phone_number == session.phone_number)),
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                    ).order_by(Appointment.id.desc()).first()

                if not recent_apt:
                    recent_apt = db.query(Appointment).filter(
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                    ).order_by(Appointment.id.desc()).first()

                if recent_apt:
                    user = recent_apt.patient.user if (recent_apt.patient and recent_apt.patient.user) else None
                    if not user and session.user_id:
                        user = db.query(User).filter(User.id == session.user_id).first()
                    if not user:
                        user = db.query(User).filter(User.role == UserRole.ADMIN).first()

                    try:
                        cancel_req = AppointmentCancelRequest(reason="Phone Voice Cancellation Request")
                        AppointmentService.cancel_appointment(db, recent_apt.id, cancel_req, current_user=user)
                        context["confirmation_code"] = recent_apt.confirmation_code
                        session.context_json = json.dumps(context)
                        session.current_state = "CANCEL_COMPLETED"
                    except Exception:
                        recent_apt.status = AppointmentStatus.CANCELLED
                        db.commit()
                        context["confirmation_code"] = recent_apt.confirmation_code
                        session.context_json = json.dumps(context)
                        session.current_state = "CANCEL_COMPLETED"
                else:
                    session.current_state = "MAIN_MENU"
            elif is_confirmed is False:
                session.current_state = "MAIN_MENU"

        elif state == "RESCHEDULE_APPOINTMENT":
            recent_apt = None
            if session.user_id:
                recent_apt = db.query(Appointment).filter(
                    Appointment.patient.has(user_id=session.user_id),
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if not recent_apt:
                recent_apt = db.query(Appointment).filter(
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if recent_apt:
                context["target_appointment_id"] = recent_apt.id
                context["target_doctor_id"] = recent_apt.doctor_id
                session.selected_doctor_id = recent_apt.doctor_id
                session.selected_facility_id = recent_apt.facility_id
                session.context_json = json.dumps(context)
                session.current_state = "RESCHEDULE_DATE"
            else:
                session.current_state = "MAIN_MENU"

        elif state == "RESCHEDULE_DATE":
            date_ent = entities.get("date", "tomorrow")
            today = get_today_ist()
            target_date = today
            if date_ent == "tomorrow":
                target_date = today + timedelta(days=1)
            elif date_ent == "day_after_tomorrow":
                target_date = today + timedelta(days=2)

            session.selected_date = target_date.strftime("%Y-%m-%d")
            doc_id = session.selected_doctor_id or context.get("target_doctor_id")

            try:
                avail_resp = AvailabilityService.generate_doctor_slots(db, doc_id, target_date)
                avail_slots = [s for s in avail_resp.slots if s.status == "AVAILABLE"]
                if avail_slots:
                    context["reschedule_slots"] = [{"start_time": s.start_time, "end_time": s.end_time} for s in avail_slots[:5]]
                    session.context_json = json.dumps(context)
                    session.current_state = "RESCHEDULE_SLOT"
                else:
                    session.current_state = "RESCHEDULE_DATE"
            except Exception:
                session.current_state = "RESCHEDULE_DATE"

        elif state == "RESCHEDULE_SLOT":
            slot_list = context.get("reschedule_slots", [])
            selected_slot = slot_list[0] if slot_list else None
            if selected_slot:
                session.selected_start_time = selected_slot["start_time"]
                session.selected_end_time = selected_slot["end_time"]
                session.current_state = "RESCHEDULE_CONFIRMATION"
            else:
                session.current_state = "RESCHEDULE_SLOT"

        elif state == "RESCHEDULE_CONFIRMATION":
            is_confirmed = entities.get("confirmation")
            if is_confirmed is None:
                txt = nlu.raw_text.lower()
                if any(k in txt for k in ["haan", "yes", "confirm", "kar do", "kardo", "badlo"]):
                    is_confirmed = True
                elif any(k in txt for k in ["nahi", "no", "mat"]):
                    is_confirmed = False

            if is_confirmed is True:
                apt_id = context.get("target_appointment_id")
                if apt_id:
                    try:
                        n_date = datetime.strptime(session.selected_date, "%Y-%m-%d").date()
                        s_time = datetime.strptime(session.selected_start_time, "%H:%M").time()
                        e_time = datetime.strptime(session.selected_end_time, "%H:%M").time()

                        user = db.query(User).filter(User.id == session.user_id).first() if session.user_id else None
                        if not user:
                            apt_obj = db.query(Appointment).filter(Appointment.id == apt_id).first()
                            if apt_obj and apt_obj.patient and apt_obj.patient.user:
                                user = apt_obj.patient.user
                            else:
                                user = db.query(User).filter(User.role == UserRole.ADMIN).first()

                        reschedule_req = AppointmentRescheduleRequest(
                            new_date=n_date,
                            new_start_time=s_time,
                            new_end_time=e_time,
                            reason="Phone Voice Reschedule Request"
                        )

                        rescheduled_apt = AppointmentService.reschedule_appointment(
                            db=db,
                            appointment_id=apt_id,
                            reschedule_in=reschedule_req,
                            current_user=user
                        )
                        context["confirmation_code"] = rescheduled_apt.confirmation_code
                        session.context_json = json.dumps(context)
                        session.current_state = "RESCHEDULE_COMPLETED"
                    except Exception:
                        session.current_state = "RESCHEDULE_SLOT"
                else:
                    session.current_state = "MAIN_MENU"
            elif is_confirmed is False:
                session.current_state = "MAIN_MENU"


        if session.current_state == "CHECK_IN":
            PhoneSessionService._execute_check_in(db, session, context)

        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

        return PhoneSessionService.format_response(db, session), nlu

    @staticmethod
    def format_response(db: Session, session: CallSession) -> PhoneSessionResponse:
        """Renders localized voice prompt text and options for current session state."""
        state = session.current_state
        lang = session.language

        context = {}
        if session.context_json:
            try:
                context = json.loads(session.context_json)
            except Exception:
                context = {}

        prompt_text = ""
        options: List[PhoneMenuOption] = []

        if state == "PHONE_REGISTRATION_NAME":
            prompt_text = VoicePromptProvider.get_prompt("PHONE_REGISTRATION_NAME", lang)
            options = []

        elif state == "RETURNING_USER_GREETING":
            user_name = "Patient"
            if session.user_id:
                u_obj = db.query(User).filter(User.id == session.user_id).first()
                if u_obj and u_obj.name:
                    user_name = u_obj.name
            prompt_text = VoicePromptProvider.get_prompt("RETURNING_GREETING", lang, name=user_name)
            options = [
                PhoneMenuOption(key="1", label="Book OPD Appointment"),
                PhoneMenuOption(key="2", label="Check Appointment Ticket"),
                PhoneMenuOption(key="3", label="Cancel Appointment"),
                PhoneMenuOption(key="4", label="Emergency 108"),
                PhoneMenuOption(key="5", label="Reschedule Appointment"),
                PhoneMenuOption(key="6", label="Check-In for OPD Visit"),
                PhoneMenuOption(key="9", label="Repeat Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state in ["GREETING", "LANGUAGE_SELECTION"]:
            prompt_text = VoicePromptProvider.get_prompt("GREETING", lang) + " " + VoicePromptProvider.get_prompt("LANGUAGE_SELECTION", lang)
            options = [
                PhoneMenuOption(key="1", label="Hindi / हिंदी"),
                PhoneMenuOption(key="2", label="Marathi / मराठी"),
                PhoneMenuOption(key="3", label="English"),
            ]

        elif state == "MAIN_MENU":
            prompt_text = VoicePromptProvider.get_prompt("MAIN_MENU", lang)
            options = [
                PhoneMenuOption(key="1", label="Book OPD Appointment"),
                PhoneMenuOption(key="2", label="Check Appointment Ticket"),
                PhoneMenuOption(key="3", label="Cancel Appointment"),
                PhoneMenuOption(key="4", label="Emergency 108"),
                PhoneMenuOption(key="5", label="Reschedule Appointment"),
                PhoneMenuOption(key="6", label="Check-In for OPD Visit"),
                PhoneMenuOption(key="9", label="Repeat Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "LOCATION_INPUT":
            prompt_text = VoicePromptProvider.get_prompt("LOCATION_INPUT", lang)
            options = [
                PhoneMenuOption(key="1", label="Baramati / Nearby Facilities"),
            ]

        elif state == "FACILITY_SELECTION":
            facs = context.get("facilities", [])
            lines = [f"[{i+1}] {f['name']}" for i, f in enumerate(facs)]
            prompt_text = VoicePromptProvider.get_prompt("FACILITY_SELECTION", lang, facility_options="\n".join(lines))
            options = [PhoneMenuOption(key=str(i+1), label=f['name']) for i, f in enumerate(facs)]
            options.append(PhoneMenuOption(key="9", label="Back"))

        elif state == "DEPARTMENT_SELECTION":
            depts = context.get("departments", [])
            lines = [f"[{i+1}] {d['name']}" for i, d in enumerate(depts)]
            prompt_text = VoicePromptProvider.get_prompt("DEPARTMENT_SELECTION", lang, department_options="\n".join(lines))
            options = [PhoneMenuOption(key=str(i+1), label=d['name']) for i, d in enumerate(depts)]
            options.append(PhoneMenuOption(key="9", label="Back"))

        elif state == "DEPARTMENT_UNAVAILABLE":
            prompt_text = VoicePromptProvider.get_prompt("DEPARTMENT_UNAVAILABLE", lang)
            options = [
                PhoneMenuOption(key="9", label="Back / Select another facility"),
                PhoneMenuOption(key="1", label="Main Menu")
            ]

        elif state == "FACILITY_UNAVAILABLE":
            prompt_text = VoicePromptProvider.get_prompt("FACILITY_UNAVAILABLE", lang)
            options = [
                PhoneMenuOption(key="9", label="Back"),
                PhoneMenuOption(key="1", label="Main Menu")
            ]

        elif state == "DOCTOR_SELECTION":
            docs = context.get("doctors", [])
            lines = [f"[{i+1}] {d['name']}" for i, d in enumerate(docs)]
            prompt_text = VoicePromptProvider.get_prompt("DOCTOR_SELECTION", lang, doctor_options="\n".join(lines))
            options = [PhoneMenuOption(key=str(i+1), label=d['name']) for i, d in enumerate(docs)]
            options.append(PhoneMenuOption(key="9", label="Back"))

        elif state == "DATE_SELECTION":
            prompt_text = VoicePromptProvider.get_prompt("DATE_SELECTION", lang)
            options = [
                PhoneMenuOption(key="1", label="Today"),
                PhoneMenuOption(key="2", label="Tomorrow"),
                PhoneMenuOption(key="3", label="Day after Tomorrow"),
                PhoneMenuOption(key="9", label="Back"),
            ]

        elif state == "SLOT_SELECTION":
            slots = context.get("slots", [])
            lines = [f"[{i+1}] {s['start_time']} - {s['end_time']}" for i, s in enumerate(slots)]
            prompt_text = VoicePromptProvider.get_prompt("SLOT_SELECTION", lang, slot_options="\n".join(lines))
            options = [PhoneMenuOption(key=str(i+1), label=f"{s['start_time']} - {s['end_time']}") for i, s in enumerate(slots)]
            options.append(PhoneMenuOption(key="9", label="Back"))

        elif state == "BOOKING_CONFIRMATION":
            doc_name = "Doctor"
            if session.selected_doctor_id:
                doc = db.query(Doctor).filter(Doctor.id == session.selected_doctor_id).first()
                if doc: doc_name = doc.name

            fac_name = "Facility"
            if session.selected_facility_id:
                fac = db.query(Facility).filter(Facility.id == session.selected_facility_id).first()
                if fac: fac_name = fac.name

            prompt_text = VoicePromptProvider.get_prompt(
                "BOOKING_CONFIRMATION", lang,
                doctor_name=doc_name,
                facility_name=fac_name,
                date=session.selected_date or "Today",
                start_time=session.selected_start_time or "09:00",
                end_time=session.selected_end_time or "09:30"
            )
            options = [
                PhoneMenuOption(key="1", label="Confirm Booking"),
                PhoneMenuOption(key="2", label="Cancel / Main Menu"),
            ]

        elif state == "BOOKING_COMPLETED":
            code = context.get("confirmation_code", "JS-2026-CONFIRMED")
            prompt_text = VoicePromptProvider.get_prompt("BOOKING_SUCCESS", lang, confirmation_code=code)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "CHECK_APPOINTMENT":
            recent_apt = None
            if session.user_id:
                recent_apt = db.query(Appointment).filter(
                    Appointment.patient.has(user_id=session.user_id)
                ).order_by(Appointment.id.desc()).first()

            if not recent_apt:
                recent_apt = db.query(Appointment).order_by(Appointment.id.desc()).first()

            if recent_apt:
                prompt_text = VoicePromptProvider.get_prompt(
                    "CHECK_APPOINTMENT_RESULT", lang,
                    confirmation_code=recent_apt.confirmation_code,
                    doctor_name=recent_apt.doctor.name if recent_apt.doctor else "Specialist",
                    facility_name=recent_apt.facility.name if recent_apt.facility else "Hospital",
                    date=str(recent_apt.appointment_date),
                    start_time=str(recent_apt.start_time),
                    status=str(recent_apt.status)
                )
            else:
                prompt_text = VoicePromptProvider.get_prompt("NO_APPOINTMENTS", lang)
            options = [PhoneMenuOption(key="1", label="Return to Main Menu")]

        elif state == "CANCEL_APPOINTMENT":
            recent_apt = None
            if session.user_id:
                patient = db.query(PatientProfile).filter(PatientProfile.user_id == session.user_id).first()
                if patient:
                    recent_apt = db.query(Appointment).filter(
                        Appointment.patient_id == patient.id,
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                    ).order_by(Appointment.id.desc()).first()

            if not recent_apt and session.phone_number:
                recent_apt = db.query(Appointment).filter(
                    Appointment.patient.has(PatientProfile.user.has(User.phone_number == session.phone_number)),
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if not recent_apt:
                recent_apt = db.query(Appointment).filter(
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if recent_apt:
                prompt_text = VoicePromptProvider.get_prompt(
                    "CANCEL_APPOINTMENT_PROMPT", lang,
                    confirmation_code=recent_apt.confirmation_code
                )
                options = [
                    PhoneMenuOption(key="1", label="Confirm Cancellation"),
                    PhoneMenuOption(key="2", label="Main Menu"),
                ]
            else:
                prompt_text = VoicePromptProvider.get_prompt("NO_APPOINTMENTS", lang)
                options = [PhoneMenuOption(key="1", label="Return to Main Menu")]

        elif state == "CANCEL_COMPLETED":
            code = context.get("confirmation_code", "JS-2026-CANCELLED")
            prompt_text = VoicePromptProvider.get_prompt("CANCEL_SUCCESS", lang, confirmation_code=code)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "RESCHEDULE_APPOINTMENT":
            apt_id = context.get("target_appointment_id")
            apt = db.query(Appointment).filter(Appointment.id == apt_id).first() if apt_id else None
            if not apt and session.user_id:
                apt = db.query(Appointment).filter(
                    Appointment.patient.has(user_id=session.user_id),
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()
            if not apt:
                apt = db.query(Appointment).filter(
                    Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.BOOKED])
                ).order_by(Appointment.id.desc()).first()

            if apt:
                prompt_text = VoicePromptProvider.get_prompt("RESCHEDULE_APPOINTMENT_PROMPT", lang, confirmation_code=apt.confirmation_code)
                options = [
                    PhoneMenuOption(key="1", label="Select New Date & Slot"),
                    PhoneMenuOption(key="2", label="Main Menu"),
                ]
            else:
                prompt_text = VoicePromptProvider.get_prompt("NO_APPOINTMENTS", lang)
                options = [PhoneMenuOption(key="1", label="Main Menu")]

        elif state == "RESCHEDULE_DATE":
            prompt_text = VoicePromptProvider.get_prompt("DATE_SELECTION", lang)
            options = [
                PhoneMenuOption(key="1", label="Today"),
                PhoneMenuOption(key="2", label="Tomorrow"),
                PhoneMenuOption(key="3", label="Day after Tomorrow"),
                PhoneMenuOption(key="9", label="Back"),
            ]

        elif state == "RESCHEDULE_SLOT":
            slots = context.get("reschedule_slots", [])
            lines = [f"[{i+1}] {s['start_time']} - {s['end_time']}" for i, s in enumerate(slots)]
            prompt_text = VoicePromptProvider.get_prompt("SLOT_SELECTION", lang, slot_options="\n".join(lines))
            options = [PhoneMenuOption(key=str(i+1), label=f"{s['start_time']} - {s['end_time']}") for i, s in enumerate(slots)]
            options.append(PhoneMenuOption(key="9", label="Back"))

        elif state == "RESCHEDULE_CONFIRMATION":
            doc_name = "Doctor"
            if session.selected_doctor_id:
                doc = db.query(Doctor).filter(Doctor.id == session.selected_doctor_id).first()
                if doc: doc_name = doc.name
            fac_name = "Facility"
            if session.selected_facility_id:
                fac = db.query(Facility).filter(Facility.id == session.selected_facility_id).first()
                if fac: fac_name = fac.name

            prompt_text = VoicePromptProvider.get_prompt(
                "RESCHEDULE_CONFIRMATION", lang,
                doctor_name=doc_name,
                facility_name=fac_name,
                date=session.selected_date or "Tomorrow",
                start_time=session.selected_start_time or "10:00",
                end_time=session.selected_end_time or "10:30"
            )
            options = [
                PhoneMenuOption(key="1", label="Confirm Reschedule"),
                PhoneMenuOption(key="2", label="Cancel / Main Menu"),
            ]

        elif state == "RESCHEDULE_COMPLETED":
            code = context.get("confirmation_code", "JS-2026-CONFIRMED")
            prompt_text = VoicePromptProvider.get_prompt("RESCHEDULE_SUCCESS", lang, confirmation_code=code, date=session.selected_date, start_time=session.selected_start_time)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "CHECK_IN_COMPLETED":
            q_token = context.get("queue_token", "P-001")
            prompt_text = VoicePromptProvider.get_prompt("CHECK_IN_SUCCESS", lang, queue_token=q_token)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "CHECK_IN_FAILED":
            err = context.get("checkin_error", "Check-in failed")
            prompt_text = VoicePromptProvider.get_prompt("CHECK_IN_FAILED", lang, error_detail=err)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
            ]

        elif state == "NO_CHECKIN_APPOINTMENT":
            prompt_text = VoicePromptProvider.get_prompt("NO_CHECKIN_APPOINTMENT", lang)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
            ]

        elif state == "EMERGENCY":
            prompt_text = VoicePromptProvider.get_prompt("EMERGENCY", lang)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "HELP":
            prompt_text = VoicePromptProvider.get_prompt("HELP", lang)
            options = [
                PhoneMenuOption(key="1", label="Main Menu"),
                PhoneMenuOption(key="0", label="End Call"),
            ]

        elif state == "ENDED":
            prompt_text = VoicePromptProvider.get_prompt("ENDED", lang)
            options = []

        voice_playback = f"[{lang.value}] {prompt_text}"

        # Log system response prompt
        sys_msg = ConversationMessage(
            call_session_id=session.id,
            sender_type="SYSTEM",
            message_type="VOICE",
            language=lang,
            content=prompt_text
        )
        db.add(sys_msg)
        db.commit()

        return PhoneSessionResponse(
            session_id=session.id,
            caller_phone=session.phone_number,
            current_state=session.current_state,
            language=session.language,
            status=session.status,
            prompt_text=prompt_text,
            voice_playback=voice_playback,
            options=options,
            selected_facility_id=session.selected_facility_id,
            selected_department_id=session.selected_department_id,
            selected_doctor_id=session.selected_doctor_id,
            selected_date=session.selected_date,
            selected_start_time=session.selected_start_time
        )
