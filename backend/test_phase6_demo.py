import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

class TestPhase6Demo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_emergency_demo_phrase(self):
        """Test exact prompt: 'Mere papa ko saans lene mein bahut dikkat ho rahi hai.'"""
        res = self.client.post("/api/voice/intent", json={
            "transcript": "Mere papa ko saans lene mein bahut dikkat ho rahi hai.",
            "lang": "hi"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_emergency"])
        self.assertEqual(data["intent"], "emergency_help")
        self.assertEqual(data["action"], "navigate_emergency")
        self.assertIn("108", data["response_text"])
        self.assertIn("108", data["response_text_hi"])
        self.assertIn("१०८", data["response_text_mr"])

    def test_02_marathi_voice_demo(self):
        """Test Marathi request 'मला डॉक्टरांना भेटायचे आहे.'"""
        res = self.client.post("/api/voice/intent", json={
            "transcript": "मला डॉक्टरांना भेटायचे आहे.",
            "lang": "mr"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "appointment_request")
        self.assertIn("बारामती", data["response_text_mr"])

    def test_03_rural_hindi_patient_demo(self):
        """Test Hindi rural patient request 'mujhe baramati me bukhar ke liye doctor dikhana hai'"""
        res = self.client.post("/api/voice/intent", json={
            "transcript": "mujhe baramati me bukhar ke liye doctor dikhana hai",
            "lang": "hi"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "appointment_request")
        self.assertEqual(data["action"], "navigate_slots")
        self.assertGreaterEqual(len(data["facilities"]), 1)

if __name__ == "__main__":
    unittest.main()
