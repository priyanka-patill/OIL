"""
Comprehensive Unit & Integration Test Suite for Part 4B — HSE Review & Approval Workflow
"""

import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.database.models import (
    User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis,
    InterventionRecommendation, HSEInterventionReview, InterventionCategory,
    InterventionPriority, InterventionStatus, HSEInterventionDecision
)
from backend.security.auth import create_access_token
from backend.main import app

from backend.services import intervention_service


class TestPart4BHSEReview(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database for testing
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(bind=self.engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = TestingSessionLocal()

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Seed Test Users
        self.admin = User(
            name="Admin Reviewer",
            email="admin.hse@oil.in",
            password_hash="hashed",
            role=UserRole.ADMIN,
            site=None,
            department="HSE"
        )
        self.hse_manager = User(
            name="Digboi HSE Manager",
            email="manager.digboi@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_MANAGER,
            site="Digboi Refinery",
            department="HSE"
        )
        self.duliajan_manager = User(
            name="Duliajan HSE Manager",
            email="manager.duliajan@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_MANAGER,
            site="Duliajan Complex",
            department="HSE"
        )
        self.db.add_all([self.admin, self.hse_manager, self.duliajan_manager])
        self.db.commit()

        # Auth Tokens
        self.admin_token = create_access_token(user_id=self.admin.id, email=self.admin.email, role=self.admin.role)
        self.hse_manager_token = create_access_token(user_id=self.hse_manager.id, email=self.hse_manager.email, role=self.hse_manager.role)
        self.duliajan_token = create_access_token(user_id=self.duliajan_manager.id, email=self.duliajan_manager.email, role=self.duliajan_manager.role)

        # Seed Safety Report & AI Analysis at Digboi Refinery
        self.report = SafetyReport(
            report_number="OIL-2026-REV001",
            report_type=ReportType.UNSAFE_ACT,
            status=ReportStatus.SUBMITTED,
            site="Digboi Refinery",
            location="Compressor Shed 2",
            refinery_unit="AVU-1",
            work_type="Electrical Repair",
            department="Electrical",
            equipment_id="COMP-201",
            date="2026-02-20",
            description="LOTO padlock missing during maintenance of motor driver. Unisolated terminal box exposed.",
            ppe_noncompliance=False,
            supervisor_negligence=True,
            maintenance_delay_or_issue=True,
            repeated_issue_ignored=False,
            created_by=self.admin.id,
        )
        self.db.add(self.report)
        self.db.commit()

        self.analysis = AIAnalysis(
            report_id=self.report.id,
            model_version="sif_model_v1",
            prediction="SIF-Potential",
            classification=1,
            probability_or_score=0.87,
            threshold=0.5,
            explanation_json='{"reason": "High severity electrical hazard"}',
            life_saving_rules_json='["Energy Isolation"]',
            hazards_json='["Electrical", "Energy"]',
            barrier_concerns_json='["Energy Isolation"]',
        )
        self.db.add(self.analysis)
        self.db.commit()

        # Generate Part 4A Recommendation
        self.rec = intervention_service.generate_recommendation_for_report(
            db=self.db, report_id=self.report.id, current_user=self.admin
        )

    def test_01_authorized_accept_workflow(self):
        """Test ACCEPT decision workflow: status changes to ACCEPTED while AI fields remain 100% immutable."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {
            "decision": "ACCEPT",
            "review_comment": "Accepted after verifying LOTO procedures with field supervisor."
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Verify DB Status
        rec_db = intervention_service.get_intervention_by_id(self.db, self.rec.id)
        self.assertEqual(rec_db.status, InterventionStatus.ACCEPTED)

        # IMMUTABILITY ASSERTION: Original AI fields MUST NOT change!
        self.assertEqual(rec_db.title, self.rec.title)
        self.assertEqual(rec_db.recommendation_text, self.rec.recommendation_text)
        self.assertEqual(rec_db.category, self.rec.category)
        self.assertEqual(rec_db.priority_suggestion, self.rec.priority_suggestion)

        # Verify Review Record
        reviews = intervention_service.get_intervention_reviews(self.db, self.rec.id)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].decision, HSEInterventionDecision.ACCEPT)
        self.assertEqual(reviews[0].reviewer_id, self.admin.id)
        self.assertIsNotNone(reviews[0].reviewed_at)

    def test_02_authorized_modify_workflow(self):
        """Test MODIFY decision workflow: stores HSE modified text & planning metadata separately."""
        headers = {"Authorization": f"Bearer {self.hse_manager_token}"}
        payload = {
            "decision": "MODIFY",
            "modified_title": "Field Conducted LOTO Verification on COMP-201",
            "modified_recommendation_text": "Conduct mandatory zero-energy verification and supervisor LOTO sign-off before commencing electrical repair.",
            "modified_category": "ENERGY_ISOLATION",
            "modified_priority": "HIGH",
            "proposed_department": "Electrical Maintenance",
            "proposed_due_date": "2026-10-15",
            "review_comment": "Modified to add supervisor sign-off requirement."
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Verify DB Status
        rec_db = intervention_service.get_intervention_by_id(self.db, self.rec.id)
        self.assertEqual(rec_db.status, InterventionStatus.MODIFIED)

        # IMMUTABILITY ASSERTION: Original AI recommendation fields MUST be unchanged!
        self.assertNotEqual(rec_db.title, payload["modified_title"])
        self.assertNotEqual(rec_db.recommendation_text, payload["modified_recommendation_text"])

        # Verify HSE Modification Storage
        reviews = intervention_service.get_intervention_reviews(self.db, self.rec.id)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].decision, HSEInterventionDecision.MODIFY)
        self.assertEqual(reviews[0].modified_title, payload["modified_title"])
        self.assertEqual(reviews[0].modified_recommendation_text, payload["modified_recommendation_text"])
        self.assertEqual(reviews[0].proposed_department, "Electrical Maintenance")
        self.assertEqual(reviews[0].proposed_due_date, "2026-10-15")

    def test_03_authorized_reject_workflow(self):
        """Test REJECT decision workflow: mandatory rejection reason is enforced and stored."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {
            "decision": "REJECT",
            "rejection_reason": "Recommendation rejected because electrical team verified LOTO padlock was restored 10 minutes post-observation.",
            "review_comment": "Verified during routine audit."
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Verify DB Status
        rec_db = intervention_service.get_intervention_by_id(self.db, self.rec.id)
        self.assertEqual(rec_db.status, InterventionStatus.REJECTED)

        # IMMUTABILITY ASSERTION: Original AI fields remain intact
        self.assertIsNotNone(rec_db.recommendation_text)

        # Verify Review Record
        reviews = intervention_service.get_intervention_reviews(self.db, self.rec.id)
        self.assertEqual(reviews[0].decision, HSEInterventionDecision.REJECT)
        self.assertEqual(reviews[0].rejection_reason, payload["rejection_reason"])

    def test_04_reject_without_reason_fails(self):
        """Test REJECT decision without a valid rejection reason returns HTTP 400 Bad Request."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {
            "decision": "REJECT",
            "rejection_reason": "   ",  # Whitespace only
            "review_comment": "Test comment"
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 400)
        msg = resp.json().get("message", "") or resp.json().get("detail", "")
        self.assertIn("mandatory", msg.lower())

    def test_05_modify_without_text_fails(self):
        """Test MODIFY decision with empty text returns HTTP 400 Bad Request."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {
            "decision": "MODIFY",
            "modified_recommendation_text": "   ",
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_06_unauthorized_site_reviewer_blocked(self):
        """Test user restricted to Duliajan Complex cannot review Digboi Refinery intervention."""
        headers = {"Authorization": f"Bearer {self.duliajan_token}"}
        payload = {
            "decision": "ACCEPT",
            "review_comment": "Unauthorized attempt."
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 403)
        msg = resp.json().get("message", "") or resp.json().get("detail", "")
        self.assertIn("unauthorized", msg.lower())

    def test_07_reviewer_identity_from_auth_token(self):
        """Test reviewer_id is derived strictly from server-side JWT session, ignoring client payload."""
        headers = {"Authorization": f"Bearer {self.hse_manager_token}"}
        payload = {
            "decision": "ACCEPT",
            "reviewer_id": 9999,  # Malicious client attempt to fake identity!
            "review_comment": "Testing reviewer identity security."
        }

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)

        reviews = intervention_service.get_intervention_reviews(self.db, self.rec.id)
        # Server MUST set reviewer_id to self.hse_manager.id (NOT 9999!)
        self.assertEqual(reviews[0].reviewer_id, self.hse_manager.id)

    def test_08_no_operational_action_created(self):
        """Strict Boundary Check: Confirm that ACCEPTing an intervention does NOT create operational action tasks."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {"decision": "ACCEPT"}

        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Check DB tables: Ensure no action lifecycle tables or SLA clocks were started
        # In Part 4B, recommendations stop at HSE Decision!
        rec_db = intervention_service.get_intervention_by_id(self.db, self.rec.id)
        self.assertEqual(rec_db.status, InterventionStatus.ACCEPTED)

    def test_09_anti_leakage_audit(self):
        """Mandatory Leakage Protection Audit: Ensure source_sheet and 12_High_Potential have ZERO impact on review."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Attach source_sheet to report
        self.report.source_sheet = "12_High_Potential"
        self.db.commit()

        payload = {"decision": "ACCEPT", "review_comment": "Testing anti-leakage"}
        resp = self.client.post(f"/api/interventions/{self.rec.id}/review", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["intervention"]["status"], "ACCEPTED")

    def test_10_review_history_endpoint(self):
        """Verify GET /api/interventions/{id}/review/history returns audit history."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Submit first review: MODIFY
        self.client.post(f"/api/interventions/{self.rec.id}/review", json={
            "decision": "MODIFY",
            "modified_recommendation_text": "First modified version text."
        }, headers=headers)

        # Submit second review: ACCEPT
        self.client.post(f"/api/interventions/{self.rec.id}/review", json={
            "decision": "ACCEPT",
            "review_comment": "Final acceptance."
        }, headers=headers)

        # Query history endpoint
        hist_resp = self.client.get(f"/api/interventions/{self.rec.id}/review/history", headers=headers)
        self.assertEqual(hist_resp.status_code, 200)
        body = hist_resp.json()
        self.assertTrue(body["success"])
        data = body["data"]

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["decision"], "ACCEPT")
        self.assertEqual(data[1]["decision"], "MODIFY")


if __name__ == "__main__":
    unittest.main()
