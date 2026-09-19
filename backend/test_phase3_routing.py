import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_phase3_smart_facility_routing_ranking():
    """Test smart routing ranks doctor-available facility (4.2km) ahead of doctor-unavailable facility (2.1km)."""
    response = client.get("/api/facilities?search=Baramati")
    assert response.status_code == 200
    facilities = response.json()
    assert len(facilities) >= 2
    
    # First facility must have doctor available
    first_fac = facilities[0]
    assert first_fac["doctor_available"] == True
    assert "District Civil Hospital" in first_fac["name"] or first_fac["smart_score"] >= 80

def test_phase3_emergency_facility_ranking():
    """Test emergency query prioritizes 24/7 emergency-capable facilities."""
    response = client.get("/api/facilities?is_emergency=true")
    assert response.status_code == 200
    facilities = response.json()
    assert len(facilities) > 0
    assert facilities[0]["emergency_available"] == True

def test_phase3_facility_response_metadata():
    """Test API includes smart routing metadata attributes."""
    response = client.get("/api/facilities")
    assert response.status_code == 200
    facilities = response.json()
    fac = facilities[0]
    assert "simulated_distance" in fac
    assert "doctor_available" in fac
    assert "emergency_available" in fac
    assert "smart_score" in fac

if __name__ == "__main__":
    test_phase3_smart_facility_routing_ranking()
    test_phase3_emergency_facility_ranking()
    test_phase3_facility_response_metadata()
    print("ALL PHASE 3 SMART FACILITY ROUTING TESTS PASSED CLEANLY!")
