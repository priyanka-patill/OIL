import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus
from backend.security.auth import hash_password, create_access_token

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestFrontendIntegration(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)

        db = TestingSessionLocal()
        self.user = User(name="Frontend User", email="frontend_user@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, is_active=True)
        self.manager = User(name="Frontend Manager", email="frontend_mgr@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_MANAGER, is_active=True)
        self.admin = User(name="Frontend Admin", email="frontend_admin@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN, is_active=True)
        db.add_all([self.user, self.manager, self.admin])
        db.commit()

        self.token_user = create_access_token(self.user.id, self.user.email, self.user.role)
        self.token_manager = create_access_token(self.manager.id, self.manager.email, self.manager.role)
        self.token_admin = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_frontend_login_flow(self):
        login_resp = self.client.post("/api/auth/login", json={"email": "frontend_user@oil.in", "password": "Pass123!"})
        self.assertEqual(login_resp.status_code, 200)
        data = login_resp.json()
        self.assertTrue(data["success"])
        self.assertIn("access_token", data["data"])
        self.assertEqual(data["data"]["user"]["role"], "HSE_USER")

    def test_frontend_dashboard_and_report_flow(self):
        headers = {"Authorization": f"Bearer {self.token_user}"}
        
        # 1. Create Report from Form
        report_payload = {
            "report_type": "NEAR_MISS",
            "date": "2026-09-16",
            "site": "Digboi Refinery",
            "refinery_unit": "Hydrogen Unit",
            "location": "Pump Area 3",
            "equipment_id": "P-305",
            "work_type": "Preventive Maintenance",
            "activity": "Pump Overhaul",
            "department": "Operations",
            "description": "Worker entered pump pit without safety harness or isolation locks.",
            "ppe_noncompliance": True,
            "supervisor_negligence": False,
            "maintenance_delay_or_issue": True,
            "repeated_issue_ignored": False,
            "previous_similar_reports": 2
        }
        create_resp = self.client.post("/api/reports", json=report_payload, headers=headers)
        self.assertEqual(create_resp.status_code, 201)
        rep_data = create_resp.json()["data"]
        rep_id = rep_data["id"]

        # 2. Query Dashboard List
        list_resp = self.client.get("/api/reports?page=1&limit=10", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        reports = list_resp.json()["data"]["reports"]
        self.assertEqual(len(reports), 1)

        # 3. Query Single Report Details
        detail_resp = self.client.get(f"/api/reports/{rep_id}", headers=headers)
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["data"]["report_number"], rep_data["report_number"])

    def test_frontend_manager_review_flow(self):
        headers_user = {"Authorization": f"Bearer {self.token_user}"}
        headers_mgr = {"Authorization": f"Bearer {self.token_manager}"}

        # 1. User submits report
        create_resp = self.client.post("/api/reports", json={
            "report_type": "UNSAFE_ACT", "date": "2026-09-16", "site": "Duliajan Site",
            "description": "Scaffolding erected without toe boards or safety mesh."
        }, headers=headers_user)
        rep_id = create_resp.json()["data"]["id"]

        # 2. Manager reviews report
        review_resp = self.client.post(f"/api/reports/{rep_id}/review", json={
            "ai_prediction_accepted": True,
            "hse_decision": "ACCEPTED",
            "review_comment": "Validated by HSE Manager."
        }, headers=headers_mgr)
        self.assertEqual(review_resp.status_code, 201)

        # 3. Verify status updated to HSE_VALIDATED
        detail_resp = self.client.get(f"/api/reports/{rep_id}", headers=headers_mgr)
        self.assertEqual(detail_resp.json()["data"]["status"], "HSE_VALIDATED")

if __name__ == "__main__":
    unittest.main()
