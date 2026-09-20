import unittest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models import User, PatientProfile, Facility, Department, Doctor, Appointment
from app.models.enums import UserRole, BookingChannel

from scripts.seed import seed_database

class TestPhase2AuthAndPermissions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_customer_registration_and_duplicate_reject(self):
        unique_phone = f"+91-98{uuid.uuid4().hex[:8]}"
        reg_payload = {
            "name": "Ramesh Bhosale",
            "phone_number": unique_phone,
            "email": f"ramesh_{uuid.uuid4().hex[:4]}@demo.in",
            "password": "CustomerSecret123!",
            "preferred_language": "HI",
            "village": "Indapur Village",
            "district": "Pune",
            "pincode": "413132"
        }
        res = self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Ramesh Bhosale")
        self.assertEqual(data["role"], "CUSTOMER")
        self.assertNotIn("password", data)

        # Re-registering exact same phone must fail with 409
        dup_res = self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertEqual(dup_res.status_code, 409)

    def test_login_and_jwt_issuance(self):
        # Test valid login with seeded customer
        login_payload = {
            "phone_number": "+91-9876543210",
            "password": "UserPass123!"
        }
        res = self.client.post("/api/v1/auth/login", json=login_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["role"], "CUSTOMER")

        token = data["access_token"]

        # Test /auth/me with valid Bearer token
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.json()
        self.assertEqual(me_data["phone_number"], "+91-9876543210")

        # Test invalid password login
        bad_pass_res = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9876543210", "password": "WrongPassword"})
        self.assertEqual(bad_pass_res.status_code, 401)

        # Test non-existent phone login
        bad_phone_res = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-0000000000", "password": "UserPass123!"})
        self.assertEqual(bad_phone_res.status_code, 401)

    def test_role_based_access_control(self):
        """Customer role attempting ADMIN endpoint POST /facilities must be rejected with 403 Forbidden."""
        # Login as Customer
        cust_login = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9876543210", "password": "UserPass123!"})
        cust_token = cust_login.json()["access_token"]

        fac_payload = {
            "name": f"Unauthorized Private Clinic {uuid.uuid4().hex[:4]}",
            "facility_type": "CLINIC",
            "address": "Main Road",
            "district": "Pune",
            "pincode": "413106",
            "phone_number": "+91-2112-999999"
        }

        # Customer attempt -> 403 Forbidden
        cust_res = self.client.post("/api/v1/facilities/", json=fac_payload, headers={"Authorization": f"Bearer {cust_token}"})
        self.assertEqual(cust_res.status_code, 403)
        self.assertIn("Access denied", cust_res.json()["detail"])

        # Login as Admin
        admin_login = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9900000001", "password": "AdminPass123!"})
        admin_token = admin_login.json()["access_token"]

        # Admin attempt -> 201 Created
        admin_res = self.client.post("/api/v1/facilities/", json=fac_payload, headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(admin_res.status_code, 201)

    def test_object_level_authorization(self):
        """Verify Customer A cannot view Customer B's appointment."""
        # 1. Login Customer 1 (Rahul Pawar)
        c1_login = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9876543210", "password": "UserPass123!"})
        c1_token = c1_login.json()["access_token"]
        c1_user_id = c1_login.json()["user"]["id"]
        c1_patient = self.db.query(PatientProfile).filter(PatientProfile.user_id == c1_user_id).first()

        # 2. Login Customer 2 (Anita Kamble)
        c2_login = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9822114455", "password": "UserPass123!"})
        c2_token = c2_login.json()["access_token"]

        doc = self.db.query(Doctor).first()
        fac = self.db.query(Facility).first()
        dept = self.db.query(Department).first()

        unique_time = f"{14 + (int(uuid.uuid4().hex[:2], 16) % 8):02d}:00:00"
        apt_payload = {
            "patient_id": c1_patient.id,
            "doctor_id": doc.id,
            "facility_id": fac.id,
            "department_id": dept.id,
            "appointment_date": "2026-12-25",
            "start_time": unique_time,
            "end_time": f"{int(unique_time[:2]):02d}:30:00",
            "booking_channel": "PWA",
            "reason_for_visit": "Customer 1 Appointment"
        }
        apt_res = self.client.post("/api/v1/appointments/", json=apt_payload, headers={"Authorization": f"Bearer {c1_token}"})
        self.assertEqual(apt_res.status_code, 201)
        apt_id = apt_res.json()["id"]

        # Customer 1 GET own appointment -> 200 OK
        c1_get = self.client.get(f"/api/v1/appointments/{apt_id}", headers={"Authorization": f"Bearer {c1_token}"})
        self.assertEqual(c1_get.status_code, 200)

        # Customer 2 GET Customer 1's appointment -> MUST FAIL WITH 403 FORBIDDEN
        c2_get = self.client.get(f"/api/v1/appointments/{apt_id}", headers={"Authorization": f"Bearer {c2_token}"})
        self.assertEqual(c2_get.status_code, 403)
        self.assertIn("Access denied", str(c2_get.json()["detail"]))

if __name__ == "__main__":
    unittest.main()
