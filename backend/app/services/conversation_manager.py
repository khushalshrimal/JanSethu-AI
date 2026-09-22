import uuid
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.enums import Language
from app.schemas.nlu import NLUIntent, NLUEntities, NLUAnalysisResponse
from app.schemas.conversation import (
    ResponseType,
    ConversationMessage,
    ConversationState,
    ConversationRequest,
    ConversationResponse,
)
from app.services.llm_service import LLMService
from app.services.safety_engine import SafetyEngine, EmergencyLevel
from app.services.healthcare_tools import HealthcareToolService
from app.services.action_router import ActionRouter
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Stateful Conversation & Healthcare Tool Integration Engine for JanSethu AI.
    Handles session memory retention, entity merging, corrections, topic switching,
    dynamic missing field determination, real database tool execution, deterministic emergency preemption,
    location capture, mock ambulance requests, and natural response generation.
    """

    _sessions: Dict[str, ConversationState] = {}

    @classmethod
    def get_session(cls, session_id: str) -> Optional[ConversationState]:
        return cls._sessions.get(session_id)

    @classmethod
    def get_or_create_session(
        cls,
        session_id: Optional[str] = None,
        language_hint: Optional[str] = None
    ) -> ConversationState:
        if not session_id or session_id not in cls._sessions:
            sid = session_id or f"conv-{uuid.uuid4().hex[:10]}"
            lang = Language.HI
            if language_hint and language_hint.upper() in Language.__members__:
                lang = Language(language_hint.upper())

            cls._sessions[sid] = ConversationState(
                session_id=sid,
                language=lang,
                entities=NLUEntities(),
                missing_fields=[],
                history=[]
            )
        return cls._sessions[session_id or sid]

    @classmethod
    def clear_session(cls, session_id: str) -> None:
        if session_id in cls._sessions:
            del cls._sessions[session_id]

    @classmethod
    def clear_all_sessions(cls) -> None:
        cls._sessions.clear()

    @classmethod
    async def process_message(
        cls,
        request: ConversationRequest,
        db: Optional[Session] = None
    ) -> ConversationResponse:
        state = cls.get_or_create_session(request.session_id, request.language_hint)
        user_msg_text = request.message.strip()
        msg_lower = user_msg_text.lower()

        # Step 1: Run Deterministic Safety Engine Classification
        emerg_level, emerg_type, emerg_conf, matched_pats = SafetyEngine.classify_emergency(user_msg_text)

        # Step 2: Run LLM NLU Analysis
        current_context_dict = {
            "session_id": state.session_id,
            "intent": state.intent.value if state.intent else None,
            "patient_name": state.entities.patient_name,
            "patient_relation": state.entities.patient_relation,
            "city": state.entities.city,
            "location": state.entities.location,
            "facility": state.entities.facility or state.entities.facility_name,
            "doctor": state.entities.doctor or state.entities.doctor_name,
            "specialty": state.entities.specialty or state.entities.speciality,
            "speciality": state.entities.speciality or state.entities.specialty,
            "department": state.entities.department,
            "symptoms": state.entities.symptoms,
            "date": state.entities.date,
            "time": state.entities.time,
        }

        nlu_res: NLUAnalysisResponse = await LLMService.analyze_nlu(
            message=user_msg_text,
            conversation_context=current_context_dict,
            language_hint=request.language_hint
        )

        state.language = nlu_res.language

        # Merge newly extracted entities into state
        cls._merge_entities(state.entities, nlu_res.entities)

        # Step 3: Check for Emergency Resolution / Cancellation Phrase
        is_cancel_phrase = any(
            phrase in msg_lower for phrase in [
                "galti se emergency", "ab emergency nahi", "emergency cancel",
                "i am fine", "no emergency", "galti se bola", "sorry wrong",
                "emergency nahi hai"
            ]
        )

        if state.emergency_triggered and is_cancel_phrase:
            state.emergency_triggered = False
            state.emergency_status = "RESOLVED"
            state.emergency_resolved = True
            state.emergency_level = "NORMAL"

            cancel_msg = {
                Language.HI: "Samajh gaya, emergency mode cancel kar diya gaya hai. Main aapki samanya healthcare query ke liye madad karne ke liye taiyar hoon.",
                Language.MR: "समजले, आपत्कालीन मोड रद्द केला आहे. मी तुमच्या सामान्य आरोग्याच्या प्रश्नांसाठी मदत करण्यास तयार आहे.",
                Language.EN: "Understood, emergency mode has been cleared. I am ready to assist with your normal healthcare request."
            }.get(state.language, "Emergency status cleared. Returning to normal assistant flow.")

            state.history.append(ConversationMessage(role="user", content=user_msg_text))
            state.history.append(ConversationMessage(role="assistant", content=cancel_msg))
            state.updated_at = datetime.utcnow().isoformat()

            return ConversationResponse(
                session_id=state.session_id,
                response_type=ResponseType.ACKNOWLEDGE,
                assistant_message=cancel_msg,
                intent=NLUIntent.GENERAL_HELP,
                entities=state.entities,
                missing_fields=[],
                language=state.language,
                emergency=False,
                emergency_level="NORMAL",
                emergency_status="RESOLVED",
                raw_user_message=user_msg_text
            )

        # Step 4: Determine if Emergency Preemption is Active
        is_high_confidence_emergency = (
            emerg_level == EmergencyLevel.HIGH_CONFIDENCE_EMERGENCY or
            nlu_res.emergency or
            nlu_res.intent in [NLUIntent.EMERGENCY, NLUIntent.AMBULANCE_REQUEST, NLUIntent.EMERGENCY_FACILITY_SEARCH] or
            state.emergency_triggered
        )

        if is_high_confidence_emergency and not is_cancel_phrase:
            state.emergency_triggered = True
            state.emergency_level = emerg_level.value if emerg_level != EmergencyLevel.NORMAL else "HIGH_CONFIDENCE_EMERGENCY"
            state.emergency_type = emerg_type or state.emergency_type or "GENERAL_EMERGENCY"
            state.intent = NLUIntent.EMERGENCY

            # Extract location from user input or existing state entities
            loc_dict = cls._extract_or_update_location(state, user_msg_text)
            state.emergency_location = loc_dict

            has_valid_location = bool(
                loc_dict and (
                    loc_dict.get("city") or
                    loc_dict.get("location") or
                    loc_dict.get("pincode") or
                    loc_dict.get("address")
                )
            )

            if has_valid_location:
                state.emergency_status = "ASSISTANCE_SIMULATED"
                if not state.ambulance_request_id:
                    state.ambulance_request_id = f"AMB-MOCK-{uuid.uuid4().hex[:5].upper()}"
            else:
                state.emergency_status = "LOCATION_REQUIRED"

            # Query real DB for emergency-capable facilities if location is known
            emerg_facilities = []
            db_to_use = db
            close_db_after = False

            if has_valid_location:
                if db_to_use is None:
                    try:
                        db_to_use = SessionLocal()
                        close_db_after = True
                    except Exception:
                        db_to_use = None

                if db_to_use:
                    try:
                        emerg_facilities = HealthcareToolService.search_facilities(
                            db=db_to_use,
                            location=loc_dict.get("location"),
                            city=loc_dict.get("city"),
                            pincode=loc_dict.get("pincode"),
                            emergency_only=True
                        )
                    except Exception as e:
                        logger.error("Error searching emergency facilities: %s", str(e))
                    finally:
                        if close_db_after and db_to_use:
                            db_to_use.close()

            assistant_msg = cls._generate_phase6_emergency_response(
                state=state,
                lang=state.language,
                emerg_facilities=emerg_facilities
            )

            state.history.append(ConversationMessage(role="user", content=user_msg_text, intent=NLUIntent.EMERGENCY.value))
            state.history.append(ConversationMessage(role="assistant", content=assistant_msg))
            state.updated_at = datetime.utcnow().isoformat()

            return ConversationResponse(
                session_id=state.session_id,
                response_type=ResponseType.EMERGENCY,
                assistant_message=assistant_msg,
                intent=NLUIntent.EMERGENCY,
                entities=state.entities,
                missing_fields=[],
                language=state.language,
                emergency=True,
                emergency_level=state.emergency_level,
                emergency_type=state.emergency_type,
                emergency_status=state.emergency_status,
                emergency_location=state.emergency_location,
                ambulance_request_id=state.ambulance_request_id,
                requires_action="EMERGENCY_DISPATCH",
                raw_user_message=user_msg_text
            )

        # Step 5: Handle Entity Correction / Merging for Normal Intent
        new_ent = nlu_res.entities
        is_corr = new_ent.is_correction

        if is_corr:
            corr_field = new_ent.corrected_field or "city"
            if corr_field in ["city", "location"] and (new_ent.city or new_ent.location):
                val = new_ent.city or new_ent.location
                state.entities.city = val
                state.entities.location = val
            elif corr_field == "doctor" and new_ent.doctor:
                state.entities.doctor = new_ent.doctor
                state.entities.doctor_name = new_ent.doctor
            elif corr_field == "facility" and new_ent.facility:
                state.entities.facility = new_ent.facility
                state.entities.facility_name = new_ent.facility
            elif corr_field == "date" and new_ent.date:
                state.entities.date = new_ent.date
        else:
            cls._merge_entities(state.entities, new_ent)

        # Step 6: Intent Determination & Topic Switching
        if nlu_res.intent not in [NLUIntent.UNKNOWN, NLUIntent.PROVIDE_LOCATION, NLUIntent.PROVIDE_NAME]:
            state.intent = nlu_res.intent
        elif state.intent is None or state.intent == NLUIntent.UNKNOWN:
            state.intent = nlu_res.intent

        # Step 7: Determine missing fields
        missing_fields = cls._detect_missing_fields(state.intent, state.entities)
        state.missing_fields = missing_fields

        # Step 8: Classify Response Type
        response_type = cls._classify_response_type(state.intent, missing_fields, False)

        # Step 9: Execute Healthcare Tools against REAL Database
        tool_results: Dict[str, Any] = {}
        db_to_use = db
        close_db_after = False

        if db_to_use is None:
            try:
                db_to_use = SessionLocal()
                close_db_after = True
            except Exception:
                db_to_use = None

        if db_to_use:
            try:
                tool_results = cls._execute_healthcare_tools(
                    db=db_to_use,
                    intent=state.intent,
                    entities=state.entities,
                    missing_fields=missing_fields,
                    user_msg=user_msg_text,
                    user_id=request.user_id,
                    phone_number=request.phone_number
                )
            except Exception as exc:
                logger.error("Error executing healthcare tool: %s", str(exc))
            finally:
                if close_db_after and db_to_use:
                    db_to_use.close()

        # Update entities if tool execution produced booking/referral results
        if tool_results.get("referral_id"):
            state.entities.referral_id = tool_results["referral_id"]
            state.entities.appointment_id = tool_results["referral_id"]

        # Step 10: Generate Natural Assistant Response based on verified tool output
        assistant_msg = cls._generate_assistant_message(
            intent=state.intent,
            response_type=response_type,
            entities=state.entities,
            missing_fields=missing_fields,
            language=state.language,
            is_correction=is_corr,
            raw_user_msg=user_msg_text,
            tool_results=tool_results
        )

        # Step 11: Update Conversation History
        state.history.append(ConversationMessage(
            role="user",
            content=user_msg_text,
            intent=state.intent.value if state.intent else None
        ))
        state.history.append(ConversationMessage(
            role="assistant",
            content=assistant_msg
        ))
        state.updated_at = datetime.utcnow().isoformat()

        action_tag = None
        if response_type == ResponseType.SEARCH_REQUIRED:
            action_tag = "SEARCH_REQUIRED"
        elif response_type == ResponseType.BOOKING_REQUIRED:
            action_tag = "BOOKING_REQUIRED"
        elif response_type == ResponseType.ASK_CLARIFICATION:
            action_tag = "CLARIFICATION_REQUIRED"

        return ConversationResponse(
            session_id=state.session_id,
            response_type=response_type,
            assistant_message=assistant_msg,
            intent=state.intent,
            entities=state.entities,
            missing_fields=missing_fields,
            language=state.language,
            emergency=False,
            emergency_level=state.emergency_level,
            emergency_status=state.emergency_status,
            emergency_location=state.emergency_location,
            ambulance_request_id=state.ambulance_request_id,
            requires_action=action_tag,
            raw_user_message=user_msg_text
        )

    @classmethod
    def _extract_or_update_location(cls, state: ConversationState, user_msg: str) -> Dict[str, Any]:
        """Extracts location or reuses existing location from state entities."""
        loc_dict = state.emergency_location or {}

        pincode_match = re.search(r"\b\d{6}\b", user_msg)
        if pincode_match:
            loc_dict["pincode"] = pincode_match.group(0)

        if state.entities.city:
            loc_dict["city"] = state.entities.city
        if state.entities.location:
            loc_dict["location"] = state.entities.location
        if state.entities.pincode:
            loc_dict["pincode"] = state.entities.pincode
        if state.entities.landmark:
            loc_dict["landmark"] = state.entities.landmark

        is_emerg_phrase = any(w in user_msg.lower() for w in ["dikkat", "saans", "pain", " emergency", "bleeding", "accident", "behosh"])
        if not is_emerg_phrase and len(user_msg.strip()) > 0:
            loc_dict["address"] = user_msg.strip()
            loc_dict["location"] = loc_dict.get("location") or user_msg.strip()

        if not loc_dict.get("address"):
            parts = [loc_dict.get("location"), loc_dict.get("city"), loc_dict.get("pincode")]
            if any(parts):
                loc_dict["address"] = ", ".join([p for p in parts if p])

        return loc_dict

    @classmethod
    def _generate_phase6_emergency_response(
        cls,
        state: ConversationState,
        lang: Language,
        emerg_facilities: List[Dict[str, Any]]
    ) -> str:
        loc = state.emergency_location or {}
        loc_str = loc.get("address") or loc.get("location") or loc.get("city") or loc.get("pincode") or ""
        req_id = state.ambulance_request_id or "AMB-MOCK-00124"

        etype = state.emergency_type or "GENERAL_EMERGENCY"
        safety_advice = ""
        if etype == "BREATHING":
            safety_advice = {
                Language.HI: "Agar saans lene mein dikkat hai, kripya aaram se baithein aur deep breath lene ki koshish karein.",
                Language.MR: "जर श्वास घेण्यास त्रास होत असेल, तर कृपया शांत बसा आणि हळूहळू श्वास घ्या.",
                Language.EN: "If experiencing breathing difficulty, please remain seated and attempt slow, calm breaths."
            }.get(lang, "")
        elif etype == "CHEST_PAIN":
            safety_advice = {
                Language.HI: "Tez seene ka dard urgent medical care require karta hai. Physical exertion se bachein.",
                Language.MR: "छातीत तीव्र वेदना असल्यास त्वरित वैद्यकीय मदतीची गरज असते.",
                Language.EN: "Severe chest pain requires urgent medical attention. Avoid any physical exertion."
            }.get(lang, "")

        fac_info_str = ""
        if emerg_facilities:
            fac_name = emerg_facilities[0].get("name", "Nearest Hospital")
            fac_info_str = {
                Language.HI: f" Aapke paas emergency hospital hai: {fac_name}.",
                Language.MR: f" तुमच्या जवळ आपत्कालीन रुग्णालय आहे: {fac_name}.",
                Language.EN: f" Nearest emergency-capable facility: {fac_name}."
            }.get(lang, "")

        if state.emergency_status == "LOCATION_REQUIRED" or not loc_str:
            if lang == Language.HI:
                return f"Ji, ye emergency lag rahi hai! {safety_advice} Kripya abhi apni location (city, area ya pincode) batayein taaki 108 emergency assistance connect ki ja sake."
            elif lang == Language.MR:
                return f"ही आपत्कालीन परिस्थिती आहे! {safety_advice} 108 मदतीसाठी कृपया तुमची सध्याची जागा सांगा."
            else:
                return f"This appears to be an emergency! {safety_advice} Please share your current location so 108 emergency assistance can be initiated."
        else:
            if lang == Language.HI:
                return f"Ji, aapki location ({loc_str}) note kar li hai.{fac_info_str} Prototype mein simulated emergency assistance connect ho raha hai (Mock Request ID: {req_id}). Real emergency ke liye 108 par call karein."
            elif lang == Language.MR:
                return f"तुमचे ठिकाण ({loc_str}) नोंदवले आहे.{fac_info_str} सिम्युलेटेड आपत्कालीन मदत (मॉक आयडी: {req_id}) सुरू केली आहे. प्रत्यक्ष आपत्कालीन परिस्थितीसाठी 108 वर कॉल करा."
            else:
                return f"Location noted as {loc_str}.{fac_info_str} Simulated emergency assistance has been activated in this prototype (Mock Request ID: {req_id}). For real emergencies, please call 108 immediately."

    @classmethod
    def _execute_healthcare_tools(
        cls,
        db: Session,
        intent: NLUIntent,
        entities: NLUEntities,
        missing_fields: List[str],
        user_msg: str,
        user_id: Optional[int],
        phone_number: Optional[str]
    ) -> Dict[str, Any]:
        msg_lower = user_msg.lower()
        is_confirm = (
            intent in [NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.APPOINTMENT_CONFIRMATION] or
            any(w in msg_lower for w in ["haan", "yes", "confirm", "book it", "book kardo", "kardo", "कर दो"])
        )

        results = ActionRouter.route_nlu_to_action(
            db=db,
            intent=intent,
            entities=entities,
            user_id=user_id,
            phone_number=phone_number,
            missing_fields=missing_fields,
            is_confirmed=is_confirm
        )

        return results

    @classmethod
    def _merge_entities(cls, existing: NLUEntities, new_ent: NLUEntities) -> None:
        if new_ent.patient_name:
            existing.patient_name = new_ent.patient_name
        if new_ent.patient_relation:
            existing.patient_relation = new_ent.patient_relation
        if new_ent.location:
            existing.location = new_ent.location
        if new_ent.city:
            existing.city = new_ent.city
        if new_ent.state:
            existing.state = new_ent.state
        if new_ent.pincode:
            existing.pincode = new_ent.pincode
        if new_ent.landmark:
            existing.landmark = new_ent.landmark
        if new_ent.facility_name or new_ent.facility:
            f_val = new_ent.facility_name or new_ent.facility
            existing.facility_name = f_val
            existing.facility = f_val
        if new_ent.doctor_name or new_ent.doctor:
            d_val = new_ent.doctor_name or new_ent.doctor
            existing.doctor_name = d_val
            existing.doctor = d_val
        if new_ent.specialty or new_ent.speciality:
            s_val = new_ent.specialty or new_ent.speciality
            existing.specialty = s_val
            existing.speciality = s_val
        if new_ent.department:
            existing.department = new_ent.department
        if new_ent.service:
            existing.service = new_ent.service
        if new_ent.duration:
            existing.duration = new_ent.duration
        if new_ent.severity:
            existing.severity = new_ent.severity
        if new_ent.date:
            existing.date = new_ent.date
        if new_ent.time:
            existing.time = new_ent.time
        if new_ent.time_period:
            existing.time_period = new_ent.time_period
        if new_ent.appointment_id:
            existing.appointment_id = new_ent.appointment_id
        if new_ent.referral_id:
            existing.referral_id = new_ent.referral_id
        if new_ent.language:
            existing.language = new_ent.language
        if new_ent.appointment_requested:
            existing.appointment_requested = True
        if new_ent.ambulance_requested:
            existing.ambulance_requested = True

        for sym in new_ent.symptoms:
            if sym not in existing.symptoms:
                existing.symptoms.append(sym)

    @classmethod
    def _detect_missing_fields(cls, intent: Optional[NLUIntent], entities: NLUEntities) -> List[str]:
        missing = []
        if not intent:
            return missing

        spec = entities.specialty or entities.speciality
        doc_n = entities.doctor_name or entities.doctor
        fac_n = entities.facility_name or entities.facility
        loc = entities.location or entities.city or entities.pincode

        if intent in [
            NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_DOCTOR, NLUIntent.FIND_FACILITY,
            NLUIntent.FACILITY_SEARCH, NLUIntent.DOCTOR_SEARCH, NLUIntent.SYMPTOM_INFORMATION
        ]:
            if not loc:
                missing.append("location")
            if intent == NLUIntent.FIND_SPECIALIST and not spec:
                missing.append("specialty")

        if intent in [NLUIntent.CHECK_AVAILABILITY, NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.OPD_SCHEDULE, NLUIntent.SLOT_SEARCH]:
            if not (doc_n or fac_n or spec):
                missing.append("doctor_or_facility")

        if intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.APPOINTMENT_CONFIRMATION]:
            if not (doc_n or fac_n or spec):
                missing.append("doctor_or_facility")
            if not (entities.date or entities.time):
                missing.append("date")

        return missing

    @classmethod
    def _classify_response_type(
        cls,
        intent: NLUIntent,
        missing_fields: List[str],
        emergency: bool
    ) -> ResponseType:
        if emergency:
            return ResponseType.EMERGENCY

        if intent == NLUIntent.UNKNOWN:
            return ResponseType.UNKNOWN

        if missing_fields:
            return ResponseType.ASK_CLARIFICATION

        if intent in [
            NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH, NLUIntent.FIND_DOCTOR,
            NLUIntent.DOCTOR_SEARCH, NLUIntent.FIND_SPECIALIST, NLUIntent.SLOT_SEARCH
        ]:
            return ResponseType.SEARCH_REQUIRED

        if intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.APPOINTMENT_CONFIRMATION]:
            return ResponseType.BOOKING_REQUIRED

        if intent in [
            NLUIntent.MY_APPOINTMENTS, NLUIntent.OPD_SCHEDULE, NLUIntent.CHECK_AVAILABILITY,
            NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.REFERRAL_ID, NLUIntent.FACILITY_INFORMATION,
            NLUIntent.DOCTOR_INFORMATION, NLUIntent.PROVIDE_NAME
        ]:
            return ResponseType.ANSWER

        if intent in [
            NLUIntent.GENERAL_GREETING, NLUIntent.GENERAL_HELLO, NLUIntent.GENERAL_HELP,
            NLUIntent.LANGUAGE_CHANGE, NLUIntent.THANK_YOU, NLUIntent.GOODBYE, NLUIntent.PROVIDE_LOCATION
        ]:
            return ResponseType.ACKNOWLEDGE

        return ResponseType.ACKNOWLEDGE

    @classmethod
    def _generate_assistant_message(
        cls,
        intent: NLUIntent,
        response_type: ResponseType,
        entities: NLUEntities,
        missing_fields: List[str],
        language: Language,
        is_correction: bool,
        raw_user_msg: str,
        tool_results: Optional[Dict[str, Any]] = None
    ) -> str:
        tool_data = tool_results or {}
        p_name = entities.patient_name
        name_prefix = f" {p_name} ji" if p_name else ""
        spec_val = entities.specialty or entities.speciality or "doctor"

        # 0. Provide Name Response
        if intent == NLUIntent.PROVIDE_NAME and p_name:
            if language == Language.HI:
                return f"Namaste{name_prefix}! JanSethu AI mein aapka swagat hai. Main aapki kis healthcare samasya ya doctor khoj mein madad kar sakta hoon?"
            elif language == Language.MR:
                return f"नमस्कार{name_prefix}! जनसेतू AI मध्ये आपले स्वागत आहे. मी तुम्हाला कशात मदत करू शकतो?"
            else:
                return f"Hello {p_name}! Welcome to JanSethu AI. How can I assist you with your health query or doctor booking today?"

        # 1. Booking Execution Result
        booking = tool_data.get("booking")
        if booking:
            if booking.get("success"):
                ref_id = booking.get("confirmation_code") or booking.get("referral_id")
                doc = booking.get("doctor_name") or entities.doctor_name or entities.doctor or "Doctor"
                dt = booking.get("appointment_date") or entities.date or "tomorrow"
                tm = booking.get("start_time") or "11:00"
                if language == Language.HI:
                    return f"Ji{name_prefix}! Aapki appointment {doc} ke saath {dt} ko {tm} baje confirm ho gayi hai. Aapka Referral ID hai: {ref_id}."
                elif language == Language.MR:
                    return f"होय{name_prefix}! तुमची अपॉइंटमेंट {doc} यांच्यासोबत कन्फर्म झाली आहे. तुमचा रेफरल आयडी: {ref_id}."
                else:
                    return f"Your appointment with {doc} on {dt} at {tm} is confirmed. Your Referral ID is: {ref_id}."
            else:
                err = booking.get("error", "Slot unavailable")
                if language == Language.HI:
                    return f"Kshama karein, appointment book nahi ho saki: {err}."
                else:
                    return f"Sorry, the appointment could not be booked: {err}."

        # 2. Confirmation Prompt for Booking
        if intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.APPOINTMENT_CONFIRMATION] and tool_data.get("requires_confirmation"):
            doc = entities.doctor_name or entities.doctor or entities.facility_name or entities.facility or "Doctor"
            dt = entities.date or "kal"
            tm = entities.time or "11:00"
            if language == Language.HI:
                return f"Ji{name_prefix}, {doc} ka {dt} ko {tm} baje ka slot available hai. Kya main appointment confirm kar doon?"
            elif language == Language.MR:
                return f"होय{name_prefix}, {doc} यांचे {dt} रोजी {tm} चे स्लॉट उपलब्ध आहे. मी ते कन्फर्म करू का?"
            else:
                return f"Yes {p_name or ''}, slot for {doc} on {dt} at {tm} is available. Would you like me to confirm this booking?"

        # 3. Referral ID Lookup Result
        ref_details = tool_data.get("referral_details")
        if ref_details:
            ref_id = ref_details["confirmation_code"]
            doc = ref_details["doctor_name"]
            fac = ref_details["facility_name"]
            dt = ref_details["appointment_date"]
            st = ref_details["start_time"]
            if language == Language.HI:
                return f"Aapka Referral ID {ref_id} verified hai: {doc} ({fac}) ke saath {dt} ko {st} baje."
            else:
                return f"Your Referral ID {ref_id} is verified: Appointment with {doc} at {fac} on {dt} at {st}."
        elif intent == NLUIntent.REFERRAL_ID and "referral_details" in tool_data and not tool_data["referral_details"]:
            if language == Language.HI:
                return "Abhi mujhe aapki koi confirmed appointment ya referral ID nahi mil rahi."
            else:
                return "No matching confirmed appointment or referral ID was found in our system."

        # 4. My Appointments Result
        my_apts = tool_data.get("my_appointments")
        if my_apts is not None:
            if my_apts:
                active_apts = [
                    a for a in my_apts 
                    if str(a.get("status", "")).upper() in ["BOOKED", "CONFIRMED", "PENDING", "APPOINTMENTSTATUS.BOOKED", "APPOINTMENTSTATUS.CONFIRMED", "APPOINTMENTSTATUS.PENDING"]
                ]
                if active_apts:
                    apt = active_apts[0]
                    ref_code = apt["confirmation_code"]
                    doc_name = apt["doctor_name"]
                    fac_name = apt["facility_name"]
                    apt_dt = apt["appointment_date"]
                    if language == Language.HI:
                        return f"Aapki active appointment: {doc_name} ({fac_name}) ke saath {apt_dt} ko. Referral ID: {ref_code}."
                    elif language == Language.MR:
                        return f"आपली नोंदवलेली अपॉइंटमेंट: {doc_name} ({fac_name}) सोबत {apt_dt} रोजी. Referral ID: {ref_code}."
                    else:
                        return f"You have 1 active appointment with {doc_name} at {fac_name} on {apt_dt}. Referral ID: {ref_code}."
                else:
                    cancelled_apts = [
                        a for a in my_apts 
                        if str(a.get("status", "")).upper() in ["CANCELLED", "APPOINTMENTSTATUS.CANCELLED"]
                    ]
                    if cancelled_apts:
                        ref_code = cancelled_apts[0]["confirmation_code"]
                        if language == Language.HI:
                            return f"Aapki appointment (Referral ID: {ref_code}) cancel ho chuki hai. Abhi aapki koi active upcoming appointment nahi hai."
                        elif language == Language.MR:
                            return f"आपली अपॉइंटमेंट (Referral ID: {ref_code}) रद्द झाली आहे. सध्या कोणतीही सक्रिय अपॉइंटमेंट नाही."
                        else:
                            return f"Your appointment (Referral ID: {ref_code}) has been cancelled. You currently have no active upcoming appointments."
                    else:
                        if language == Language.HI:
                            return "Abhi mujhe aapki koi confirmed appointment nahi mil rahi."
                        elif language == Language.MR:
                            return "सध्या कोणतीही निश्चित अपॉइंटमेंट सापडली नाही."
                        else:
                            return "No confirmed appointments were found for your account."
            else:
                if language == Language.HI:
                    return "Abhi mujhe aapki koi confirmed appointment nahi mil rahi."
                elif language == Language.MR:
                    return "सध्या कोणतीही निश्चित अपॉइंटमेंट सापडली नाही."
                else:
                    return "No confirmed appointments were found for your account."

        # 5. Cancellation Result
        cancellation = tool_data.get("cancellation")
        if cancellation:
            if cancellation.get("success"):
                if language == Language.HI:
                    return "Aapki appointment safaltapoorvak cancel kar di gayi hai."
                else:
                    return "Your appointment has been successfully cancelled."
            else:
                err = cancellation.get("error", "")
                if language == Language.HI:
                    return f"Appointment cancel karne mein dikkat aayi: {err}."
                else:
                    return f"Could not cancel appointment: {err}."

        # 6. Facility & Specialist Search Result Verification
        facs = tool_data.get("facilities")
        if facs is not None:
            if facs:
                names = [f["name"] for f in facs[:3]]
                fac_str = ", ".join(names)
                loc = entities.city or entities.location or "apke ilake"
                if language == Language.HI:
                    return f"Ji{name_prefix}, mujhe {loc} mein {spec_val} ke liye {len(facs)} verified healthcare options mile hain: {fac_str}. Kya aap appointment book karna chahenge?"
                elif language == Language.MR:
                    return f"{loc} मध्ये {spec_val} साठी {len(facs)} पर्याय मिळाले आहेत: {fac_str}."
                else:
                    return f"Found {len(facs)} verified healthcare facilities for {spec_val} in {loc}: {fac_str}. Would you like to check available OPD slots?"
            else:
                loc = entities.city or entities.location or "is location"
                if language == Language.HI:
                    return f"Kshama karein, {loc} mein {spec_val} ke liye koi matching facility nahi mili. Kripya dusri location try karein."
                else:
                    return f"Sorry, no matching facilities were found for {spec_val} in {loc}. Please try another location or pincode."

        # 7. Doctor Search Result Verification
        docs = tool_data.get("doctors")
        if docs is not None:
            if docs:
                doc_names = [d["name"] for d in docs[:3]]
                doc_str = ", ".join(doc_names)
                fac = entities.facility_name or entities.facility or entities.city or "hospital"
                if language == Language.HI:
                    return f"{fac} mein available doctors: {doc_str}. Kya aap inki availability janna chahte hain?"
                else:
                    return f"Available doctors in {fac}: {doc_str}. Would you like to check their OPD availability?"

        # 8. Slot / Availability Result Verification
        if intent in [NLUIntent.CHECK_AVAILABILITY, NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.SLOT_SEARCH, NLUIntent.OPD_SCHEDULE]:
            doc = entities.doctor_name or entities.doctor or entities.facility_name or entities.facility or "Doctor"
            slots = tool_data.get("slots")
            if slots:
                slot_times = [s["start_time"] for s in slots[:3]]
                slot_str = ", ".join(slot_times)
                dt = entities.date or "kal"
                if language == Language.HI:
                    return f"Ji{name_prefix}, {doc} ke {dt} ke available slots hain: {slot_str}. Kya main 11:00 baje ka slot book kar doon?"
                else:
                    return f"Available slots for {doc} on {dt}: {slot_str}. Would you like me to book one for you?"
            else:
                if language == Language.HI:
                    return f"Kshama karein, {doc} ke koi available slots nahi hain ya doctor database mein nahi mile."
                else:
                    return f"Sorry, no available slots were found for {doc} in our database."

        # Correction response
        if is_correction:
            loc = entities.city or entities.location or "naya sthan"
            if language == Language.HI:
                return f"Samajh gaya, aapki location update karke {loc} kar di gayi hai. Main aapke liye nearest facilities khoj raha hoon."
            elif language == Language.MR:
                return f"समजले, तुमचे स्थान {loc} असे अपडेट केले आहे. मी तुमच्यासाठी जवळील रुग्णालये शोधत आहे."
            else:
                return f"Got it, your location has been updated to {loc}. Searching for available healthcare services for you."

        # Missing fields response
        if response_type == ResponseType.ASK_CLARIFICATION:
            if "location" in missing_fields:
                if language == Language.HI:
                    return f"Ji{name_prefix}, aap kis city ya ilake (jaise Baramati, Pune) mein {spec_val} ya doctor dhundhna chahte hain? Kripya apna location batayein."
                elif language == Language.MR:
                    return f"तुम्हाला कोणत्या शहरात किंवा भागात (उदा. बारामती, पुणे) डॉक्टर शोधायचे आहेत? कृपया तुमचे शहर सांगा."
                else:
                    return f"Which city or location (e.g. Baramati, Pune) are you looking for {spec_val} doctors in?"
            elif "specialty" in missing_fields:
                if language == Language.HI:
                    return "Aapko kis type ke doctor ki zarurat hai, ya aap apne symptoms bata sakte hain?"
                elif language == Language.MR:
                    return "तुम्हाला कोणत्या प्रकारच्या डॉक्टरची गरज आहे, किंवा तुमचे आजार सांगू शकता?"
                else:
                    return "What type of specialist or symptoms do you need assistance with?"
            elif "doctor_or_facility" in missing_fields:
                if language == Language.HI:
                    return "Aap kis doctor ya hospital ki availability janna chahte hain?"
                elif language == Language.MR:
                    return "तुम्हाला कोणत्या डॉक्टर किंवा रुग्णालयाची माहिती हवी आहे?"
                else:
                    return "Which doctor or hospital availability would you like to check?"
            elif "date" in missing_fields or "date_or_slot" in missing_fields:
                if language == Language.HI:
                    return "Aap kis din ya tareekh ke liye appointment book karna chahte hain?"
                elif language == Language.MR:
                    return "तुम्हाला कोणत्या तारखेसाठी अपॉइंटमेंट बुक करायची आहे?"
                else:
                    return "What date or time would you like to schedule your appointment for?"

        # Topic switch / General Greetings & Thanks
        if intent in [NLUIntent.GENERAL_GREETING, NLUIntent.GENERAL_HELLO]:
            if language == Language.HI:
                return f"Namaste{name_prefix}! JanSethu AI mein aapka swagat hai. Main aapki kya madad kar sakta hoon?"
            elif language == Language.MR:
                return f"नमस्कार{name_prefix}! जनसेतू AI मध्ये आपले स्वागत आहे. मी आपल्याला कशी मदत करू शकतो?"
            else:
                return f"Hello{name_prefix}! Welcome to JanSethu AI. How can I help you with your health query today?"

        if intent == NLUIntent.THANK_YOU:
            if language == Language.HI:
                return f"Aapka swagat hai{name_prefix}! JanSethu AI hamesha aapki swasthya seva ke liye tatpar hai."
            elif language == Language.MR:
                return f"धन्यवाद{name_prefix}! जनसेतू AI आपल्या आरोग्याच्या सेवेसाठी तत्पर आहे."
            else:
                return f"You're welcome{name_prefix}! JanSethu AI is always here to assist with your healthcare needs."

        if intent == NLUIntent.GOODBYE:
            if language == Language.HI:
                return "Dhanyawad! Apna khyal rakhein. Swasth rahein!"
            elif language == Language.MR:
                return "धन्यवाद! आपली काळजी घ्या."
            else:
                return "Thank you for using JanSethu AI. Take care and stay healthy!"

        if intent in [NLUIntent.MEDICAL_HELP, NLUIntent.GENERAL_HELP]:
            if language == Language.HI:
                return "JanSethu AI ke dwaara aap hospital khoj sakte hain, doctor ki availability dekh sakte hain aur appointment book kar sakte hain."
            else:
                return "JanSethu AI helps you find nearby hospitals, check doctor availability, and book OPD appointments."

        if intent in [NLUIntent.SYMPTOM_REPORT, NLUIntent.SYMPTOM_INFORMATION]:
            sym_str = ", ".join(entities.symptoms) if entities.symptoms else "symptoms"
            if language == Language.HI:
                return f"Aapke symptoms ({sym_str}) note kar liye hain. Ye symptoms medical attention require kar sakte hain. Kya main aapke liye nearest hospital ya specialist doctor dhundhun?"
            elif language == Language.MR:
                return f"तुमची लक्षणे ({sym_str}) नोंदवली आहेत. मी तुमच्यासाठी रुग्णालय किंवा डॉक्टर शोधू का?"
            else:
                return f"Noted your symptoms ({sym_str}). These symptoms may require medical attention. Shall I help you find a suitable doctor or hospital?"

        if intent == NLUIntent.UNKNOWN:
            if language == Language.HI:
                return "Kripya apne swasthya samasya, doctor ya hospital ke bare mein vistaar se batayein taaki main aapki madad kar sakoon."
            else:
                return "I'm not sure I understood. Please describe your symptom or the medical service you are looking for."

        if language == Language.HI:
            return "Aapki jaankari process ki ja rahi hai. Kripya aage batayein."
        else:
            return "Processing your request. Please go ahead."
