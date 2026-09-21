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

class TestBackendReviews(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)
        
        db = TestingSessionLocal()
        self.user = User(name="User", email="user@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, is_active=True)
        self.manager = User(name="Manager", email="manager@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_MANAGER, is_active=True)
        db.add_all([self.user, self.manager])
        db.commit()

        self.report = SafetyReport(
            report_number="OIL-2026-000001",
            created_by=self.user.id,
            report_type=ReportType.NEAR_MISS,
            date="2026-09-15",
            site="Digboi Refinery",
            description="LOTO bypassed during maintenance.",
            status=ReportStatus.SUBMITTED
        )
        db.add(self.report)
        db.commit()
        db.refresh(self.report)
        self.report_id = self.report.id

        self.token_manager = create_access_token(self.manager.id, self.manager.email, self.manager.role)
        self.token_user = create_access_token(self.user.id, self.user.email, self.user.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_hse_manager_submit_review_accept(self):
        headers = {"Authorization": f"Bearer {self.token_manager}"}
        review_payload = {
            "ai_prediction_accepted": True,
            "hse_decision": "ACCEPTED",
            "review_comment": "Reviewed and validated by HSE Manager."
        }
        response = self.client.post(f"/api/reports/{self.report_id}/review", json=review_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["hse_decision"], "ACCEPTED")

        # Verify report status updated to HSE_VALIDATED
        rep_resp = self.client.get(f"/api/reports/{self.report_id}", headers=headers)
        self.assertEqual(rep_resp.json()["data"]["status"], "HSE_VALIDATED")

if __name__ == "__main__":
    unittest.main()
