import os
import io
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportAttachment
from backend.security.auth import hash_password, create_access_token

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestAttachmentSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = TestingSessionLocal()
        cls.client = TestClient(app)

        # Seed Test Users
        cls.user1 = User(
            name="Regular Operator",
            email="operator1@oil.in",
            password_hash=hash_password("password123"),
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Operations"
        )
        cls.user2 = User(
            name="Other Operator",
            email="operator2@oil.in",
            password_hash=hash_password("password123"),
            role=UserRole.HSE_USER,
            site="Duliajan Field",
            department="Maintenance"
        )
        cls.admin = User(
            name="HSE Admin Manager",
            email="admin@oil.in",
            password_hash=hash_password("password123"),
            role=UserRole.ADMIN,
            site="Digboi Refinery",
            department="Safety"
        )
        cls.db.add_all([cls.user1, cls.user2, cls.admin])
        cls.db.commit()

        # Auth tokens
        cls.token_user1 = create_access_token(cls.user1.id, cls.user1.email, cls.user1.role)
        cls.token_user2 = create_access_token(cls.user2.id, cls.user2.email, cls.user2.role)
        cls.token_admin = create_access_token(cls.admin.id, cls.admin.email, cls.admin.role)

    def setUp(self):
        def override_get_db():
            try:
                yield self.db
            finally:
                pass
        app.dependency_overrides[get_db] = override_get_db

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_01_create_report_without_attachments(self):
        """Report creation with 0 attachments should succeed cleanly."""
        headers = {"Authorization": f"Bearer {self.token_user1}"}
        payload = {
            "report_type": "NEAR_MISS",
            "date": "2026-09-18",
            "site": "Digboi Refinery",
            "refinery_unit": "Hydrogen Unit",
            "location": "Block-1",
            "equipment_id": "P-101",
            "work_type": "Overhaul",
            "activity": "Gasket change",
            "department": "Operations",
            "description": "Observed minor leak during flange alignment near Pump P-101."
        }
        res = self.client.post("/api/reports", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()["data"]
        self.assertIn("id", data)
        self.assertEqual(data["attachments"], [])

    def test_02_upload_valid_attachments(self):
        """Uploading valid JPG, PNG, and PDF attachments to an existing report."""
        headers = {"Authorization": f"Bearer {self.token_user1}"}

        # Create report first
        payload = {
            "report_type": "UNSAFE_CONDITION",
            "date": "2026-09-18",
            "site": "Digboi Refinery",
            "description": "Corroded pipe support structure found near Hydrocracker Unit."
        }
        rep_res = self.client.post("/api/reports", json=payload, headers=headers)
        report_id = rep_res.json()["data"]["id"]

        # Create dummy file bytes
        jpg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

        files = [
            ("files", ("pipe_condition.jpg", io.BytesIO(jpg_bytes), "image/jpeg")),
            ("files", ("work_permit.pdf", io.BytesIO(pdf_bytes), "application/pdf")),
        ]

        att_res = self.client.post(f"/api/reports/{report_id}/attachments", files=files, headers=headers)
        self.assertEqual(att_res.status_code, 201)
        atts = att_res.json()["data"]
        self.assertEqual(len(atts), 2)
        self.assertEqual(atts[0]["original_filename"], "pipe_condition.jpg")
        self.assertEqual(atts[1]["original_filename"], "work_permit.pdf")

        # Verify report details includes attachments
        detail_res = self.client.get(f"/api/reports/{report_id}", headers=headers)
        self.assertEqual(detail_res.status_code, 200)
        report_data = detail_res.json()["data"]
        self.assertEqual(len(report_data["attachments"]), 2)

    def test_03_reject_forbidden_executable(self):
        """Security: Executable extensions (.exe, .sh, .py) must be strictly rejected."""
        headers = {"Authorization": f"Bearer {self.token_user1}"}

        payload = {"report_type": "NEAR_MISS", "date": "2026-09-18", "site": "Digboi Refinery", "description": "Test report for security check."}
        rep_res = self.client.post("/api/reports", json=payload, headers=headers)
        report_id = rep_res.json()["data"]["id"]

        files = [("files", ("malicious_script.sh", io.BytesIO(b"#!/bin/bash\necho hack"), "text/x-shellscript"))]
        att_res = self.client.post(f"/api/reports/{report_id}/attachments", files=files, headers=headers)
        self.assertEqual(att_res.status_code, 400)
        self.assertIn("Security Violation", att_res.json()["message"])

    def test_04_reject_oversized_file(self):
        """Oversized files exceeding 10MB limit must be rejected."""
        headers = {"Authorization": f"Bearer {self.token_user1}"}

        payload = {"report_type": "NEAR_MISS", "date": "2026-09-18", "site": "Digboi Refinery", "description": "Test report for size check."}
        rep_res = self.client.post("/api/reports", json=payload, headers=headers)
        report_id = rep_res.json()["data"]["id"]

        # Create dummy file > 10MB
        large_data = b"0" * (10 * 1024 * 1024 + 100)
        files = [("files", ("huge_file.pdf", io.BytesIO(large_data), "application/pdf"))]

        att_res = self.client.post(f"/api/reports/{report_id}/attachments", files=files, headers=headers)
        self.assertEqual(att_res.status_code, 400)
        self.assertIn("exceeds maximum allowed size", att_res.json()["message"])

    def test_05_download_and_preview_attachment(self):
        """Authorized users can download and preview report attachments."""
        headers = {"Authorization": f"Bearer {self.token_user1}"}

        payload = {"report_type": "NEAR_MISS", "date": "2026-09-18", "site": "Digboi Refinery", "description": "Test report for download check."}
        rep_res = self.client.post("/api/reports", json=payload, headers=headers)
        report_id = rep_res.json()["data"]["id"]

        jpg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
        files = [("files", ("photo.jpg", io.BytesIO(jpg_bytes), "image/jpeg"))]
        att_res = self.client.post(f"/api/reports/{report_id}/attachments", files=files, headers=headers)
        att_id = att_res.json()["data"][0]["id"]

        # Test Download
        dl_res = self.client.get(f"/api/attachments/{att_id}/download", headers=headers)
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.headers["content-disposition"], 'attachment; filename="photo.jpg"')

        # Test Preview
        prev_res = self.client.get(f"/api/attachments/{att_id}/preview", headers=headers)
        self.assertEqual(prev_res.status_code, 200)
        self.assertTrue(prev_res.headers["content-disposition"].startswith("inline"))

    def test_06_unauthorized_user_access_denied(self):
        """User2 attempting to access User1's private report attachment must be denied (403 Forbidden)."""
        headers_u1 = {"Authorization": f"Bearer {self.token_user1}"}
        headers_u2 = {"Authorization": f"Bearer {self.token_user2}"}

        payload = {"report_type": "NEAR_MISS", "date": "2026-09-18", "site": "Digboi Refinery", "description": "Private report by user 1."}
        rep_res = self.client.post("/api/reports", json=payload, headers=headers_u1)
        report_id = rep_res.json()["data"]["id"]

        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        files = [("files", ("private_permit.pdf", io.BytesIO(pdf_bytes), "application/pdf"))]
        att_res = self.client.post(f"/api/reports/{report_id}/attachments", files=files, headers=headers_u1)
        att_id = att_res.json()["data"][0]["id"]

        # User2 tries to download User1's attachment
        dl_res = self.client.get(f"/api/attachments/{att_id}/download", headers=headers_u2)
        self.assertEqual(dl_res.status_code, 403)

    def test_07_delete_attachment(self):
        """Creator can delete their attachment."""
        headers = {"Authorization": f"Bearer {self.token_user1}"}

        payload = {"report_type": "NEAR_MISS", "date": "2026-09-18", "site": "Digboi Refinery", "description": "Test report for deletion."}
        rep_res = self.client.post("/api/reports", json=payload, headers=headers)
        report_id = rep_res.json()["data"]["id"]

        jpg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
        files = [("files", ("temp_photo.jpg", io.BytesIO(jpg_bytes), "image/jpeg"))]
        att_res = self.client.post(f"/api/reports/{report_id}/attachments", files=files, headers=headers)
        att_id = att_res.json()["data"][0]["id"]

        # Delete attachment
        del_res = self.client.delete(f"/api/attachments/{att_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Verify attachment is gone
        list_res = self.client.get(f"/api/reports/{report_id}/attachments", headers=headers)
        self.assertEqual(len(list_res.json()["data"]), 0)

if __name__ == "__main__":
    unittest.main()
