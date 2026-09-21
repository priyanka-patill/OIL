import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestBackendHealth(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "healthy")
        self.assertIn("environment", data)

if __name__ == "__main__":
    unittest.main()
