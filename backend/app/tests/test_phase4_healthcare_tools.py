import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.enums import Language, FacilityType, AppointmentStatus
from app.schemas.conversation import ConversationRequest, ResponseType
from app.schemas.nlu import NLUIntent
from app.services.conversation_manager import ConversationManager
from app.services.healthcare_tools import HealthcareToolService
from app.repositories.facility_repository import FacilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.facility import FacilityCreate
from app.schemas.doctor import DoctorCreate, DoctorAvailabilityCreate

client = TestClient(app)

class TestPhase4HealthcareTools:
    @classmethod
    def setup_class(cls):
        """Seed verified healthcare data in DB for testing."""
        cls.db: Session = SessionLocal()
        ConversationManager.clear_all_sessions()

        # Seed Facility if needed
        facs = FacilityRepository.search(cls.db, q="Hospital A")
        if facs:
            cls.facility = facs[0]
        else:
            cls.facility = FacilityRepository.create_facility(
                cls.db,
                FacilityCreate(
                    name="Hospital A",
                    facility_type=FacilityType.GOVERNMENT_HOSPITAL,
                    address="Prem Nagar Main Road",
                    phone_number="9876543210",
                    district="Jaipur",
                    state="Rajasthan",
                    pincode="302019",
                    village="Prem Nagar",
                    latitude=26.9124,
                    longitude=75.7873,
                    emergency_capable=True
                )
            )

        # Seed Doctor if needed
        docs = DoctorRepository.search_doctors(cls.db, facility_id=cls.facility.id)
        if docs:
            cls.doctor = docs[0]
        else:
            # Get or create department
            dept_id = cls.facility.departments[0].id if cls.facility.departments else 1
            cls.doctor = DoctorRepository.create_doctor(
                cls.db,
                DoctorCreate(
                    name="Dr Lakshya",
                    qualification="MBBS, MS (Orthopedics)",
                    specialization="Orthopedics",
                    facility_id=cls.facility.id,
                    department_id=dept_id
                )
            )
            # Add availability for all days (0..6)
            for day in range(7):
                DoctorRepository.add_availability(
                    cls.db,
                    cls.doctor.id,
                    DoctorAvailabilityCreate(
                        day_of_week=day,
                        start_time="09:00",
                        end_time="17:00",
                        slot_duration_minutes=30
                    )
                )

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def setup_method(self):
        ConversationManager.clear_all_sessions()
        # Clean up test appointments to ensure available slots
        from app.models.appointment import Appointment
        self.db.query(Appointment).filter(
            Appointment.appointment_date >= date.today()
        ).delete()
        self.db.commit()

    @pytest.mark.anyio
    async def test_01_facility_search_real_db(self):
        """TEST 1 — Facility search querying real DB records."""
        req = ConversationRequest(
            session_id="test-p4-fac",
            message="Jaipur mein orthopedic hospital chahiye",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req, db=self.db)
        assert res.intent in [NLUIntent.FACILITY_SEARCH, NLUIntent.DOCTOR_SEARCH, NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_FACILITY]
        assert res.entities.city == "Jaipur"
        assert len(res.assistant_message) > 0
        assert "Jaipur" in res.assistant_message or "hospital" in res.assistant_message.lower()

    @pytest.mark.anyio
    async def test_02_doctor_search_real_db(self):
        """TEST 2 — Doctor search for specific facility."""
        req = ConversationRequest(
            session_id="test-p4-doc",
            message="Hospital A mein orthopedic doctors kaun hain?",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req, db=self.db)
        assert res.entities.facility == "Hospital A"
        assert res.intent in [NLUIntent.DOCTOR_SEARCH, NLUIntent.FACILITY_SEARCH, NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_DOCTOR]
        assert len(res.assistant_message) > 0

    @pytest.mark.anyio
    async def test_03_doctor_availability_real_db(self):
        """TEST 3 — Availability check for specific doctor."""
        req = ConversationRequest(
            session_id="test-p4-avail",
            message="Hospital A mein Dr Lakshya available hain?",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req, db=self.db)
        assert res.entities.doctor == "Dr Lakshya"
        assert res.entities.facility == "Hospital A"
        assert len(res.assistant_message) > 0

    @pytest.mark.anyio
    async def test_04_slot_search_with_context(self):
        """TEST 4 — Slot search using prior context."""
        session_id = "test-p4-slot"
        req1 = ConversationRequest(
            session_id=session_id,
            message="Hospital A mein Dr Lakshya available hain?",
            language_hint="HI"
        )
        await ConversationManager.process_message(req1, db=self.db)

        req2 = ConversationRequest(
            session_id=session_id,
            message="Kal morning ka slot hai?",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2, db=self.db)
        assert res2.entities.doctor == "Dr Lakshya"
        assert res2.entities.facility == "Hospital A"
        assert res2.entities.date in ["tomorrow", "kal"] or res2.entities.date is not None
        assert len(res2.assistant_message) > 0

    @pytest.mark.anyio
    async def test_05_booking_confirmation_flow(self):
        """
        TEST 5 — Appointment Booking Flow:
        1. User asks to book slot -> System asks for confirmation first.
        2. User confirms ("Haan") -> System creates real DB booking & returns real Referral ID.
        """
        session_id = "test-p4-booking"

        # Turn 1: User asks to book
        req1 = ConversationRequest(
            session_id=session_id,
            message="Dr Lakshya ko kal 11 baje book kar do",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1, db=self.db)
        assert res1.intent in [NLUIntent.BOOK_APPOINTMENT, NLUIntent.CONFIRM_APPOINTMENT]
        assert "confirm" in res1.assistant_message.lower() or "confirm" in res1.assistant_message

        # Turn 2: User confirms
        req2 = ConversationRequest(
            session_id=session_id,
            message="Haan",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2, db=self.db)
        assert res2.entities.referral_id is not None
        assert res2.entities.referral_id.startswith("JS-") or res2.entities.referral_id.startswith("JAN-REF-")
        assert res2.entities.referral_id in res2.assistant_message

    @pytest.mark.anyio
    async def test_06_referral_lookup(self):
        """TEST 6 — Referral ID Lookup."""
        # First book an appointment to get a valid referral ID
        booking_res = HealthcareToolService.create_appointment(
            db=self.db,
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            appointment_date="tomorrow",
            start_time="11:30"
        )
        assert booking_res.get("success") is True
        ref_id = booking_res["confirmation_code"]

        req = ConversationRequest(
            session_id="test-p4-ref",
            message=f"mera referral ID {ref_id} kya hai?",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req, db=self.db)
        assert ref_id in res.assistant_message or ref_id == res.entities.referral_id

    @pytest.mark.anyio
    async def test_07_my_appointments_lookup(self):
        """TEST 7 — My Appointments query."""
        req = ConversationRequest(
            session_id="test-p4-myapts",
            message="meri appointment kab hai?",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req, db=self.db)
        assert res.intent == NLUIntent.MY_APPOINTMENTS
        assert len(res.assistant_message) > 0

    @pytest.mark.anyio
    async def test_08_no_hallucination_nonexistent_doctor(self):
        """TEST 8 — Searching for nonexistent doctor must NOT hallucinate availability."""
        req = ConversationRequest(
            session_id="test-p4-nohallucinate",
            message="Jaipur mein Dr UnknownNonExistentPerson available hain?",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req, db=self.db)
        assert "nahi" in res.assistant_message.lower() or "sorry" in res.assistant_message.lower() or "no" in res.assistant_message.lower() or "kshama" in res.assistant_message.lower() or "not found" in res.assistant_message.lower()

    @pytest.mark.anyio
    async def test_09_multi_turn_context_preservation(self):
        """TEST 9 — Context preservation across follow-up turns."""
        session_id = "test-p4-context-seq"

        req1 = ConversationRequest(
            session_id=session_id,
            message="Hospital A mein Dr Lakshya available hain?",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1, db=self.db)
        assert res1.entities.doctor == "Dr Lakshya"
        assert res1.entities.facility == "Hospital A"

        req2 = ConversationRequest(
            session_id=session_id,
            message="Kal morning?",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2, db=self.db)
        assert res2.entities.doctor == "Dr Lakshya"
        assert res2.entities.facility == "Hospital A"
        assert res2.entities.date in ["tomorrow", "kal"] or res2.entities.date is not None

    def test_10_action_router_registration(self):
        """TEST 10 — ActionRouter has registered all 17 controlled actions."""
        from app.services.action_router import ActionRouter
        registered = ActionRouter.get_registered_actions()
        expected_actions = [
            "find_facilities", "find_nearby_facilities", "find_facilities_by_specialty",
            "get_facility_details", "find_doctors", "get_doctor_details",
            "get_doctor_availability", "find_available_slots", "find_emergency_facilities",
            "find_available_ambulances", "create_appointment", "cancel_appointment",
            "reschedule_appointment", "get_patient_appointments", "create_emergency_request",
            "create_confirmation_ticket", "send_confirmation"
        ]
        for act in expected_actions:
            assert act in registered

    def test_11_ambulance_search_database(self):
        """TEST 11 — Ambulance search returning AVAILABLE ambulances."""
        from app.services.action_router import ActionRouter
        res = ActionRouter.dispatch("find_available_ambulances", db=self.db, params={"location": "Baramati"})
        assert res["success"] is True
        data = res["data"]
        assert isinstance(data, list)
        for amb in data:
            assert amb["status"] == "AVAILABLE"

    @pytest.mark.anyio
    async def test_12_test_conversation_a(self):
        """
        TEST CONVERSATION A — Standard end-to-end appointment journey:
        Greeting -> Skin Doctor -> Location -> Tomorrow -> 4 PM -> Book -> Confirmation.
        """
        sid = "test-conv-a"
        # Turn 1: Hi
        r1 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Hi, my name is Ramesh"), db=self.db)
        assert r1.assistant_message is not None

        # Turn 2: Skin doctor
        r2 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="I need a skin doctor"), db=self.db)
        assert r2.entities.specialty in ["Dermatology", "skin"] or r2.entities.speciality in ["Dermatology", "skin"]

        # Turn 3: Baramati
        r3 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Baramati"), db=self.db)
        assert r3.entities.location == "Baramati" or r3.entities.city == "Baramati"

        # Turn 4: Tomorrow
        r4 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Tomorrow"), db=self.db)
        assert r4.entities.date in ["tomorrow", "kal"] or r4.entities.date is not None

        # Turn 5: 4 PM
        r5 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="4 PM"), db=self.db)
        assert r5.assistant_message is not None

        # Turn 6: Book it
        r6 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Book it"), db=self.db)
        assert r6.entities.referral_id is not None or "confirm" in r6.assistant_message.lower()

    @pytest.mark.anyio
    async def test_13_test_conversation_b_emergency(self):
        """
        TEST CONVERSATION B — Emergency workflow in Marathi:
        Emergency signal -> Emergency Safety -> Location -> Facilities + Ambulance -> Dispatch.
        """
        sid = "test-conv-b"
        # Turn 1: Emergency breathing phrase in Marathi
        r1 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="माझ्या वडिलांना श्वास घेण्यास खूप त्रास होत आहे", language_hint="MR"), db=self.db)
        assert r1.emergency is True
        assert r1.emergency_status in ["LOCATION_REQUIRED", "ASSISTANCE_SIMULATED"]

        # Turn 2: Provide location
        r2 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="बारामतीजवळ आहेत", language_hint="MR"), db=self.db)
        assert r2.emergency is True
        assert r2.emergency_location is not None
        assert "108" in r2.assistant_message or "AMB-MOCK-" in r2.assistant_message or "रुग्णवाहिका" in r2.assistant_message

        # Turn 3: Confirm ambulance request
        r3 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="हो, ambulance हवी आहे", language_hint="MR"), db=self.db)
        assert r3.emergency is True
        assert r3.ambulance_request_id is not None

    @pytest.mark.anyio
    async def test_14_test_conversation_c_facility(self):
        """TEST CONVERSATION C — Hospital search by location."""
        sid = "test-conv-c"
        r1 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Mujhe hospital chahiye"), db=self.db)
        r2 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Baramati mein"), db=self.db)
        assert r2.intent in [NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH, NLUIntent.PROVIDE_LOCATION]
        assert "Baramati" in r2.assistant_message or "hospital" in r2.assistant_message.lower()

    @pytest.mark.anyio
    async def test_15_test_conversation_d_cancellation(self):
        """TEST CONVERSATION D — Appointment Cancellation."""
        sid = "test-conv-d"
        # Book an appointment first
        booking = HealthcareToolService.create_appointment(
            db=self.db,
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            appointment_date="tomorrow",
            start_time="14:00"
        )
        assert booking["success"] is True

        r1 = await ConversationManager.process_message(ConversationRequest(session_id=sid, message="Meri appointment cancel karni hai"), db=self.db)
        assert r1.intent == NLUIntent.CANCEL_APPOINTMENT
        assert "cancel" in r1.assistant_message.lower() or "रद्द" in r1.assistant_message or "radd" in r1.assistant_message.lower() or "success" in r1.assistant_message.lower()

