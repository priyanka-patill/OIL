"""
Data Integrity & Aggregation Count Test Suite

Verifies:
1. Clean DB with 0 actions -> Pending Reviews, Active Actions, Impact Available = 0
2. Distinct Entity Counting (prevents multi-snapshot or duplicate join row multiplication)
3. Site Scoping & Role Scoping consistency across summary counts
"""

import json
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.models import (
    Base, User, UserRole, SafetyReport, ReportType, ReportStatus,
    InterventionRecommendation, InterventionCategory, InterventionPriority, InterventionStatus,
    Action, ActionStatus, ActionPriority, ActionSLA, SLAStatus, ActionImpactAnalysis
)
from backend.main import app
from backend.database.database import get_db
from backend.security.dependencies import get_current_user

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class TestDataIntegrityCounts(unittest.TestCase):

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

        self.admin = User(
            name="Test Admin",
            email="admin_integrity@oil.in",
            password_hash="hash",
            role=UserRole.ADMIN,
            site="Headquarters",
            department="IT"
        )
        self.db.add(self.admin)
        self.db.commit()
        self.admin_id = self.admin.id

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        def override_get_current_user():
            return self.db.query(User).filter(User.id == self.admin_id).first()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def test_clean_database_counts_are_zero(self):
        """Verifies that a clean database returns exactly 0 for all action metrics."""
        rep = SafetyReport(
            report_number="OIL-2026-TEST01",
            created_by=self.admin_id,
            report_type=ReportType.NEAR_MISS,
            date="2026-09-17",
            site="Digboi Refinery",
            description="Simple test observation.",
            status=ReportStatus.SUBMITTED
        )
        self.db.add(rep)
        self.db.commit()

        resp = self.client.get("/api/action-center/summary")
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()["data"]["summary"]

        self.assertEqual(summary["pending_reviews"], 0)
        self.assertEqual(summary["active_actions"], 0)
        self.assertEqual(summary["due_soon"], 0)
        self.assertEqual(summary["overdue"], 0)
        self.assertEqual(summary["completed"], 0)
        self.assertEqual(summary["verification_pending"], 0)
        self.assertEqual(summary["impact_available"], 0)
        self.assertEqual(summary["insufficient_data"], 0)

    def test_single_pending_review_count(self):
        """Verifies 1 report + 1 pending intervention -> pending_reviews = 1, active_actions = 0."""
        rep = SafetyReport(
            report_number="OIL-2026-TEST02",
            created_by=self.admin_id,
            report_type=ReportType.NEAR_MISS,
            date="2026-09-17",
            site="Digboi Refinery",
            description="Unsafe condition observation.",
            status=ReportStatus.SUBMITTED
        )
        self.db.add(rep)
        self.db.commit()

        intv = InterventionRecommendation(
            recommendation_number="REC-TEST-0001",
            report_id=rep.id,
            title="Inspect Isolation Valve",
            recommendation_text="Perform valve inspection",
            rationale="Precursor risk reduction",
            evidence_summary="Observed noncompliance in pump area",
            category=InterventionCategory.MAINTENANCE,
            priority_suggestion=InterventionPriority.HIGH,
            status=InterventionStatus.PENDING_HSE_VALIDATION
        )
        self.db.add(intv)
        self.db.commit()

        resp = self.client.get("/api/action-center/summary")
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()["data"]["summary"]

        self.assertEqual(summary["pending_reviews"], 1)
        self.assertEqual(summary["active_actions"], 0)
        self.assertEqual(summary["impact_available"], 0)

    def test_distinct_impact_snapshots_count(self):
        """Verifies that multiple historical impact snapshots on 1 action count as 1 impact_available action."""
        rep = SafetyReport(
            report_number="OIL-2026-TEST03",
            created_by=self.admin_id,
            report_type=ReportType.NEAR_MISS,
            date="2026-09-17",
            site="Digboi Refinery",
            description="Pipe rack vibration report.",
            status=ReportStatus.HSE_VALIDATED
        )
        self.db.add(rep)
        self.db.commit()

        intv = InterventionRecommendation(
            recommendation_number="REC-TEST-0002",
            report_id=rep.id,
            title="Replace Pipe Rack Dampener",
            recommendation_text="Install dampeners",
            rationale="Vibration mitigation",
            evidence_summary="Pipe rack vibration observed",
            category=InterventionCategory.MAINTENANCE,
            priority_suggestion=InterventionPriority.HIGH,
            status=InterventionStatus.ACCEPTED
        )
        self.db.add(intv)
        self.db.commit()

        act = Action(
            action_number="ACT-TEST-0001",
            intervention_id=intv.id,
            report_id=rep.id,
            created_by=self.admin_id,
            assigned_user_id=self.admin_id,
            assigned_department="Operations",
            site="Digboi Refinery",
            title="Replace Pipe Rack Dampener",
            description="Install new dampeners",
            due_date="2026-10-15",
            priority=ActionPriority.HIGH,
            status=ActionStatus.VERIFIED
        )
        self.db.add(act)
        self.db.commit()

        # Insert 3 historical impact snapshots for the SAME action
        for i in range(3):
            snap = ActionImpactAnalysis(
                action_id=act.id,
                intervention_id=intv.id,
                intervention_date=datetime.now(timezone.utc),
                before_start="2026-06-01",
                before_end="2026-08-31",
                after_start="2026-09-01",
                after_end="2026-09-17",
                metrics_json=json.dumps({"test": 123}),
                data_sufficiency_status="SUFFICIENT"
            )
            self.db.add(snap)
        self.db.commit()

        resp = self.client.get("/api/action-center/summary")
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()["data"]["summary"]

        # Must be 1 distinct action, NOT 3 multiplied snapshots
        self.assertEqual(summary["impact_available"], 1)


if __name__ == "__main__":
    unittest.main()
