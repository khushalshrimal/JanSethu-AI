import unittest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.enums import UserRole, AppointmentStatus
from app.models.user import User
from app.models.facility import Facility, Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.core.security import create_access_token
from app.utils.timezone import get_today_ist

client = TestClient(app)

class TestPhase8ProviderAdmin(unittest.TestCase):
    def setUp(self):
        self.db: Session = SessionLocal()
        self.today = get_today_ist()
        self.tomorrow = self.today + timedelta(days=1)

        # Retrieve test users with proper roles
        self.customer = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()
        self.admin = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        self.provider = self.db.query(User).filter(User.role == UserRole.PROVIDER).first()

        # Auth headers
        self.customer_headers = {"Authorization": f"Bearer {create_access_token(self.customer.id)}"}
        self.admin_headers = {"Authorization": f"Bearer {create_access_token(self.admin.id)}"}
        self.provider_headers = {"Authorization": f"Bearer {create_access_token(self.provider.id)}"}

        # Doctor profile
        self.doctor = self.db.query(Doctor).first()

    def tearDown(self):
        self.db.close()

    def test_provider_dashboard_metrics(self):
        res = client.get("/api/v1/provider/dashboard", headers=self.provider_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("today_total", data)
        self.assertIn("waiting_count", data)
        self.assertIn("completed_count", data)

    def test_provider_appointment_status_update_and_audit(self):
        apt = self.db.query(Appointment).filter(Appointment.doctor_id == self.doctor.id).first()
        if not apt:
            self.skipTest("No appointment found for test")

        res = client.put(
            f"/api/v1/provider/appointments/{apt.id}/status",
            headers=self.provider_headers,
            json={"status": "IN_PROGRESS", "notes": "Patient entered OPD consultation room"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "IN_PROGRESS")

        # Verify transition to COMPLETED
        res_comp = client.put(
            f"/api/v1/provider/appointments/{apt.id}/status",
            headers=self.provider_headers,
            json={"status": "COMPLETED", "notes": "Consultation complete, prescription issued"}
        )
        self.assertEqual(res_comp.status_code, 200)
        self.assertEqual(res_comp.json()["status"], "COMPLETED")

    def test_provider_leave_exception_blocks_slots(self):
        leave_date = self.tomorrow.strftime("%Y-%m-%d")
        res = client.post(
            "/api/v1/provider/schedule-exceptions",
            headers=self.provider_headers,
            json={
                "doctor_id": self.doctor.id,
                "date": leave_date,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "reason": "Emergency OPD Leave"
            }
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json()["is_active"])

        # Check availability for that doctor on leave_date -> available slots must be 0
        avail_res = client.get(f"/api/v1/doctors/{self.doctor.id}/availability?date={leave_date}")
        self.assertEqual(avail_res.status_code, 200)
        slots = avail_res.json()["slots"]
        available_slots = [s for s in slots if s["status"] == "AVAILABLE"]
        self.assertEqual(len(available_slots), 0)

    def test_admin_dashboard_metrics(self):
        res = client.get("/api/v1/admin/dashboard", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_facilities"], 1)
        self.assertGreaterEqual(data["total_doctors"], 1)

    def test_admin_doctor_onboarding_and_status_toggle(self):
        fac = self.db.query(Facility).first()
        dept = self.db.query(Department).first()

        res = client.post(
            "/api/v1/admin/doctors",
            headers=self.admin_headers,
            json={
                "facility_id": fac.id,
                "department_id": dept.id,
                "name": "Dr. Phase8 Test Doctor",
                "qualification": "MBBS, MD",
                "specialization": "Pediatrics",
                "phone_number": "+919876543299",
                "consultation_type": "OPD_IN_PERSON",
                "is_active": True
            }
        )
        self.assertEqual(res.status_code, 201)
        doc_data = res.json()
        doc_id = doc_data["id"]
        self.assertEqual(doc_data["name"], "Dr. Phase8 Test Doctor")

        # Toggle inactive
        res_toggle = client.patch(
            f"/api/v1/admin/doctors/{doc_id}/status",
            headers=self.admin_headers,
            json={"is_active": False}
        )
        self.assertEqual(res_toggle.status_code, 200)
        self.assertFalse(res_toggle.json()["is_active"])

    def test_admin_emergency_contacts_crud(self):
        res = client.post(
            "/api/v1/admin/emergency-contacts",
            headers=self.admin_headers,
            json={
                "name": "District Emergency Response Unit",
                "phone_number": "108",
                "contact_type": "AMBULANCE",
                "priority": 1,
                "is_active": True
            }
        )
        self.assertEqual(res.status_code, 201)
        c_id = res.json()["id"]

        res_list = client.get("/api/v1/admin/emergency-contacts", headers=self.admin_headers)
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        res_del = client.delete(f"/api/v1/admin/emergency-contacts/{c_id}", headers=self.admin_headers)
        self.assertEqual(res_del.status_code, 204)

    def test_admin_audit_logs_query(self):
        res = client.get("/api/v1/admin/audit-logs", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        logs = res.json()
        self.assertIsInstance(logs, list)

    def test_rbac_protection_customer_forbidden(self):
        res_prov = client.get("/api/v1/provider/dashboard", headers=self.customer_headers)
        self.assertEqual(res_prov.status_code, 403)

        res_admin = client.get("/api/v1/admin/dashboard", headers=self.customer_headers)
        self.assertEqual(res_admin.status_code, 403)
