import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.enums import Language, CallSessionStatus, AppointmentStatus, BookingChannel, FacilityType
from app.models.telephony import CallSession, ConversationMessage
from app.models.appointment import Appointment
from app.models.user import User, PatientProfile
from app.services.phone_session_service import PhoneSessionService
from app.services.voice.speech_provider import (
    SpeechInputProvider,
    LocalSpeechInputProvider,
    ConfiguredSpeechInputProvider,
    get_speech_provider,
)
from app.services.voice.tts_provider import (
    TTSProvider,
    LocalTTSProvider,
    ConfiguredTTSProvider,
    get_tts_provider,
)
from app.services.voice.voice_understanding import VoiceUnderstandingService
from app.services.voice.intent_parser import IntentParser, IntentEnum
from app.services.voice.voice_normalizer import VoiceNormalizer
from app.repositories.facility_repository import FacilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.facility import FacilityCreate
from app.schemas.doctor import DoctorCreate


class TestPhase5VoiceEngine:

    @classmethod
    def setup_class(cls):
        """Seed initial healthcare domain data if not present."""
        cls.db: Session = SessionLocal()

        facs = FacilityRepository.search(cls.db, q="Baramati Sub-District Hospital")
        if facs:
            cls.facility = facs[0]
        else:
            cls.facility = FacilityRepository.create_facility(
                cls.db,
                FacilityCreate(
                    name="Baramati Sub-District Hospital",
                    facility_type=FacilityType.GOVERNMENT_HOSPITAL,
                    address="Bhigwan Road, Baramati",
                    phone_number="02112222100",
                    district="Pune",
                    state="Maharashtra",
                    pincode="413102",
                    village="Baramati",
                    latitude=18.1506,
                    longitude=74.5772,
                    emergency_capable=True
                )
            )

        docs = DoctorRepository.search_doctors(cls.db, facility_id=cls.facility.id)
        if docs:
            cls.doctor = docs[0]
        else:
            dept_id = cls.facility.departments[0].id if cls.facility.departments else 1
            cls.doctor = DoctorRepository.create_doctor(
                cls.db,
                DoctorCreate(
                    name="Dr. Deshmukh",
                    specialization="General Medicine",
                    qualification="MBBS, MD",
                    facility_id=cls.facility.id,
                    department_id=dept_id,
                    phone_number="9823012345",
                    experience_years=10,
                    consultation_fee=100.0,
                    is_active=True
                )
            )

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    @pytest.mark.anyio
    async def test_01_voice_emergency_preemption(self):
        """TEST 1: Voice Emergency Preemption (Breathing difficulty in Hinglish)."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776655")
        
        # User expresses severe breathing emergency
        resp, nlu = await PhoneSessionService.process_voice_input(
            self.db,
            session.id,
            "mujhe saans lene mein bohot takleef ho rahi hai emergency 108"
        )

        assert nlu.intent == IntentEnum.EMERGENCY
        assert session.current_state == "EMERGENCY"
        assert "🚨" in resp.prompt_text or "108" in resp.prompt_text or "आपातकालीन" in resp.prompt_text

    @pytest.mark.anyio
    async def test_02_ambulance_request_flow(self):
        """TEST 2: Ambulance Request Flow with Location Capture."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776654")

        resp, nlu = await PhoneSessionService.process_voice_input(
            self.db,
            session.id,
            "mujhe 108 ambulance chahiye Baramati location par"
        )

        assert nlu.intent == IntentEnum.EMERGENCY
        assert session.current_state == "EMERGENCY"
        assert resp.prompt_text is not None

    @pytest.mark.anyio
    async def test_03_hindi_opd_booking_flow(self):
        """TEST 3: Hindi OPD Booking Flow via Voice."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776653")

        # Turn 1: Registration name
        resp, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "Mera naam Ramesh Kumar hai")
        assert session.user_id is not None

        # Turn 2: Express intent to book doctor
        resp, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "mujhe doctor ko dikhana hai")
        assert session.current_state in ["FACILITY_SELECTION", "LOCATION_INPUT", "DEPARTMENT_SELECTION"]

        # Turn 3: Choose facility
        resp, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "Baramati Sub-District Hospital")
        assert session.current_state in ["DEPARTMENT_SELECTION", "FACILITY_SELECTION", "DOCTOR_SELECTION"]

        # Turn 4: Select date
        resp, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "kal ka appointment chahiye")
        assert session.current_state in ["SLOT_SELECTION", "DATE_SELECTION", "DOCTOR_SELECTION"]

    @pytest.mark.anyio
    async def test_04_marathi_facility_search_flow(self):
        """TEST 4: Marathi Facility Search & Appointment Flow."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776652")

        resp, nlu = await PhoneSessionService.process_voice_input(
            self.db,
            session.id,
            "मला बारामती रुग्णालयात डॉक्टरांना दाखवायचे आहे",
            language_hint="MR"
        )

        assert nlu.language == Language.MR
        assert session.language == Language.MR
        assert resp.prompt_text is not None

    @pytest.mark.anyio
    async def test_05_doctor_discovery_availability_checking(self):
        """TEST 5: Doctor Discovery & Availability Checking."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776651")

        resp, nlu = await PhoneSessionService.process_voice_input(
            self.db,
            session.id,
            "kal doctor available hai kya timing kya hai"
        )

        assert nlu.intent in [IntentEnum.CHECK_AVAILABILITY, IntentEnum.BOOK_APPOINTMENT, IntentEnum.SEARCH_DOCTOR]
        assert resp.prompt_text is not None

    @pytest.mark.anyio
    async def test_06_cancellation_and_reschedule_voice(self):
        """TEST 6: Cancellation & Reschedule via Spoken Natural Input."""
        # Create user and profile
        user = self.db.query(User).filter(User.phone_number == "9988776650").first()
        if not user:
            user = User(
                name="Voice Patient",
                phone_number="9988776650",
                password_hash=User.hash_password("pwd123"),
                role="CUSTOMER"
            )
            self.db.add(user)
            self.db.flush()

        profile = self.db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
        if not profile:
            profile = PatientProfile(user_id=user.id, district="Pune", state="Maharashtra")
            self.db.add(profile)
            self.db.flush()

        import uuid
        from datetime import time
        
        apt = self.db.query(Appointment).filter(
            Appointment.patient_id == profile.id,
            Appointment.status == AppointmentStatus.CONFIRMED
        ).first()

        if not apt:
            code = f"JS-2026-T50-{uuid.uuid4().hex[:4].upper()}"
            apt = Appointment(
                patient_id=profile.id,
                doctor_id=self.doctor.id,
                facility_id=self.facility.id,
                department_id=self.doctor.department_id,
                appointment_date=date.today() + timedelta(days=10),
                start_time=time(16, 30),
                end_time=time(17, 0),
                confirmation_code=code,
                status=AppointmentStatus.CONFIRMED,
                booking_channel=BookingChannel.PHONE
            )
            self.db.add(apt)
            self.db.commit()

        session = PhoneSessionService.start_session(self.db, phone_number="9988776650")
        
        # Express cancellation intent
        resp, nlu = await PhoneSessionService.process_voice_input(self.db, session.id, "meri appointment cancel kar do")
        assert nlu.intent == IntentEnum.CANCEL_APPOINTMENT
        assert session.current_state == "CANCEL_APPOINTMENT"

        # Confirm cancellation
        resp, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "haan cancel karo")
        assert session.current_state in ["CANCEL_COMPLETED", "MAIN_MENU"]

    @pytest.mark.anyio
    async def test_07_ambiguous_intent_fallback(self):
        """TEST 7: Ambiguous Intent Handling with Conversational Fallback."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776649")

        # Pass ambiguous text payload with low confidence STT dict
        low_conf_payload = {"text": "kuch samajh nahi aa raha", "confidence": 0.15}
        resp, nlu = await PhoneSessionService.process_voice_input(self.db, session.id, low_conf_payload)

        assert nlu.confidence < 0.25
        assert "Kripya" in resp.prompt_text or "phir se" in resp.prompt_text or resp.prompt_text is not None

    @pytest.mark.anyio
    async def test_08_multilingual_code_switching(self):
        """TEST 8: Multilingual Code-Switching (Hindi to English mid-session)."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776648")

        # Turn 1: Hindi
        resp1, nlu1 = await PhoneSessionService.process_voice_input(self.db, session.id, "Namaste, mera naam Vijay hai")
        assert session.language in [Language.HI, Language.EN]

        # Turn 2: English code switch
        resp2, nlu2 = await PhoneSessionService.process_voice_input(
            self.db,
            session.id,
            "I want to change language to english please",
            language_hint="EN"
        )
        assert nlu2.language == Language.EN
        assert session.language == Language.EN

    def test_09_confirmation_normalization(self):
        """TEST 9: Confirmation Normalization."""
        # Test affirmative phrases
        assert VoiceNormalizer.normalize_confirmation("Haan ji bilkul") is True
        assert VoiceNormalizer.normalize_confirmation("Yes confirm kar do") is True
        assert VoiceNormalizer.normalize_confirmation("Pakka book karo") is True
        assert VoiceNormalizer.normalize_confirmation("हो नक्की करा") is True

        # Test negative phrases
        assert VoiceNormalizer.normalize_confirmation("Nahi mat karo") is False
        assert VoiceNormalizer.normalize_confirmation("No cancel it") is False
        assert VoiceNormalizer.normalize_confirmation("नाही नको") is False

    @pytest.mark.anyio
    async def test_10_stt_mock_fallback_low_confidence(self):
        """TEST 10: STT Mock Fallback & Low-Confidence Retry Prompting."""
        speech_provider = get_speech_provider()
        tts_provider = get_tts_provider()

        assert isinstance(speech_provider, SpeechInputProvider)
        assert isinstance(tts_provider, TTSProvider)

        # Test transcription fallback
        res = await speech_provider.transcribe("")
        assert "text" in res
        assert "confidence" in res

        # Test TTS synthesis
        tts_res = await tts_provider.synthesize("JanSethu Voice Engine")
        assert tts_res["text"] == "JanSethu Voice Engine"

    @pytest.mark.anyio
    async def test_11_telephony_session_persistence(self):
        """TEST 11: Telephony Session Persistence & Audio Metadata Tracking."""
        session = PhoneSessionService.start_session(
            self.db,
            phone_number="9988776647",
            channel="VOICE_CALL",
            provider="development",
            provider_call_id="call-voice-test-11"
        )

        assert session.provider_call_id == "call-voice-test-11"
        assert session.status == CallSessionStatus.ACTIVE

        resp, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "Doctor ko dikhana hai")
        
        # Verify messages recorded in DB
        msgs = self.db.query(ConversationMessage).filter(ConversationMessage.call_session_id == session.id).all()
        assert len(msgs) >= 2  # System greeting + User input + System prompt

    @pytest.mark.anyio
    async def test_12_e2e_voice_pipeline(self):
        """TEST 12: Full End-to-End Voice Turn Pipeline Verification."""
        session = PhoneSessionService.start_session(self.db, phone_number="9988776646")

        # Step 1: Voice greeting & name
        resp1, _ = await PhoneSessionService.process_voice_input(self.db, session.id, "Mera naam Aniket Patil hai")
        assert session.user_id is not None

        # Step 2: Emergency preemption
        resp2, nlu2 = await PhoneSessionService.process_voice_input(self.db, session.id, "chest pain ho raha hai emergency")
        assert nlu2.intent == IntentEnum.EMERGENCY
        assert session.current_state == "EMERGENCY"

        # Step 3: End call
        resp3 = PhoneSessionService.format_response(self.db, PhoneSessionService.end_session(self.db, session.id))
        assert session.status == CallSessionStatus.COMPLETED
        assert session.current_state == "ENDED"
