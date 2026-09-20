import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestHealthEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("JanSethu AI 2.0", data["service"])

    def test_health_v1_endpoint(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertEqual(data["service"], "JanSethu AI 2.0")

if __name__ == "__main__":
    unittest.main()
