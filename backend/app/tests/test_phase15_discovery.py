import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.facility import Facility, Department
from app.models.enums import FacilityType
from app.repositories.facility_repository import haversine_distance_km

class TestPhase15HealthcareDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_search_facilities_by_pincode(self):
        """Test facility discovery by pincode (413106)."""
        res = self.client.get("/api/v1/facilities/search?pincode=413106")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for fac in data:
            self.assertEqual(fac["pincode"], "413106")

    def test_02_search_facilities_by_district(self):
        """Test facility discovery by district (case-insensitive 'pune')."""
        res = self.client.get("/api/v1/facilities/search?district=pune")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for fac in data:
            self.assertEqual(fac["district"].lower(), "pune")

    def test_03_search_facilities_by_village(self):
        """Test facility discovery by village (case-insensitive 'baramati')."""
        res = self.client.get("/api/v1/facilities/search?village=baramati")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for fac in data:
            self.assertIn("baramati", fac["village"].lower())

    def test_04_search_facilities_by_facility_type(self):
        """Test facility discovery by facility_type ('PHC')."""
        res = self.client.get("/api/v1/facilities/search?facility_type=PHC")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for fac in data:
            self.assertEqual(fac["facility_type"], "PHC")

    def test_05_search_facilities_by_emergency_capable(self):
        """Test facility discovery by emergency capability (emergency_capable=true)."""
        res = self.client.get("/api/v1/facilities/search?emergency_capable=true")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for fac in data:
            self.assertTrue(fac["emergency_available"])
            self.assertTrue(fac["emergency_capable"])

    def test_06_search_facilities_by_haversine_gps_distance(self):
        """Test Haversine distance calculation and sorting via GPS coordinates."""
        # Near Baramati (18.1506, 74.5772)
        res = self.client.get("/api/v1/facilities/search?latitude=18.1506&longitude=74.5772")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        # Verify distance_km is present and sorted ascending
        distances = [fac["distance_km"] for fac in data if fac.get("distance_km") is not None]
        self.assertEqual(distances, sorted(distances))
        # Nearest facility should have distance ~ 0 km
        self.assertLess(data[0]["distance_km"], 2.0)

    def test_07_search_facilities_by_gps_radius_filtering(self):
        """Test radius filtering (radius_km=5 vs radius_km=100)."""
        res_small = self.client.get("/api/v1/facilities/search?latitude=18.1506&longitude=74.5772&radius_km=5")
        res_large = self.client.get("/api/v1/facilities/search?latitude=18.1506&longitude=74.5772&radius_km=100")
        self.assertEqual(res_small.status_code, 200)
        self.assertEqual(res_large.status_code, 200)
        self.assertGreaterEqual(len(res_large.json()), len(res_small.json()))

    def test_08_search_facilities_by_combined_filters(self):
        """Test multi-parameter combined filtering (district + emergency_capable + facility_type)."""
        res = self.client.get("/api/v1/facilities/search?district=Pune&emergency_capable=true&facility_type=GOVERNMENT_HOSPITAL")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        for fac in data:
            self.assertEqual(fac["district"], "Pune")
            self.assertTrue(fac["emergency_available"])
            self.assertEqual(fac["facility_type"], "GOVERNMENT_HOSPITAL")

    def test_09_search_facilities_by_department_id(self):
        """Test filtering facilities offering a specific department_id."""
        first_dept = self.db.query(Department).first()
        self.assertIsNotNone(first_dept)
        res = self.client.get(f"/api/v1/facilities/search?department_id={first_dept.id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        fac_ids = [fac["id"] for fac in data]
        self.assertIn(first_dept.facility_id, fac_ids)

    def test_10_search_facilities_free_text_q(self):
        """Test free text search query matching name, address, village, district, or pincode."""
        res = self.client.get("/api/v1/facilities/search?q=Baramati")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)

    def test_11_search_facilities_exclude_inactive(self):
        """Test inactive facilities are excluded by default."""
        res = self.client.get("/api/v1/facilities/search")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        for fac in data:
            self.assertTrue(fac["is_active"])

    def test_12_search_facilities_include_inactive_flag(self):
        """Test inactive facilities can be included when include_inactive=true."""
        # Create a temporary inactive facility
        temp_fac = Facility(
            name="Inactive Test PHC",
            facility_type=FacilityType.PHC,
            description="Inactive facility for testing",
            address="Test address",
            village="Test",
            district="Test",
            state="Maharashtra",
            pincode="999999",
            phone_number="+91-9999999999",
            is_active=False
        )
        self.db.add(temp_fac)
        self.db.commit()

        try:
            res_default = self.client.get("/api/v1/facilities/search?pincode=999999")
            res_inactive = self.client.get("/api/v1/facilities/search?pincode=999999&include_inactive=true")
            self.assertEqual(len(res_default.json()), 0)
            self.assertEqual(len(res_inactive.json()), 1)
        finally:
            self.db.delete(temp_fac)
            self.db.commit()

    def test_13_search_facilities_case_insensitive_matching(self):
        """Test case-insensitivity across search parameters."""
        res_lower = self.client.get("/api/v1/facilities/search?district=pune")
        res_upper = self.client.get("/api/v1/facilities/search?district=PUNE")
        self.assertEqual(res_lower.status_code, 200)
        self.assertEqual(res_upper.status_code, 200)
        self.assertEqual(len(res_lower.json()), len(res_upper.json()))

    def test_14_search_facilities_empty_query_returns_all_active(self):
        """Test empty search query returns all active facilities in DB."""
        res = self.client.get("/api/v1/facilities/search")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        active_count = self.db.query(Facility).filter(Facility.is_active == True).count()
        self.assertEqual(len(data), active_count)

    def test_15_search_facilities_invalid_lat_returns_400(self):
        """Test latitude validation failure (> 90 degrees) returns 400 Bad Request."""
        res = self.client.get("/api/v1/facilities/search?latitude=105.0&longitude=74.5")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Latitude must be between", res.json()["detail"])

    def test_16_search_facilities_invalid_lng_returns_400(self):
        """Test longitude validation failure (> 180 degrees) returns 400 Bad Request."""
        res = self.client.get("/api/v1/facilities/search?latitude=18.5&longitude=200.0")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Longitude must be between", res.json()["detail"])

    def test_17_search_facilities_invalid_radius_returns_400(self):
        """Test radius validation failure (<= 0 km) returns 400 Bad Request."""
        res = self.client.get("/api/v1/facilities/search?latitude=18.5&longitude=74.5&radius_km=-5.0")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Search radius must be greater than 0", res.json()["detail"])

    def test_18_search_facilities_public_access_no_auth(self):
        """Test healthcare discovery endpoint is publicly accessible without JWT token."""
        res = self.client.get("/api/v1/facilities/search")
        self.assertEqual(res.status_code, 200)

    def test_19_department_discovery_for_facility(self):
        """Test department discovery for a specific facility."""
        fac = self.db.query(Facility).filter(Facility.is_active == True).first()
        res = self.client.get(f"/api/v1/facilities/{fac.id}/departments")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_20_doctor_discovery_in_facility(self):
        """Test doctor discovery within a facility."""
        fac = self.db.query(Facility).filter(Facility.is_active == True).first()
        res = self.client.get(f"/api/v1/doctors?facility_id={fac.id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_21_healthcare_alias_endpoint(self):
        """Test /api/v1/healthcare/search alias route."""
        res = self.client.get("/api/v1/healthcare/search?pincode=413106")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)

    def test_22_haversine_distance_calculation_accuracy(self):
        """Test Haversine distance mathematical formula accuracy directly."""
        # Pune (18.5204, 73.8567) to Baramati (18.1506, 74.5772) is approx 86 km
        dist = haversine_distance_km(18.5204, 73.8567, 18.1506, 74.5772)
        self.assertGreater(dist, 80.0)
        self.assertLess(dist, 95.0)

if __name__ == "__main__":
    unittest.main()
