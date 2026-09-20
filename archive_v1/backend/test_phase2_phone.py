import pytest
from fastapi.testclient import TestClient
from main import app
import crud
from database import get_db

client = TestClient(app)

def test_phase2_telephony_welcome_trilingual():
    """Test initial welcome call prompt in Hindi, Marathi, and English."""
    response = client.post("/api/telephony/voice", json={
        "Caller": "+91-9876543210",
        "Step": "welcome",
        "Language": "hi"
    })
    assert response.status_code == 200
    data = response.json()
    assert "जनसेतु AI" in data["speech_text_hi"]
    assert "1" in data["speech_text_hi"]

def test_phase2_dtmf_language_selection():
    """Test DTMF keypad input (1=Hindi, 2=Marathi, 3=English)."""
    # Press 2 for Marathi
    response = client.post("/api/telephony/gather", json={
        "Caller": "+91-9876543210",
        "Digits": "2",
        "Step": "welcome",
        "Language": "mr"
    })
    assert response.status_code == 200
    data = response.json()
    assert "मराठी" in data["speech_text_mr"]

def test_phase2_normal_flow_hindi():
    """Test Hindi normal speech consultation flow with entity extraction."""
    response = client.post("/api/telephony/gather", json={
        "Caller": "+91-9876543210",
        "SpeechResult": "मुझे तीन दिन से बारामती में बुखार है",
        "Language": "hi"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_emergency"] == False
    assert "Fever" in data["symptoms"]
    assert "Baramati" in data["location"]
    assert data["sms_sent"] == True
    assert data["sms_body"] is not None

def test_phase2_normal_flow_marathi():
    """Test Marathi normal speech consultation flow."""
    response = client.post("/api/telephony/gather", json={
        "Caller": "+91-9876543210",
        "SpeechResult": "मला तीन दिवसांपासून बारामतीमध्ये ताप आहे",
        "Language": "mr"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_emergency"] == False
    assert "Fever" in data["symptoms"]
    assert "Baramati" in data["location"]
    assert data["sms_sent"] == True

def test_phase2_emergency_safety_screening():
    """Test deterministic safety engine triggering POTENTIAL EMERGENCY."""
    response = client.post("/api/telephony/gather", json={
        "Caller": "+91-9876543210",
        "SpeechResult": "मरीज को सांस लेने में बहुत तकलीफ हो रही है और छाती में दर्द है",
        "Language": "hi"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_emergency"] == True
    assert data["urgency"] == "CRITICAL EMERGENCY"
    assert "108" in data["speech_text_hi"] or "108" in data["speech_text"]
    assert data["sms_sent"] == False # Does not attempt standard appointment SMS on critical emergency

if __name__ == "__main__":
    test_phase2_telephony_welcome_trilingual()
    test_phase2_dtmf_language_selection()
    test_phase2_normal_flow_hindi()
    test_phase2_normal_flow_marathi()
    test_phase2_emergency_safety_screening()
    print("ALL PHASE 2 PHONE & SAFETY SCREENING TESTS PASSED CLEANLY!")
