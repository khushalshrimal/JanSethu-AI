from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["demo_mode"] == True

def test_get_facilities():
    response = client.get("/facilities")
    assert response.status_code == 200
    facilities = response.json()
    assert len(facilities) > 0

def test_get_facility_detail():
    response = client.get("/facilities/1")
    assert response.status_code == 200
    fac = response.json()
    assert fac["id"] == 1

def test_get_facility_slots():
    response = client.get("/facilities/1/slots")
    assert response.status_code == 200
    slots = response.json()
    assert isinstance(slots, list)

def test_create_and_get_appointment():
    # 1. Create appointment
    payload = {
        "facility_id": 1,
        "service": "General OPD",
        "date": "Tomorrow",
        "time": "10:30 AM",
        "patient_name": "Test Patient",
        "phone": "+91-9999999999"
    }
    create_res = client.post("/appointments", json=payload)
    assert create_res.status_code == 200
    apt_data = create_res.json()
    apt_id = apt_data["id"]
    assert apt_data["patient_name"] == "Test Patient"
    assert apt_data["status"] == "pending"

    # 2. Get appointment by ID
    get_res = client.get(f"/appointments/{apt_id}")
    assert get_res.status_code == 200
    fetched_apt = get_res.json()
    assert fetched_apt["id"] == apt_id
    assert fetched_apt["patient_name"] == "Test Patient"

def test_emergency():
    response = client.get("/emergency")
    assert response.status_code == 200
    data = response.json()
    assert len(data["contacts"]) >= 3

if __name__ == "__main__":
    test_health()
    test_get_facilities()
    test_get_facility_detail()
    test_get_facility_slots()
    test_create_and_get_appointment()
    test_emergency()
    print("All Phase 2 Backend API Tests Passed Cleanly!")
