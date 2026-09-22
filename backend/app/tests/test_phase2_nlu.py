import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.llm_service import LLMService, DeterministicNLUParser
from app.services.safety_engine import SafetyEngine
from app.schemas.nlu import NLUIntent, Language

client = TestClient(app)

class TestPhase2NLU:

    @pytest.mark.anyio
    async def test_01_facility_search_location(self):
        msg = "Mujhe Jaipur mein hospital chahiye"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent in [NLUIntent.FACILITY_SEARCH, NLUIntent.DOCTOR_SEARCH]
        assert res.entities.city == "Jaipur"
        assert res.emergency is False

    @pytest.mark.anyio
    async def test_02_facility_search_symptom(self):
        msg = "Fever ke liye nearby hospital batao"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent in [NLUIntent.FACILITY_SEARCH, NLUIntent.FIND_FACILITY, NLUIntent.FIND_SPECIALIST]
        assert "fever" in res.entities.symptoms or res.entities.department in ["general medicine", "General Medicine"]
        assert res.emergency is False

    @pytest.mark.anyio
    async def test_03_doctor_search_speciality(self):
        msg = "Mujhe Jaipur mein orthopedic doctor chahiye"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent in [NLUIntent.DOCTOR_SEARCH, NLUIntent.FIND_DOCTOR, NLUIntent.FIND_SPECIALIST]
        assert res.entities.city == "Jaipur"
        assert res.entities.specialty in ["Orthopedics", "Orthopedic", "orthopedic"] or res.entities.speciality in ["Orthopedics", "Orthopedic", "orthopedic"]

    @pytest.mark.anyio
    async def test_04_doctor_availability(self):
        msg = "Hospital A mein Dr Lakshya available hain?"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent in [NLUIntent.DOCTOR_AVAILABILITY, NLUIntent.CHECK_AVAILABILITY]
        assert res.entities.facility == "Hospital A"
        assert res.entities.doctor == "Dr Lakshya"

    @pytest.mark.anyio
    async def test_05_slot_search_time_period(self):
        msg = "Kal morning Dr Lakshya ka slot hai?"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent in [NLUIntent.SLOT_SEARCH, NLUIntent.CHECK_AVAILABILITY]
        assert res.entities.doctor == "Dr Lakshya"
        assert res.entities.date == "tomorrow"
        assert res.entities.time_period == "morning"

    @pytest.mark.anyio
    async def test_06_book_appointment_specific_time(self):
        msg = "Dr Lakshya ko kal 11 baje book kar do"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent == NLUIntent.BOOK_APPOINTMENT
        assert res.entities.doctor == "Dr Lakshya"
        assert res.entities.date == "tomorrow"
        assert res.entities.time == "11:00"

    @pytest.mark.anyio
    async def test_07_emergency_detection(self):
        msg = "Mujhe saans lene mein bahut dikkat ho rahi hai"
        res = await LLMService.analyze_nlu(msg)
        assert res.intent == NLUIntent.EMERGENCY
        assert res.emergency is True
        assert res.confidence >= 0.95

    @pytest.mark.anyio
    async def test_08_location_correction_marathi_hindi(self):
        msg = "नहीं, जयपुर नहीं अजमेर"
        res = await LLMService.analyze_nlu(msg, conversation_context={"city": "Jaipur"})
        assert res.entities.city == "Ajmer"
        assert res.entities.is_correction is True

    @pytest.mark.anyio
    async def test_09_api_endpoint_analyze(self):
        response = client.post(
            "/api/v1/ai/analyze",
            json={
                "message": "Mujhe Jaipur mein orthopedic doctor chahiye",
                "conversation_context": None,
                "language_hint": "hi"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] in ["DOCTOR_SEARCH", "FIND_DOCTOR", "FIND_SPECIALIST"]
        assert data["entities"]["city"] == "Jaipur"
        assert data["entities"]["specialty"] in ["Orthopedics", "Orthopedic", "orthopedic"] or data["entities"]["speciality"] in ["Orthopedics", "Orthopedic", "orthopedic"]
        assert data["emergency"] is False

    def test_10_security_no_secret_keys_exposed(self):
        response = client.post(
            "/api/v1/ai/analyze",
            json={"message": "hello"}
        )
        assert response.status_code == 200
        content_str = response.text.lower()
        assert "secret_key" not in content_str
        assert "llm_api_key" not in content_str
        assert "password" not in content_str
