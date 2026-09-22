import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import Language
from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ResponseType,
)
from app.schemas.nlu import NLUIntent
from app.services.conversation_manager import ConversationManager

client = TestClient(app)

class TestPhase3Conversation:
    def setup_method(self):
        ConversationManager.clear_all_sessions()

    @pytest.mark.anyio
    async def test_session1_standard_multiturn_booking(self):
        """
        Session 1: Standard multi-turn appointment booking flow.
        Verifies session memory, entity accumulation, missing field prompts.
        """
        session_id = "test-session-1"

        # Turn 1: User states symptoms
        req1 = ConversationRequest(
            session_id=session_id,
            message="Mujhe fever aur headache hai",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert res1.session_id == session_id
        assert res1.intent in [NLUIntent.SYMPTOM_INFORMATION, NLUIntent.DOCTOR_SEARCH, NLUIntent.FACILITY_SEARCH, NLUIntent.FIND_SPECIALIST]
        assert "fever" in res1.entities.symptoms
        assert "headache" in res1.entities.symptoms
        assert "location" in res1.missing_fields
        assert res1.response_type == ResponseType.ASK_CLARIFICATION

        # Turn 2: User provides location
        req2 = ConversationRequest(
            session_id=session_id,
            message="Jaipur mein hospital batao",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.session_id == session_id
        assert res2.entities.city == "Jaipur"
        # Check symptoms retained in memory
        assert "fever" in res2.entities.symptoms
        assert "headache" in res2.entities.symptoms
        assert "location" not in res2.missing_fields
        assert res2.response_type == ResponseType.SEARCH_REQUIRED

        # Turn 3: User specifies doctor
        req3 = ConversationRequest(
            session_id=session_id,
            message="Dr. Sharma available hain kya?",
            language_hint="HI"
        )
        res3 = await ConversationManager.process_message(req3)
        assert res3.entities.doctor == "Dr. Sharma"
        assert res3.entities.city == "Jaipur"
        assert res3.intent in [NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.SLOT_SEARCH, NLUIntent.DOCTOR_SEARCH]

    @pytest.mark.anyio
    async def test_session2_entity_correction_flow(self):
        """
        Session 2: Entity correction flow ("Jaipur" -> "Ajmer").
        Verifies field replacement while retaining unrelated entities.
        """
        session_id = "test-session-2"

        # Turn 1: Initial request with Jaipur
        req1 = ConversationRequest(
            session_id=session_id,
            message="Jaipur mein ENT specialist chahiye",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert res1.entities.city == "Jaipur"
        assert res1.entities.speciality == "ENT"

        # Turn 2: Correction to Ajmer
        req2 = ConversationRequest(
            session_id=session_id,
            message="Nahi, Jaipur nahi Ajmer mein",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.entities.city == "Ajmer"
        assert res2.entities.speciality == "ENT"  # ENT specialty retained!
        assert "Ajmer" in res2.assistant_message

    @pytest.mark.anyio
    async def test_session3_contextual_short_phrase(self):
        """
        Session 3: Contextual short phrase follow-up ("Kal?").
        Verifies relative date resolution and retention of prior hospital/doctor context.
        """
        session_id = "test-session-3"

        # Turn 1: Specify facility and speciality
        req1 = ConversationRequest(
            session_id=session_id,
            message="SMS Hospital Jaipur mein Orthopedic doctor",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert res1.entities.facility in ["SMS Hospital", "Sms Hospital"]
        assert res1.entities.city == "Jaipur"
        assert (res1.entities.specialty or res1.entities.speciality).lower() in ["orthopedic", "orthopedics"]

        # Turn 2: Contextual short utterance "Kal?"
        req2 = ConversationRequest(
            session_id=session_id,
            message="Kal?",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.entities.facility in ["SMS Hospital", "Sms Hospital"]
        assert res2.entities.city == "Jaipur"
        assert (res2.entities.specialty or res2.entities.speciality).lower() in ["orthopedic", "orthopedics"]
        assert res2.entities.date in ["tomorrow", "kal"] or res2.entities.date is not None

    @pytest.mark.anyio
    async def test_session4_topic_switching(self):
        """
        Session 4: Topic switching mid-conversation (Doctor Search -> My Appointments).
        Verifies graceful intent shift and active task update.
        """
        session_id = "test-session-4"

        # Turn 1: Search doctors
        req1 = ConversationRequest(
            session_id=session_id,
            message="Jaipur mein doctor khojo",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert res1.intent in [NLUIntent.DOCTOR_SEARCH, NLUIntent.FIND_DOCTOR]

        # Turn 2: Switch topic to appointments lookup
        req2 = ConversationRequest(
            session_id=session_id,
            message="Waise mere purane appointments dikhao",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.intent == NLUIntent.MY_APPOINTMENTS
        assert res2.response_type == ResponseType.ANSWER

    @pytest.mark.anyio
    async def test_session5_emergency_override(self):
        """
        Session 5: Emergency priority override.
        Verifies immediate safety preemption even mid-dialogue.
        """
        session_id = "test-session-5"

        # Turn 1: Routine query
        req1 = ConversationRequest(
            session_id=session_id,
            message="Jaipur mein hospital batao",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert not res1.emergency

        # Turn 2: Emergency utterance
        req2 = ConversationRequest(
            session_id=session_id,
            message="Mujhe saans lene mein bahut dikkat ho rahi hai, emergency hai!",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.emergency
        assert res2.response_type == ResponseType.EMERGENCY
        assert res2.intent == NLUIntent.EMERGENCY

    @pytest.mark.anyio
    async def test_session6_unknown_ambiguous_input(self):
        """
        Session 6: Unknown or ambiguous input handling.
        Verifies polite fallback clarification prompt.
        """
        session_id = "test-session-6"

        req = ConversationRequest(
            session_id=session_id,
            message="blabla xyz random text 12345",
            language_hint="EN"
        )
        res = await ConversationManager.process_message(req)
        assert res.intent == NLUIntent.UNKNOWN
        assert res.response_type in [ResponseType.UNKNOWN, ResponseType.ASK_CLARIFICATION]
        assert len(res.assistant_message) > 0

    def test_conversation_api_endpoint(self):
        """
        Verifies POST /api/v1/conversation/message endpoint works as expected over HTTP.
        """
        payload = {
            "session_id": "api-test-session",
            "message": "Jaipur mein OPD timing kya hai?",
            "language_hint": "HI"
        }
        response = client.post("/api/v1/conversation/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "api-test-session"
        assert "intent" in data
        assert "assistant_message" in data
        assert "entities" in data
