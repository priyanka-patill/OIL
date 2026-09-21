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
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestBackendAudit(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)
        
        db = TestingSessionLocal()
        self.admin = User(name="Admin", email="admin_audit@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN, is_active=True)
        db.add(self.admin)
        db.commit()

        self.token_admin = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_report_creation_generates_audit_log(self):
        headers = {"Authorization": f"Bearer {self.token_admin}"}
        
        # 1. Create a report
        rep = {
            "report_type": "NEAR_MISS", "date": "2026-09-15", "site": "Digboi Refinery",
            "description": "Worker without safety glasses near valve."
        }
        self.client.post("/api/reports", json=rep, headers=headers)

        # 2. Query audit logs as Admin
        audit_resp = self.client.get("/api/admin/audit-logs", headers=headers)
        self.assertEqual(audit_resp.status_code, 200)
        
        logs = audit_resp.json()["data"]["logs"]
        actions = [l["action"] for l in logs]
        self.assertIn("REPORT_CREATED", actions)

if __name__ == "__main__":
    unittest.main()
