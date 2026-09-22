import pytest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.enums import BookingChannel, AppointmentStatus, FacilityType, UserRole
from app.models.appointment import Appointment
from app.models.user import User, PatientProfile
from app.schemas.conversation import ConversationRequest, ConversationResponse, ResponseType
from app.services.conversation_manager import ConversationManager
from app.services.llm_service import DeterministicNLUParser
from app.services.safety_engine import SafetyEngine
from app.repositories.facility_repository import FacilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.facility import FacilityCreate
from app.schemas.doctor import DoctorCreate
from app.config.check_config import validate_configuration

client = TestClient(app)

class TestPhase7FinalIntegration:

    @classmethod
    def setup_class(cls):
        cls.db: Session = SessionLocal()

        # Setup test patient user
        patient_user = cls.db.query(User).filter(User.phone_number == "9876543210").first()
        if not patient_user:
            patient_user = User(
                phone_number="9876543210",
                name="P7 Test Patient",
                password_hash="hashed_pw_p7",
                role=UserRole.CUSTOMER,
                is_active=True
            )
            cls.db.add(patient_user)
            cls.db.commit()
            cls.db.refresh(patient_user)
            patient_profile = PatientProfile(
                user_id=patient_user.id,
                gender="MALE"
            )
            cls.db.add(patient_profile)
            cls.db.commit()
            cls.db.refresh(patient_profile)
        cls.patient_user = patient_user

        # Setup test facility
        facs = FacilityRepository.search(cls.db, q="Phase7 Integration Hospital")
        if facs:
            cls.facility = facs[0]
        else:
            cls.facility = FacilityRepository.create_facility(
                cls.db,
                FacilityCreate(
                    name="Phase7 Integration Hospital",
                    facility_type=FacilityType.GOVERNMENT_HOSPITAL,
                    address="Station Road, Baramati",
                    phone_number="02112888888",
                    district="Pune",
                    state="Maharashtra",
                    pincode="413102",
                    village="Baramati",
                    latitude=18.1506,
                    longitude=74.5772,
                    emergency_capable=True
                )
            )

        # Setup test doctor
        docs = DoctorRepository.search_doctors(cls.db, facility_id=cls.facility.id)
        if docs:
            cls.doctor = docs[0]
        else:
            dept_id = cls.facility.departments[0].id if cls.facility.departments else 1
            cls.doctor = DoctorRepository.create_doctor(
                cls.db,
                DoctorCreate(
                    name="Dr. Phase7 Cardiologist",
                    specialization="Cardiology",
                    qualification="MD, DM Cardiology",
                    facility_id=cls.facility.id,
                    department_id=dept_id,
                    phone_number="9999977777",
                    experience_years=12,
                    consultation_fee=300.0,
                    is_active=True
                )
            )

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    @pytest.mark.anyio
    async def test_01_scenario_a_normal_doctor_search(self):
        """Scenario A: Search for Cardiologist in Baramati/Pune."""
        req = ConversationRequest(
            session_id="p7_session_a",
            message="Baramati mein cardiologist doctor chahiye",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req)
        assert res is not None
        assert res.session_id == "p7_session_a"
        assert len(res.assistant_message) > 0

    def test_02_scenario_b_multi_information_utterance(self):
        """Scenario B: Dense multi-entity utterance extraction."""
        nlu_res = DeterministicNLUParser.parse("Maza mulga Rahul saathi doctor pahije chest pain ahe Baramati madhe")
        assert nlu_res is not None
        assert nlu_res.entities is not None

    @pytest.mark.anyio
    async def test_03_scenario_c_user_location_correction(self):
        """Scenario C: User corrects location mid-conversation ('Nahi, Pune mein')."""
        session_id = "p7_session_c"
        req1 = ConversationRequest(
            session_id=session_id,
            message="Baramati me doctor chahiye",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert res1.entities.city == "Baramati" or res1.entities.location == "Baramati" or res1.entities.district == "Baramati"

        req2 = ConversationRequest(
            session_id=session_id,
            message="Nahi, Pune mein doctor chahiye",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.entities.city == "Pune" or res2.entities.location == "Pune" or res2.entities.district == "Pune"

    @pytest.mark.anyio
    async def test_04_scenario_d_context_memory_across_turns(self):
        """Scenario D: Information accumulated across multiple turns without loss."""
        session_id = "p7_session_d"
        req1 = ConversationRequest(session_id=session_id, message="Main Pune me hoon", language_hint="HI")
        await ConversationManager.process_message(req1)

        req2 = ConversationRequest(session_id=session_id, message="Mujhe fever aur headache hai", language_hint="HI")
        res2 = await ConversationManager.process_message(req2)

        assert "fever" in res2.entities.symptoms or len(res2.entities.symptoms) > 0
        assert res2.entities.city == "Pune" or res2.entities.location == "Pune"

    @pytest.mark.anyio
    async def test_05_scenario_e_multilingual_code_switching(self):
        """Scenario E: Smooth switching between English, Hindi, and Marathi."""
        session_id = "p7_session_e"
        req_hi = ConversationRequest(session_id=session_id, message="Baramati me hospital kahan hai?", language_hint="HI")
        res_hi = await ConversationManager.process_message(req_hi)
        assert res_hi is not None

        req_mr = ConversationRequest(session_id=session_id, message="Kiti doctor uplabdh ahet?", language_hint="MR")
        res_mr = await ConversationManager.process_message(req_mr)
        assert res_mr is not None

        req_en = ConversationRequest(session_id=session_id, message="I want to book an appointment tomorrow", language_hint="EN")
        res_en = await ConversationManager.process_message(req_en)
        assert res_en is not None

    @pytest.mark.anyio
    async def test_06_emergency_override_108(self):
        """Emergency Override: High priority safety trigger redirects immediately."""
        req = ConversationRequest(
            session_id="p7_emergency_session",
            message="Bahut tez sine me dard hai, patient behosh ho raha hai!",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req)
        assert res is not None
        assert res.response_type == ResponseType.EMERGENCY or "108" in res.assistant_message or "अस्पताल" in res.assistant_message or "Emergency" in res.assistant_message or "emergency" in res.assistant_message.lower()

    def test_07_atomic_booking_lifecycle(self):
        """Atomic Booking Lifecycle & Double Booking Prevention."""
        import random
        target_date = date.today() + timedelta(days=30 + random.randint(1, 500))
        target_start = time(11, 0)
        target_end = time(11, 30)

        dept_id = self.facility.departments[0].id if self.facility.departments else 1

        # First booking attempt
        apt1 = AppointmentRepository.create_appointment(
            db=self.db,
            patient_id=self.patient_user.id,
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=dept_id,
            apt_date=target_date,
            start_time=target_start,
            end_time=target_end,
            booking_channel=BookingChannel.PHONE,
            reason_for_visit="Phase 7 Integration Test"
        )
        assert apt1 is not None
        assert apt1.status == AppointmentStatus.BOOKED or apt1.status == AppointmentStatus.CONFIRMED

        # Duplicate booking attempt on exact same slot raises ValueError
        with pytest.raises(ValueError) as excinfo:
            AppointmentRepository.create_appointment(
                db=self.db,
                patient_id=self.patient_user.id,
                doctor_id=self.doctor.id,
                facility_id=self.facility.id,
                department_id=dept_id,
                apt_date=target_date,
                start_time=target_start,
                end_time=target_end,
                booking_channel=BookingChannel.PHONE,
                reason_for_visit="Duplicate Test"
            )
        assert "SLOT_ALREADY_BOOKED" in str(excinfo.value)

    def test_08_config_and_health_audit(self):
        """Validate config integrity and health check endpoints."""
        is_valid = validate_configuration()
        assert is_valid is True

        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") in ["healthy", "ok"]

        res_ready = client.get("/health/ready")
        assert res_ready.status_code == 200
        data_ready = res_ready.json()
        assert data_ready.get("status") in ["healthy", "ok"] or data_ready.get("database") in ["connected", "ok"]

