import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app
from database import SessionLocal
import models

class TestPhase5Provider(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_provider_emergency_cases(self):
        """Test GET /api/provider/emergency_cases returns emergency triage queue"""
        res = self.client.get("/api/provider/emergency_cases")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("patient_name", data[0])
        self.assertIn("detected_issue", data[0])
        self.assertIn("urgency", data[0])

    def test_02_appointment_status_transitions(self):
        """Test status transitions (confirmed -> waiting -> consultation -> completed -> cancelled)"""
        # Create a test appointment first
        create_res = self.client.post("/api/appointments", json={
            "facility_id": 1,
            "service": "General OPD",
            "date": "Tomorrow",
            "time": "10:30 AM",
            "patient_name": "Phase5 Test Patient",
            "phone": "+91-9998887776",
            "doctor_name": "Dr. Sharma"
        })
        self.assertEqual(create_res.status_code, 200)
        apt_id = create_res.json()["id"]

        statuses = ["waiting", "consultation", "completed", "cancelled", "confirmed"]
        for st in statuses:
            status_res = self.client.patch(f"/api/appointments/{apt_id}/status?status={st}")
            self.assertEqual(status_res.status_code, 200, f"Failed updating status to {st}")
            self.assertEqual(status_res.json()["status"], st)

            # Check DB state
            get_res = self.client.get(f"/api/appointments/{apt_id}")
            self.assertEqual(get_res.status_code, 200)
            self.assertEqual(get_res.json()["status"], st)

    def test_03_doctor_slot_management(self):
        """Test adding a slot, toggling availability, and deleting a slot"""
        # 1. Add slot
        add_res = self.client.post("/api/facilities/1/slots", json={
            "facility_id": 1,
            "date": "Tomorrow",
            "time": "05:00 PM",
            "doctor_name": "Dr. Provider Test",
            "department": "Pediatrics",
            "available": True
        })
        self.assertEqual(add_res.status_code, 200)
        slot_id = add_res.json()["id"]
        self.assertTrue(add_res.json()["available"])

        # 2. Toggle slot availability
        toggle_res = self.client.patch(f"/api/slots/{slot_id}/toggle")
        self.assertEqual(toggle_res.status_code, 200)
        self.assertFalse(toggle_res.json()["available"])

        # 3. Delete slot
        del_res = self.client.delete(f"/api/slots/{slot_id}")
        self.assertEqual(del_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
