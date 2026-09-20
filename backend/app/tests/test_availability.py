import unittest
from datetime import date, time, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models import Facility, Doctor, Appointment, DoctorScheduleException, Department
from app.services.availability_service import AvailabilityService
from app.utils.timezone import get_today_ist

from scripts.seed import seed_database

class TestPhase3AvailabilityAndDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_facility_discovery_filtering(self):
        """Test facility search by pincode, district, and village."""
        # Pincode search
        res = self.client.get("/api/v1/facilities/?pincode=413106")
        self.assertEqual(res.status_code, 200)
        facs = res.json()
        self.assertGreaterEqual(len(facs), 1)
        self.assertTrue(any(f["name"] == "Government Sub-District Hospital, Baramati" for f in facs))

        # District search
        dist_res = self.client.get("/api/v1/facilities/?district=Pune")
        self.assertEqual(dist_res.status_code, 200)
        self.assertGreaterEqual(len(dist_res.json()), 3)

    def test_haversine_nearby_facility_search(self):
        """Test coordinate-based nearby search with Haversine distance calculation."""
        # Exact Baramati coordinates
        res = self.client.get("/api/v1/facilities/nearby?latitude=18.1506&longitude=74.5772&radius_km=15")
        self.assertEqual(res.status_code, 200)
        facs = res.json()
        self.assertGreater(len(facs), 0)
        top_fac = facs[0]
        self.assertEqual(top_fac["name"], "Government Sub-District Hospital, Baramati")
        self.assertEqual(top_fac["distance_km"], 0.0)

    def test_dynamic_slot_generation_with_bookings_and_exceptions(self):
        """
        Tests slot generation on 2026-10-25:
        - 09:00 - 09:30 must be BOOKED (from TKN-SEED101)
        - 10:00 - 11:30 must be BLOCKED (from Dr. Sharma Emergency Duty exception)
        - 09:30 - 10:00 must be AVAILABLE
        """
        res = self.client.get("/api/v1/doctors/1/availability?date=2026-10-25")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["doctor_id"], 1)
        self.assertEqual(data["timezone"], "Asia/Kolkata")
        slots = data["slots"]
        self.assertGreater(len(slots), 0)

        # Slot 09:00 - 09:30 -> BOOKED
        slot_9_00 = next(s for s in slots if s["start_time"] == "09:00")
        self.assertEqual(slot_9_00["status"], "BOOKED")

        # Slot 09:30 - 10:00 -> AVAILABLE
        slot_9_30 = next(s for s in slots if s["start_time"] == "09:30")
        self.assertEqual(slot_9_30["status"], "AVAILABLE")

        # Slot 10:00 - 10:30 -> BLOCKED
        slot_10_00 = next(s for s in slots if s["start_time"] == "10:00")
        self.assertEqual(slot_10_00["status"], "BLOCKED")
        self.assertIn("Emergency Casualty", slot_10_00["reason"])

    def test_past_date_slot_protection(self):
        """Verify that requesting availability for a past date marks all slots as PAST."""
        yesterday = get_today_ist() - timedelta(days=1)
        res = self.client.get(f"/api/v1/doctors/1/availability?date={yesterday}")
        self.assertEqual(res.status_code, 200)
        slots = res.json()["slots"]
        for s in slots:
            self.assertEqual(s["status"], "PAST")

    def test_booking_precheck_service(self):
        """Test reusable check_slot_availability service."""
        doc = self.db.query(Doctor).first()
        fac = self.db.query(Facility).first()
        dept = self.db.query(Department).filter(Department.id == doc.department_id).first()

        # Check available slot
        ok, msg = AvailabilityService.check_slot_availability(
            self.db,
            doctor_id=doc.id,
            facility_id=fac.id,
            department_id=dept.id,
            target_date=date(2026, 10, 25),
            start_time=time(9, 30),
            end_time=time(10, 0)
        )
        self.assertTrue(ok)
        self.assertIn("available", msg)

        # Check booked slot
        ok_booked, msg_booked = AvailabilityService.check_slot_availability(
            self.db,
            doctor_id=doc.id,
            facility_id=fac.id,
            department_id=dept.id,
            target_date=date(2026, 10, 25),
            start_time=time(9, 0),
            end_time=time(9, 30)
        )
        self.assertFalse(ok_booked)
        self.assertIn("already booked", msg_booked)

    def test_admin_add_schedule_exception(self):
        """Verify Admin can add a new DoctorScheduleException."""
        admin_login = self.client.post("/api/v1/auth/login", json={"phone_number": "+91-9900000001", "password": "AdminPass123!"})
        admin_token = admin_login.json()["access_token"]

        exc_payload = {
            "date": "2026-11-15",
            "start_time": "11:00:00",
            "end_time": "13:00:00",
            "reason": "Attending Healthcare Conference",
            "is_active": True
        }

        res = self.client.post(
            "/api/v1/doctors/1/exceptions",
            json=exc_payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["reason"], "Attending Healthcare Conference")

if __name__ == "__main__":
    unittest.main()
