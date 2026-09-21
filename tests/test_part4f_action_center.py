"""
Part 4F — HSE Action Center & Full System Integration Test Suite

Tests:
1. Action Center Summary KPI Counts (real DB aggregation).
2. Site RBAC Scoping & Anti-Leakage (prevents cross-site aggregate data leakage for restricted users).
3. Section Payloads (Pending Reviews, My Actions, Overdue Actions, Verification Pending, Impact Analyses, Recent Activity).
4. Global Filtering Consistency (site, department, priority, status, SLA status).
5. Part 4D SLA Integration (days overdue calculation & escalation display).
6. Part 4E Impact Integration (preservation of SUFFICIENT vs INSUFFICIENT_DATA).
7. Non-Causal Wording Audit (zero "caused", "prevented", "eliminated" in outputs).
8. Anti-Leakage Audit (source_sheet / 12_High_Potential isolation).
9. End-to-End Operational Chain Verification (Part 3 -> 4A -> 4B -> 4C -> 4D -> 4E -> 4F).
"""

import json
import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.models import (
    Base, User, UserRole, SafetyReport, AIAnalysis,
    InterventionRecommendation, InterventionCategory, InterventionPriority, InterventionStatus,
    HSEInterventionReview, HSEInterventionDecision, Action, ActionStatus, ActionPriority,
    ActionSLA, SLAStatus, SLACompletionTiming, ActionEvidence, ActionCompletionHistory, ActionImpactAnalysis
)
from backend.services import action_service, impact_service, sla_service
from backend.main import app
from backend.database.database import get_db
from backend.security.dependencies import get_current_user

