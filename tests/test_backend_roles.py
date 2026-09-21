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

class TestBackendRoles(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)
        
        db = TestingSessionLocal()
        
        self.user = User(name="HSE User", email="user@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, is_active=True)
        self.manager = User(name="HSE Manager", email="manager@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_MANAGER, is_active=True)
        self.admin = User(name="Admin", email="admin@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN, is_active=True)
        
        db.add_all([self.user, self.manager, self.admin])
        db.commit()
        
        self.token_user = create_access_token(self.user.id, self.user.email, self.user.role)
        self.token_manager = create_access_token(self.manager.id, self.manager.email, self.manager.role)
        self.token_admin = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_hse_user_forbidden_from_admin_endpoints(self):
        headers = {"Authorization": f"Bearer {self.token_user}"}
        response = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_hse_user_forbidden_from_hse_review_creation(self):
        headers = {"Authorization": f"Bearer {self.token_user}"}
        review_data = {"hse_decision": "ACCEPTED", "ai_prediction_accepted": True}
        response = self.client.post("/api/reports/1/review", json=review_data, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin_endpoints(self):
        headers = {"Authorization": f"Bearer {self.token_admin}"}
        response = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 3)

if __name__ == "__main__":
    unittest.main()
