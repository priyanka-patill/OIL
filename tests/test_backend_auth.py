import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.database.database import Base, get_db

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

class TestBackendAuth(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_signup_user_default_role(self):
        payload = {
            "name": "Test Operator",
            "email": "operator@oil.in",
            "password": "Password123!",
            "department": "Maintenance",
            "site": "Digboi Refinery"
        }
        response = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["email"], "operator@oil.in")
        self.assertEqual(data["data"]["role"], "HSE_USER") # Enforces HSE_USER

    def test_signup_duplicate_email(self):
        payload = {
            "name": "Test Operator",
            "email": "operator2@oil.in",
            "password": "Password123!"
        }
        r1 = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(r1.status_code, 201)
        
        r2 = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(r2.status_code, 409)

    def test_login_success_and_me(self):
        signup_payload = {
            "name": "Login User",
            "email": "loginuser@oil.in",
            "password": "Password123!"
        }
        self.client.post("/api/auth/signup", json=signup_payload)

        login_payload = {
            "email": "loginuser@oil.in",
            "password": "Password123!"
        }
        login_resp = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(login_resp.status_code, 200)
        
        token_data = login_resp.json()["data"]
        access_token = token_data["access_token"]
        self.assertIsNotNone(access_token)

        headers = {"Authorization": f"Bearer {access_token}"}
        me_resp = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["data"]["email"], "loginuser@oil.in")

    def test_invalid_password(self):
        signup_payload = {
            "name": "Invalid Pass User",
            "email": "badpass@oil.in",
            "password": "Password123!"
        }
        self.client.post("/api/auth/signup", json=signup_payload)

        login_payload = {
            "email": "badpass@oil.in",
            "password": "WrongPassword!"
        }
        resp = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(resp.status_code, 401)

if __name__ == "__main__":
    unittest.main()
