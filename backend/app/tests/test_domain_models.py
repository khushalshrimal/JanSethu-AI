import unittest
import uuid
from datetime import date, time
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models import User, Facility, Department, Doctor, PatientProfile, Appointment
from app.models.enums import UserRole, BookingChannel

from scripts.seed import seed_database

class TestPhase1DomainModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_health_check_continued(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")

    def test_user_creation_and_hash(self):
        unique_phone = f"+91-99{uuid.uuid4().hex[:8]}"
        user_data = {
            "name": "Test Patient User",
            "phone_number": unique_phone,
            "email": f"testpatient_{uuid.uuid4().hex[:4]}@jansethu.in",
            "password": "SecurePassword123!",
            "preferred_language": "HI",
            "village": "Test Village",
            "district": "Pune",
            "pincode": "413106"
        }
        response = self.client.post("/api/v1/auth/register", json=user_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Test Patient User")
        self.assertNotIn("password", data)

    def test_facility_and_doctor_retrieval(self):
        response = self.client.get("/api/v1/facilities/")
        self.assertEqual(response.status_code, 200)
        facs = response.json()
        self.assertGreater(len(facs), 0)
        fac_id = facs[0]["id"]

        doc_resp = self.client.get(f"/api/v1/doctors/?facility_id={fac_id}")
        self.assertEqual(doc_resp.status_code, 200)
        docs = doc_resp.json()
        self.assertGreater(len(docs), 0)

    def test_double_booking_prevention(self):
        """Verify that booking the exact same doctor/date/time slot twice fails with 409 Conflict."""
        # Authenticate as customer
        login_res = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9876543210", "password": "UserPass123!"})
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        fac = self.db.query(Facility).first()
        dept = self.db.query(Department).first()
        doc = self.db.query(Doctor).first()
        user = self.db.query(User).filter(User.phone_number == "+91-9876543210").first()

        self.assertIsNotNone(fac)
        self.assertIsNotNone(doc)
        self.assertIsNotNone(user.patient_profile)

        unique_date = f"2027-01-{10 + (int(uuid.uuid4().hex[:2], 16) % 15):02d}"
        apt_payload = {
            "patient_id": user.patient_profile.id,
            "doctor_id": doc.id,
            "facility_id": fac.id,
            "department_id": dept.id,
            "appointment_date": unique_date,
            "start_time": "10:00:00",
            "end_time": "10:30:00",
            "booking_channel": "PWA",
            "reason_for_visit": "Test OPD Consultation"
        }

        # First booking - should succeed (201 Created)
        resp1 = self.client.post("/api/v1/appointments/", json=apt_payload, headers=auth_headers)
        self.assertEqual(resp1.status_code, 201)
        data1 = resp1.json()
        self.assertIn("JS-2026-", data1["confirmation_code"])

        # Second booking for EXACT same doctor, date, and start_time - MUST FAIL with 409 Conflict
        resp2 = self.client.post("/api/v1/appointments/", json=apt_payload, headers=auth_headers)
        self.assertEqual(resp2.status_code, 409)
        data2 = resp2.json()
        self.assertEqual(data2["detail"]["code"], "SLOT_ALREADY_BOOKED")

if __name__ == "__main__":
    unittest.main()
