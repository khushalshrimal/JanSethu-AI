import pytest
import asyncio
from app.schemas.conversation import ConversationRequest, ConversationResponse, ResponseType
from app.services.conversation_manager import ConversationManager
from app.services.safety_engine import SafetyEngine, EmergencyLevel
from app.schemas.nlu import NLUIntent

class TestPhase6Emergency:

    def setup_method(self):
        ConversationManager.clear_all_sessions()

    @pytest.mark.anyio
    async def test_01_breathing_emergency(self):
        req = ConversationRequest(
            session_id="test-em-01",
            message="Mujhe saans lene mein bahut dikkat ho rahi hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_level == "HIGH_CONFIDENCE_EMERGENCY"
        assert res.intent == NLUIntent.EMERGENCY
        assert "saans" in res.assistant_message.lower() or "emergency" in res.assistant_message.lower()

    @pytest.mark.anyio
    async def test_02_chest_pain_emergency(self):
        req = ConversationRequest(
            session_id="test-em-02",
            message="Mere seene mein bahut tez dard ho raha hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_type == "CHEST_PAIN"

    @pytest.mark.anyio
    async def test_03_accident_emergency(self):
        req = ConversationRequest(
            session_id="test-em-03",
            message="Major accident ho gaya hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_type == "ACCIDENT"

    @pytest.mark.anyio
    async def test_04_heavy_bleeding_emergency(self):
        req = ConversationRequest(
            session_id="test-em-04",
            message="Bahut zyada khoon nikal raha hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_type == "BLEEDING"

    @pytest.mark.anyio
    async def test_05_normal_symptom_not_emergency(self):
        req = ConversationRequest(
            session_id="test-em-05",
            message="Mujhe halka headache hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is False
        assert res.emergency_level == "NORMAL"

    @pytest.mark.anyio
    async def test_06_general_info_query_not_personal_emergency(self):
        req = ConversationRequest(
            session_id="test-em-06",
            message="Emergency department kab open hai?",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is False
        assert res.emergency_level in ["NORMAL", "POTENTIAL_EMERGENCY"]

    @pytest.mark.anyio
    async def test_07_emergency_with_location_included(self):
        req = ConversationRequest(
            session_id="test-em-07",
            message="Mujhe saans lene mein dikkat hai, main Malviya Nagar Jaipur mein hoon.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_status == "ASSISTANCE_SIMULATED"
        assert res.ambulance_request_id is not None
        assert res.ambulance_request_id.startswith("AMB-MOCK-")
        assert res.emergency_location is not None

    @pytest.mark.anyio
    async def test_08_emergency_multi_turn_location_followup(self):
        req1 = ConversationRequest(
            session_id="test-em-08",
            message="Mujhe saans lene mein bahut dikkat ho rahi hai.",
            language_hint="HI"
        )
        res1: ConversationResponse = await ConversationManager.process_message(req1)
        assert res1.emergency is True
        assert res1.emergency_status == "LOCATION_REQUIRED"

        req2 = ConversationRequest(
            session_id="test-em-08",
            message="32 Prem Nagar Jaipur 302017",
            language_hint="HI"
        )
        res2: ConversationResponse = await ConversationManager.process_message(req2)
        assert res2.emergency is True
        assert res2.emergency_status == "ASSISTANCE_SIMULATED"
        assert res2.ambulance_request_id is not None
        assert res2.emergency_location is not None

    @pytest.mark.anyio
    async def test_09_emergency_interrupts_ai_speech(self):
        req = ConversationRequest(
            session_id="test-em-09",
            message="Mujhe emergency hai, 108 chahiye!",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.response_type == ResponseType.EMERGENCY

    @pytest.mark.anyio
    async def test_10_emergency_interrupts_booking_flow(self):
        req1 = ConversationRequest(
            session_id="test-em-10",
            message="Dr Lakshya ka kal 11 baje slot book karna hai.",
            language_hint="HI"
        )
        res1: ConversationResponse = await ConversationManager.process_message(req1)

        req2 = ConversationRequest(
            session_id="test-em-10",
            message="Actually mujhe bahut tez chest pain ho raha hai.",
            language_hint="HI"
        )
        res2: ConversationResponse = await ConversationManager.process_message(req2)
        assert res2.emergency is True
        assert res2.intent == NLUIntent.EMERGENCY
        assert res2.entities.referral_id is None

    @pytest.mark.anyio
    async def test_11_emergency_after_appointment_created(self):
        state = ConversationManager.get_or_create_session("test-em-11")
        state.entities.referral_id = "JAN-REF-2026-9999"

        req = ConversationRequest(
            session_id="test-em-11",
            message="Mujhe saans lene mein dikkat ho rahi hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.entities.referral_id == "JAN-REF-2026-9999"

    @pytest.mark.anyio
    async def test_12_mock_ambulance_flow(self):
        req = ConversationRequest(
            session_id="test-em-12",
            message="Saans nahi aa rahi, 32 Prem Nagar Jaipur",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_status == "ASSISTANCE_SIMULATED"
        assert "AMB-MOCK-" in res.ambulance_request_id

    @pytest.mark.anyio
    async def test_13_no_fake_dispatch_claim(self):
        req = ConversationRequest(
            session_id="test-em-13",
            message="Saans nahi aa rahi, Baramati Pune",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert "simulated" in res.assistant_message.lower() or "prototype" in res.assistant_message.lower() or "108" in res.assistant_message

    @pytest.mark.anyio
    async def test_14_missing_location_prompts_user(self):
        req = ConversationRequest(
            session_id="test-em-14",
            message="Mujhe chest pain hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_status == "LOCATION_REQUIRED"

    @pytest.mark.anyio
    async def test_15_existing_session_location_reused(self):
        state = ConversationManager.get_or_create_session("test-em-15")
        state.entities.city = "Jaipur"
        state.entities.location = "Malviya Nagar"

        req = ConversationRequest(
            session_id="test-em-15",
            message="Mujhe saans lene mein bahut dikkat ho rahi hai.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is True
        assert res.emergency_status == "ASSISTANCE_SIMULATED"
        assert res.ambulance_request_id is not None

    @pytest.mark.anyio
    async def test_16_false_positive_context(self):
        req = ConversationRequest(
            session_id="test-em-16",
            message="Emergency ward ka address batao.",
            language_hint="HI"
        )
        res: ConversationResponse = await ConversationManager.process_message(req)
        assert res.emergency is False

    @pytest.mark.anyio
    async def test_17_emergency_cancellation(self):
        req1 = ConversationRequest(
            session_id="test-em-17",
            message="Saans nahi aa rahi",
            language_hint="HI"
        )
        res1 = await ConversationManager.process_message(req1)
        assert res1.emergency is True

        req2 = ConversationRequest(
            session_id="test-em-17",
            message="Galti se emergency bola tha, ab emergency nahi hai.",
            language_hint="HI"
        )
        res2 = await ConversationManager.process_message(req2)
        assert res2.emergency is False
        assert res2.emergency_status == "RESOLVED"

    @pytest.mark.anyio
    async def test_18_llm_unavailable_deterministic_fallback(self):
        level, emerg_type, conf, matched = SafetyEngine.classify_emergency("Mujhe saans lene mein bahut dikkat ho rahi hai.")
        assert level == EmergencyLevel.HIGH_CONFIDENCE_EMERGENCY
        assert conf >= 0.9
        assert emerg_type == "BREATHING"
