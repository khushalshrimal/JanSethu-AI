from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_telephony_channel():
    # 1. Config check
    res_cfg = client.get("/telephony/config")
    assert res_cfg.status_code == 200
    assert res_cfg.json()["mock_mode"] == True

    # 2. Incoming phone call welcome step
    res1 = client.post("/telephony/voice", json={"Caller": "+91-9876543210", "Step": "welcome"})
    assert res1.status_code == 200
    assert "<Response>" in res1.json()["twiml_xml"]

    # 3. Keypad press '1' for Hindi
    res2 = client.post("/telephony/gather", json={"Caller": "+91-9876543210", "Digits": "1", "Step": "gather_language"})
    assert res2.status_code == 200
    assert "हिंदी" in res2.json()["speech_text_hi"]

    # 4. Spoken voice input appointment request with complete details
    res3 = client.post("/telephony/gather", json={
        "Caller": "+91-9876543210",
        "SpeechResult": "I need a fever doctor tomorrow in Sanganer",
        "Language": "en"
    })
    assert res3.status_code == 200
    assert res3.json()["sms_sent"] == True
    assert "Ticket #" in res3.json()["speech_text"]

if __name__ == "__main__":
    test_telephony_channel()
    print("All Phase 7 Telephony / Keypad Phone Channel Tests Passed Cleanly!")
