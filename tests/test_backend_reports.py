import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import User, UserRole
from backend.security.auth import hash_password, create_access_token

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestBackendReports(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)
        
        db = TestingSessionLocal()
        self.user = User(name="HSE User", email="report_user@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, is_active=True)
        db.add(self.user)
        db.commit()
        
        self.token = create_access_token(self.user.id, self.user.email, self.user.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_create_report_and_generate_number(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        report_payload = {
            "report_type": "NEAR_MISS",
            "date": "2026-09-15",
            "site": "Digboi Refinery",
            "refinery_unit": "Hydrogen Unit",
            "equipment_id": "P-305",
            "work_type": "Preventive Maintenance",
            "department": "Operations",
            "description": "Worker entered process area without safety helmet and bypassed isolation locks.",
            "ppe_noncompliance": True,
            "maintenance_delay_or_issue": True
        }
        response = self.client.post("/api/reports", json=report_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertTrue(data["success"])
        rep = data["data"]
        self.assertTrue(rep["report_number"].startswith("OIL-"))
        self.assertEqual(rep["site"], "Digboi Refinery")
        self.assertEqual(rep["status"], "SUBMITTED")

    def test_list_and_filter_reports(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        rep1 = {
            "report_type": "NEAR_MISS", "date": "2026-09-15", "site": "Digboi Refinery",
            "description": "Worker without safety glasses near valve."
        }
        rep2 = {
            "report_type": "UNSAFE_ACT", "date": "2026-09-14", "site": "Duliajan Site",
            "description": "Lifting operation continued despite unsafe weather."
        }
        self.client.post("/api/reports", json=rep1, headers=headers)
        self.client.post("/api/reports", json=rep2, headers=headers)

        # Filter by site
        resp = self.client.get("/api/reports?site=Digboi Refinery", headers=headers)
        self.assertEqual(resp.status_code, 200)
        reports = resp.json()["data"]["reports"]
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["site"], "Digboi Refinery")

if __name__ == "__main__":
    unittest.main()
