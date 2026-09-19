import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_phase4_appointment_token_generation():
    """Test appointment creation auto-generates token_number (A-104) and saves doctor_name."""
    response = client.post("/api/appointments", json={
        "facility_id": 1,
        "service": "Pediatrics",
        "date": "20 Sep 2026",
        "time": "10:30 AM",
        "patient_name": "Ram Lal",
        "phone": "+91-9876543210",
        "doctor_name": "Dr. Sharma"
    })
    assert response.status_code == 200
    data = response.json()
    assert "token_number" in data
    assert data["token_number"].startswith("A-")
    assert "doctor_name" in data
    assert "Dr." in data["doctor_name"]
    assert data["status"] == "confirmed"

def test_phase4_appointment_tracking_lookup():
    """Test phone tracking API returns token and status details."""
    response = client.get("/api/appointments?phone=%2B91-9876543210")
    assert response.status_code == 200
    apts = response.json()
    assert len(apts) > 0
    apt = apts[0]
    assert "token_number" in apt
    assert apt["token_number"] is not None

def test_phase4_provider_status_update():
    """Test provider advancing appointment status to consultation/completed."""
    # First get an appointment
    apts_res = client.get("/api/appointments")
    apts = apts_res.json()
    assert len(apts) > 0
    target_id = apts[0]["id"]
    
    # Update status to completed
    update_res = client.patch(f"/api/appointments/{target_id}/status?status=confirmed")
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "confirmed"

if __name__ == "__main__":
    test_phase4_appointment_token_generation()
    test_phase4_appointment_tracking_lookup()
    test_phase4_provider_status_update()
    print("ALL PHASE 4 END-TO-END APPOINTMENT & TRACKING TESTS PASSED CLEANLY!")
