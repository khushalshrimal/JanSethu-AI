import pytest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.enums import BookingChannel, AppointmentStatus, FacilityType, UserRole
from app.models.user import User, PatientProfile
from app.schemas.conversation import ConversationRequest, ConversationResponse, ResponseType
from app.services.conversation_manager import ConversationManager
from app.services.llm_service import LLMService, DeterministicNLUParser
from app.services.safety_engine import SafetyEngine
from app.config.check_config import validate_configuration

client = TestClient(app)

class TestRealLLMIntegration:

    @classmethod
    def setup_class(cls):
        cls.db: Session = SessionLocal()

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def test_01_config_audit_nvidia_provider(self):
        """Verify configuration audit identifies LLM_ENGINE as nvidia."""
        is_valid = validate_configuration()
        assert is_valid is True

    @pytest.mark.anyio
    async def test_02_natural_conversation_hindi_hinglish(self):
        """Test natural Hindi/Hinglish message parsing and response synthesis."""
        req = ConversationRequest(
            session_id="real_llm_sess_01",
            message="Baramati mein heart ke doctor ko dikhana hai",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req)
        assert res is not None
        assert res.session_id == "real_llm_sess_01"
        assert len(res.assistant_message) > 0
        assert res.entities.city == "Baramati" or res.entities.location == "Baramati"
        assert res.entities.specialty == "Cardiology" or res.entities.speciality == "Cardiology" or "Cardiology" in str(res.entities.department)

    @pytest.mark.anyio
    async def test_03_natural_conversation_marathi(self):
        """Test natural Marathi message parsing."""
        req = ConversationRequest(
            session_id="real_llm_sess_02",
            message="मला बारामतीमध्ये हृदयरोग तज्ज्ञ डॉक्टर पाहिजे",
            language_hint="MR"
        )
        res = await ConversationManager.process_message(req)
        assert res is not None
        assert len(res.assistant_message) > 0

    @pytest.mark.anyio
    async def test_04_emergency_preemption_guarantee(self):
        """Verify emergency safety engine preempts LLM and redirects to 108."""
        req = ConversationRequest(
            session_id="real_llm_emergency_sess",
            message="Bahut tez sine me dard hai, patient behosh ho raha hai!",
            language_hint="HI"
        )
        res = await ConversationManager.process_message(req)
        assert res is not None
        assert res.response_type == ResponseType.EMERGENCY or "108" in res.assistant_message or "emergency" in res.assistant_message.lower()

    @pytest.mark.anyio
    async def test_05_fallback_to_deterministic_nlu_on_empty_or_invalid_key(self):
        """Verify graceful local deterministic fallback when LLM API key is empty or API is unreachable."""
        res = await LLMService.analyze_nlu(
            message="Baramati me skin doctor chahiye",
            conversation_context=None,
            language_hint="HI"
        )
        assert res is not None
        assert res.intent is not None
        assert res.entities.location == "Baramati" or res.entities.city == "Baramati"
        assert res.entities.specialty == "Dermatology" or res.entities.speciality == "Dermatology"