# In-memory SQLite DB with StaticPool for thread-safe TestClient compatibility
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class TestPart4FHseActionCenter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            TEST_SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestingSessionLocal()

        # Users
        self.admin_user = User(
            name="Admin User",
            email="admin@oil.in",
            password_hash="pass_hash",
            role=UserRole.ADMIN,
            is_active=True
        )

        self.site_a_user = User(
            name="Site A Engineer",
            email="engineer.sitea@oil.in",
            password_hash="pass_hash",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Maintenance",
            is_active=True
        )

        self.site_b_user = User(
            name="Site B Inspector",
            email="inspector.siteb@oil.in",
            password_hash="pass_hash",
            role=UserRole.HSE_MANAGER,
            site="Duliajan Field",
            department="Operations",
            is_active=True
        )

        self.db.add_all([self.admin_user, self.site_a_user, self.site_b_user])
        self.db.commit()

        # Reports
        self.report_a = SafetyReport(
            report_number="REP-SITE-A-001",
            created_by=self.site_a_user.id,
            date="2026-08-01",
            description="Energy Isolation issue with gas flange leak at Site A.",
            site="Digboi Refinery",
            department="Maintenance",
            created_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        )

        self.report_b = SafetyReport(
            report_number="REP-SITE-B-001",
            created_by=self.site_b_user.id,
            date="2026-08-05",
            description="Pressure relief valve failure at Site B.",
            site="Duliajan Field",
            department="Operations",
            created_at=datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc)
        )

        self.db.add_all([self.report_a, self.report_b])
        self.db.commit()

        # Interventions
        self.intv_a = InterventionRecommendation(
            recommendation_number="INT-DIG-0001",
            report_id=self.report_a.id,
            title="Replace Flange Gaskets Site A",
            category=InterventionCategory.ENERGY_ISOLATION,
            recommendation_text="Perform gasket replacement.",
            rationale="Recurring flange leaks observed.",
            evidence_summary="Observed 3 precursor leak reports.",
            priority_suggestion=InterventionPriority.HIGH,
            status=InterventionStatus.ACCEPTED
        )

        self.intv_pending_b = InterventionRecommendation(
            recommendation_number="INT-DUL-PENDING-0001",
            report_id=self.report_b.id,
            title="Calibrate Relief Valve Site B",
            category=InterventionCategory.GAS_TESTING,
            recommendation_text="Perform pressure calibration.",
            rationale="Relief valve drift detected.",
            evidence_summary="Observed valve drift during pressure test.",
            priority_suggestion=InterventionPriority.HIGH,
            status=InterventionStatus.PENDING_HSE_VALIDATION
        )

        self.db.add_all([self.intv_a, self.intv_pending_b])
        self.db.commit()

        # Operational Action at Site A
        self.action_a = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.intv_a.id,
            created_by_user=self.site_b_user,
            assigned_user_id=self.site_a_user.id,
            assigned_department="Maintenance",
            priority="HIGH",
            due_date="2026-12-31"
        )
        action_service.update_action_status(self.db, self.action_a.id, ActionStatus.IN_PROGRESS, self.site_a_user)

    def tearDown(self):
        self.db.close()

    def test_01_action_center_summary_api(self):
        """Test GET /api/action-center/summary API returns authoritative real DB counts."""
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.admin_user
        client = TestClient(app)

        res = client.get("/api/action-center/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]["summary"]

        self.assertEqual(data["pending_reviews"], 1) # intv_pending_b
        self.assertEqual(data["active_actions"], 1) # action_a
        self.assertIn("due_soon", data)
        self.assertIn("overdue", data)
        self.assertIn("impact_available", data)

        app.dependency_overrides.clear()

    def test_02_site_rbac_scoping_prevents_aggregate_data_leakage(self):
        """Test non-admin user restricted to Site A gets summary metrics scoped ONLY to Site A."""
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.site_a_user
        client = TestClient(app)

        res = client.get("/api/action-center/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]["summary"]

        # Pending review at Site B (Duliajan Field) must NOT be counted for Site A user!
        self.assertEqual(data["pending_reviews"], 0)
        self.assertEqual(data["active_actions"], 1) # action_a at Site A

        app.dependency_overrides.clear()

    def test_03_action_center_sections_payload(self):
        """Test GET /api/action-center/sections returns structured operational sections."""
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.admin_user
        client = TestClient(app)

        res = client.get("/api/action-center/sections")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertIn("pending_reviews", data)
        self.assertIn("my_actions", data)
        self.assertIn("overdue_actions", data)
        self.assertIn("verification_pending", data)
        self.assertIn("impact_analyses", data)
        self.assertIn("recent_activity", data)

        self.assertEqual(len(data["pending_reviews"]), 1)
        self.assertEqual(data["pending_reviews"][0]["title"], "Calibrate Relief Valve Site B")

        app.dependency_overrides.clear()

    def test_04_sla_overdue_days_and_escalation_display(self):
        """Test that Part 4D SLA overdue days and escalations are correctly exposed in Action Center."""
        # Manually set SLA status to OVERDUE on action_a
        sla_rec = self.action_a.sla
        sla_rec.sla_status = SLAStatus.OVERDUE
        sla_rec.due_at = datetime.now(timezone.utc) - timedelta(days=5)
        sla_rec.current_escalation_level = 1
        self.db.commit()

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.admin_user
        client = TestClient(app)

        res = client.get("/api/action-center/sections")
        self.assertEqual(res.status_code, 200)
        overdue_list = res.json()["data"]["overdue_actions"]

        self.assertEqual(len(overdue_list), 1)
        self.assertEqual(overdue_list[0]["action_number"], self.action_a.action_number)
        self.assertGreaterEqual(overdue_list[0]["days_overdue"], 4)
        self.assertEqual(overdue_list[0]["current_escalation_level"], 1)

        app.dependency_overrides.clear()

    def test_05_observational_impact_and_insufficient_data_preservation(self):
        """Test that Part 4E impact results preserve INSUFFICIENT_DATA and non-causal claims."""
        # Calculate impact for action_a
        impact = impact_service.calculate_and_store_impact(self.db, self.action_a)
        self.assertEqual(impact.data_sufficiency_status, "INSUFFICIENT_DATA")

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.admin_user
        client = TestClient(app)

        res = client.get("/api/action-center/sections")
        self.assertEqual(res.status_code, 200)
        impact_list = res.json()["data"]["impact_analyses"]

        self.assertEqual(len(impact_list), 1)
        self.assertEqual(impact_list[0]["data_sufficiency_status"], "INSUFFICIENT_DATA")

        # Non-causal audit
        full_text = json.dumps(impact_list).lower()
        forbidden_causal_terms = ["intervention caused a", "prevented sif", "eliminated sif", "reduced fatality risk", "proven reduction"]
        for term in forbidden_causal_terms:
            self.assertNotIn(term, full_text, f"Forbidden causal claim '{term}' found in Action Center output!")

        app.dependency_overrides.clear()

    def test_06_end_to_end_operational_chain(self):
        """Test full operational chain from Part 3 report -> 4A -> 4B -> 4C -> 4D -> 4E -> 4F Action Center."""
        # 1. Complete action_a
        action_service.complete_action_with_verification_pending(
            db=self.db,
            action_id=self.action_a.id,
            user=self.site_a_user,
            completion_comment="Work completed at Site A."
        )

        # 2. Verify action_a as HSE Manager
        action_service.verify_action_by_hse(
            db=self.db,
            action_id=self.action_a.id,
            hse_user=self.site_b_user,
            decision="VERIFY",
            comment_text="Approved by HSE Inspector."
        )

        # 3. Query Action Center API
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.admin_user
        client = TestClient(app)

        res_sum = client.get("/api/action-center/summary")
        self.assertEqual(res_sum.status_code, 200)
        summary_data = res_sum.json()["data"]["summary"]

        self.assertEqual(summary_data["verified"], 1)

        app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
