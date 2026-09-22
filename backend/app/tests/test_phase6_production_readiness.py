import pytest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.core.config import settings
from app.models.enums import Language, BookingChannel, AppointmentStatus, FacilityType
from app.models.appointment import Appointment
from app.models.user import User, PatientProfile
from app.integrations.telephony.factory import get_telephony_provider
from app.integrations.telephony.twilio_provider import TwilioTelephonyProvider
from app.integrations.telephony.vonage_provider import VonageTelephonyProvider
from app.integrations.telephony.development_provider import DevelopmentTelephonyProvider
from app.integrations.sms.factory import get_sms_provider
from app.integrations.sms.twilio_sms_provider import TwilioSMSProvider
from app.integrations.sms.development_provider import DevelopmentSMSProvider
from app.services.voice.speech_provider import get_speech_provider, LocalSpeechInputProvider, ConfiguredSpeechInputProvider
from app.services.voice.tts_provider import get_tts_provider, LocalTTSProvider, ConfiguredTTSProvider
from app.services.location_provider import get_location_provider, MockLocationProvider, ConfiguredLocationProvider
from app.repositories.facility_repository import FacilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.facility import FacilityCreate
from app.schemas.doctor import DoctorCreate
from app.config.check_config import validate_configuration

client = TestClient(app)

class TestPhase6ProductionReadiness:

    @classmethod
    def setup_class(cls):
        cls.db: Session = SessionLocal()

        facs = FacilityRepository.search(cls.db, q="Phase6 Test Hospital")
        if facs:
            cls.facility = facs[0]
        else:
            cls.facility = FacilityRepository.create_facility(
                cls.db,
                FacilityCreate(
                    name="Phase6 Test Hospital",
                    facility_type=FacilityType.GOVERNMENT_HOSPITAL,
                    address="Station Road, Baramati",
                    phone_number="02112999999",
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
                    name="Dr. Phase6 Doctor",
                    specialization="General Medicine",
                    qualification="MBBS",
                    facility_id=cls.facility.id,
                    department_id=dept_id,
                    phone_number="9999988888",
                    experience_years=5,
                    consultation_fee=150.0,
                    is_active=True
                )
            )

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def test_01_telephony_provider_factory_fallback(self):
        """TEST 1: Telephony provider factory resolution and mock fallback."""
        dev_provider = get_telephony_provider("development")
        assert isinstance(dev_provider, DevelopmentTelephonyProvider)

        twilio_provider = get_telephony_provider("twilio")
        assert isinstance(twilio_provider, TwilioTelephonyProvider)

        vonage_provider = get_telephony_provider("vonage")
        assert isinstance(vonage_provider, VonageTelephonyProvider)

    def test_02_sms_provider_factory_fallback(self):
        """TEST 2: SMS provider factory resolution and fallback."""
        dev_sms = get_sms_provider("development")
        assert isinstance(dev_sms, DevelopmentSMSProvider)

        twilio_sms = get_sms_provider("twilio")
        assert isinstance(twilio_sms, TwilioSMSProvider)

    @pytest.mark.anyio
    async def test_03_speech_and_tts_provider_factories(self):
        """TEST 3: Speech & TTS provider factories."""
        stt = get_speech_provider()
        assert isinstance(stt, (LocalSpeechInputProvider, ConfiguredSpeechInputProvider))

        tts = get_tts_provider()
        assert isinstance(tts, (LocalTTSProvider, ConfiguredTTSProvider))

    def test_04_location_provider_geocoding(self):
        """TEST 4: Location Provider Geocoding & Distance Calculation."""
        loc_provider = get_location_provider()
        res = loc_provider.geocode("Baramati ke paas")

        assert res["formatted_name"] == "Baramati"
        assert res["district"] == "Pune"
        assert res["is_mock"] is True

        dist = loc_provider.calculate_distance(18.1506, 74.5772, 18.5204, 73.8567)
        assert dist > 50.0  # Approx distance between Baramati and Pune in KM

    def test_05_health_endpoints_production_readiness(self):
        """TEST 5: Health & Readiness endpoints return detailed provider status."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "telephony" in data
        assert "stt" in data
        assert "tts" in data
        assert "sms" in data
        assert "location" in data

        live_resp = client.get("/health/live")
        assert live_resp.status_code == 200
        assert live_resp.json()["status"] == "alive"

        ready_resp = client.get("/health/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "ready"

        demo_resp = client.get("/api/v1/health/demo-readiness")
        assert demo_resp.status_code == 200
        assert demo_resp.json()["status"] in ["PASS", "DEGRADED"]

    def test_06_config_check_validator(self):
        """TEST 6: Production & Demo configuration CLI validator."""
        isValid = validate_configuration()
        assert isValid is True

    def test_07_atomic_slot_recheck_concurrency(self):
        """TEST 7: Atomic slot re-check prevents double-booking."""
        import uuid
        user = self.db.query(User).filter(User.phone_number == "9900011122").first()
        if not user:
            user = User(
                name="Concurrency Test User",
                phone_number="9900011122",
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

        target_date = date.today() + timedelta(days=15)
        s_time = time(14, 0)
        e_time = time(14, 30)

        # Check existing appointment
        existing = self.db.query(Appointment).filter(
            Appointment.doctor_id == self.doctor.id,
            Appointment.appointment_date == target_date,
            Appointment.start_time == s_time
        ).first()

        if not existing:
            # Create first booking
            apt1 = AppointmentRepository.create_appointment(
                db=self.db,
                patient_id=profile.id,
                doctor_id=self.doctor.id,
                facility_id=self.facility.id,
                department_id=self.doctor.department_id,
                apt_date=target_date,
                start_time=s_time,
                end_time=e_time,
                booking_channel=BookingChannel.PWA
            )
            assert apt1.id is not None

        # Attempt duplicate booking for same doctor, date, start_time
        with pytest.raises(ValueError) as exc_info:
            AppointmentRepository.create_appointment(
                db=self.db,
                patient_id=profile.id,
                doctor_id=self.doctor.id,
                facility_id=self.facility.id,
                department_id=self.doctor.department_id,
                apt_date=target_date,
                start_time=s_time,
                end_time=e_time,
                booking_channel=BookingChannel.PHONE
            )
        assert "SLOT_ALREADY_BOOKED" in str(exc_info.value)
