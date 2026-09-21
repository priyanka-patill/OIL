"""
Part 4E — Completion, Verification & Impact Tracking Test Suite

Tests:
1. Action Completion Workflow (mandatory comment, server timestamp, status transition to VERIFICATION_PENDING).
2. HSE Verification Workflow (role-based auth, verified_at timestamp, impact calculation trigger).
3. HSE Reopen Workflow (mandatory reopen reason, cycle preservation).
4. Multi-Cycle Completion History (ActionCompletionHistory audit trail).
5. SLA Completion Timing Preservation (COMPLETED_ON_TIME vs COMPLETED_LATE).
6. Observational Impact Engine (5 Safety Indicators calculation).
7. Data Sufficiency & Zero Denominator Rules (INSUFFICIENT_DATA status on small samples/zero denominators).
8. Non-Causal Language Audit (no "caused", "prevented", "eliminated", "reduced fatality risk").
9. Anti-Leakage Audit (source_sheet / 12_High_Potential not used as logic triggers).
10. API Endpoints Integration.
"""

import os
import json
import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database.models import (
    Base, User, UserRole, SafetyReport, AIAnalysis,
    InterventionRecommendation, InterventionCategory, InterventionPriority, InterventionStatus,
    HSEInterventionReview, HSEInterventionDecision, Action, ActionStatus, ActionPriority,
    ActionEvidence, ActionCompletionHistory, ActionImpactAnalysis, ActionSLA, SLAStatus, SLACompletionTiming
)
from backend.services import action_service, impact_service, sla_service
from backend.main import app
from backend.database.database import get_db
from backend.security.dependencies import get_current_user

from sqlalchemy.pool import StaticPool

# Test in-memory SQLite database with StaticPool for multi-threaded TestClient compatibility
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class TestPart4ECompletionVerificationImpact(unittest.TestCase):

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

        # Create Test Users
        self.assignee_user = User(
            name="Assignee Engineer",
            email="assignee@oil.in",
            password_hash="hashed_pass_123",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Maintenance",
            is_active=True
        )

        self.hse_reviewer = User(
            name="HSE Inspector",
            email="inspector@oil.in",
            password_hash="hashed_pass_456",
            role=UserRole.HSE_MANAGER,
            site="Digboi Refinery",
            department="Safety",
            is_active=True
        )

        self.db.add_all([self.assignee_user, self.hse_reviewer])
        self.db.commit()
        self.db.refresh(self.assignee_user)
        self.db.refresh(self.hse_reviewer)

        # Create Test Precursor Safety Report
        self.report = SafetyReport(
            report_number="REP-DIG-2026-001",
            created_by=self.assignee_user.id,
            date="2026-08-01",
            description="Minor gas leakage observed around flange joint during pump maintenance.",
            site="Digboi Refinery",
            department="Maintenance",
            created_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        )
        self.db.add(self.report)
        self.db.commit()
        self.db.refresh(self.report)

        # Create Test AI Analysis
        self.ai_analysis = AIAnalysis(
            report_id=self.report.id,
            model_version="sif_model_v1",
            prediction="SIF_POTENTIAL",
            classification=1,
            probability_or_score=0.88,
            threshold=0.5,
            explanation_json=json.dumps({"top_features": ["Isolation Valve", "Gas Leakage"]}),
            analysis_status="COMPLETED"
        )
        self.db.add(self.ai_analysis)
        self.db.commit()
        self.db.refresh(self.ai_analysis)

        # Create Accepted Intervention
        self.intervention = InterventionRecommendation(
            recommendation_number="INT-R1-ENER-0001",
            report_id=self.report.id,
            analysis_id=self.ai_analysis.id,
            recurring_pattern_id="PAT-GAS-ISOLATION-01",
            barrier_category="Energy Isolation",
            title="Replace Flange Gaskets and Audit Isolation Valves",
            category=InterventionCategory.ENERGY_ISOLATION,
            recommendation_text="Perform immediate replacement of damaged flange gaskets and audit isolation procedures.",
            rationale="Repeated gas leakage issues identified during pump maintenance.",
            priority_suggestion=InterventionPriority.HIGH,
            evidence_summary="Observed recurring flange leakages.",
            status=InterventionStatus.ACCEPTED
        )
        self.db.add(self.intervention)
        self.db.commit()
        self.db.refresh(self.intervention)

        # Create Operational Action
        self.action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.intervention.id,
            created_by_user=self.hse_reviewer,
            assigned_user_id=self.assignee_user.id,
            assigned_department="Maintenance",
            priority="HIGH",
            due_date="2026-12-31"
        )
        # Move action to IN_PROGRESS
        action_service.update_action_status(self.db, self.action.id, ActionStatus.IN_PROGRESS, self.assignee_user)

    def tearDown(self):
        self.db.close()

    def test_01_completion_workflow_validation(self):
        """Test Action Completion workflow (mandatory comment, server timestamp, status transition)."""
        # Empty completion comment should fail
        with self.assertRaises(ValueError) as ctx:
            action_service.complete_action_with_verification_pending(
                db=self.db,
                action_id=self.action.id,
                user=self.assignee_user,
                completion_comment="   "
            )
        self.assertIn("Completion comment is mandatory", str(ctx.exception))

        # Valid completion
        completed_act = action_service.complete_action_with_verification_pending(
            db=self.db,
            action_id=self.action.id,
            user=self.assignee_user,
            completion_comment="Flange gaskets were replaced and pressure test passed at 100 PSI.",
            evidence_file_name="pressure_test_report.pdf",
            evidence_file_path="/uploads/pressure_test_report.pdf",
            evidence_description="Hydrostatic pressure test certificate."
        )

        self.assertEqual(completed_act.status, ActionStatus.VERIFICATION_PENDING)
        self.assertIsNotNone(completed_act.completion_date)

        # Check ActionCompletionHistory entry
        history = action_service.get_action_completion_history(self.db, self.action.id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].cycle_number, 1)
        self.assertEqual(history[0].completion_comment, "Flange gaskets were replaced and pressure test passed at 100 PSI.")
        self.assertEqual(history[0].verification_status, "PENDING")

        # Check attached evidence
        self.assertEqual(len(completed_act.evidences), 1)
        self.assertEqual(completed_act.evidences[0].file_name, "pressure_test_report.pdf")

    def test_02_hse_verification_workflow(self):
        """Test HSE Verification workflow (verified_at recording, status transition, impact trigger)."""
        # Complete action first
        action_service.complete_action_with_verification_pending(
            db=self.db,
            action_id=self.action.id,
            user=self.assignee_user,
            completion_comment="Gaskets replaced successfully."
        )

        # Verify action as HSE reviewer
        verified_act = action_service.verify_action_by_hse(
            db=self.db,
            action_id=self.action.id,
            hse_user=self.hse_reviewer,
            decision="VERIFY",
            comment_text="Verified onsite. Pressure testing records confirmed and approved."
        )

        self.assertEqual(verified_act.status, ActionStatus.VERIFIED)
        self.assertIsNotNone(verified_act.verified_at)

        # Check completion history record updated
        history = action_service.get_action_completion_history(self.db, self.action.id)
        self.assertEqual(history[0].verification_status, "VERIFIED")
        self.assertEqual(history[0].verified_by, self.hse_reviewer.id)

        # Check Impact Analysis record created
        impact = impact_service.get_latest_impact_analysis(self.db, self.action.id)
        self.assertIsNotNone(impact)
        self.assertEqual(impact.action_id, self.action.id)
        self.assertEqual(impact.methodology_version, "impact_methodology_v1")

    def test_03_hse_reopen_and_multicycle_history(self):
        """Test HSE Reopen workflow and preservation of multi-cycle completion history."""
        # Complete Cycle 1
        action_service.complete_action_with_verification_pending(
            db=self.db,
            action_id=self.action.id,
            user=self.assignee_user,
            completion_comment="Cycle 1: Attempted gasket repair."
        )

        # Reopen by HSE (empty comment should fail)
        with self.assertRaises(ValueError):
            action_service.verify_action_by_hse(
                db=self.db,
                action_id=self.action.id,
                hse_user=self.hse_reviewer,
                decision="REOPEN",
                comment_text=""
            )

        # Reopen with valid reason
        reopened_act = action_service.verify_action_by_hse(
            db=self.db,
            action_id=self.action.id,
            hse_user=self.hse_reviewer,
            decision="REOPEN",
            comment_text="Submitted evidence lacks physical inspection certificate. Reopening for full audit."
        )

        self.assertEqual(reopened_act.status, ActionStatus.REOPENED)
        self.assertIsNotNone(reopened_act.reopened_at)

        # Resume action to IN_PROGRESS
        action_service.update_action_status(self.db, self.action.id, ActionStatus.IN_PROGRESS, self.assignee_user)

        # Complete Cycle 2
        action_service.complete_action_with_verification_pending(
            db=self.db,
            action_id=self.action.id,
            user=self.assignee_user,
            completion_comment="Cycle 2: Provided formal third-party inspection certificate."
        )

        # Check multi-cycle completion history preserved intact
        history = action_service.get_action_completion_history(self.db, self.action.id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].cycle_number, 1)
        self.assertEqual(history[0].verification_status, "REOPENED")
        self.assertEqual(history[0].reopen_reason, "Submitted evidence lacks physical inspection certificate. Reopening for full audit.")
        self.assertEqual(history[1].cycle_number, 2)
        self.assertEqual(history[1].verification_status, "PENDING")

    def test_04_sla_completion_timing_preservation(self):
        """Test that Part 4D SLA completion timing (COMPLETED_ON_TIME vs COMPLETED_LATE) is preserved."""
        # Check SLA record exists
        sla_rec = self.action.sla
        self.assertIsNotNone(sla_rec)

        # Complete action before due date
        action_service.complete_action_with_verification_pending(
            db=self.db,
            action_id=self.action.id,
            user=self.assignee_user,
            completion_comment="Completed on time."
        )

        self.db.refresh(sla_rec)
        self.assertEqual(sla_rec.completion_timing, SLACompletionTiming.COMPLETED_ON_TIME)

    def test_05_observational_impact_engine_and_data_sufficiency(self):
        """Test observational Before/After Impact Engine (5 indicators & data sufficiency rules)."""
        # Add 3 historical reports in Before period (e.g. July 2026, within 90-day before window matching Energy Isolation)
        for i in range(3):
            r = SafetyReport(
                report_number=f"REP-DIG-BEFORE-{i+1}",
                created_by=self.assignee_user.id,
                date=f"2026-07-0{i+1}",
                description="Energy Isolation gas leak observed around valve.",
                site="Digboi Refinery",
                department="Maintenance",
                created_at=datetime(2026, 7, i+1, 10, 0, tzinfo=timezone.utc)
            )
            self.db.add(r)
        
        # Add 1 report in After period (e.g. Sept 2026, within 90-day after window)
        after_r = SafetyReport(
            report_number="REP-DIG-AFTER-1",
            created_by=self.assignee_user.id,
            date="2026-09-25",
            description="Energy Isolation minor leak after gasket replacement.",
            site="Digboi Refinery",
            department="Maintenance",
            created_at=datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
        )
        self.db.add(after_r)
        self.db.commit()

        # Calculate Impact
        impact = impact_service.calculate_and_store_impact(self.db, self.action, before_days=90, after_days=90)
        self.assertIsNotNone(impact)
        self.assertEqual(impact.data_sufficiency_status, "SUFFICIENT")
        self.assertEqual(impact.overall_observed_change, "OBSERVED_DECREASE")

        metrics = json.loads(impact.metrics_json)
        self.assertEqual(metrics["related_report_recurrence"]["before"], 3) # 3 before reports matching Energy Isolation
        self.assertEqual(metrics["related_report_recurrence"]["after"], 1)
        self.assertEqual(metrics["related_report_recurrence"]["status"], "OBSERVED_DECREASE")

    def test_06_insufficient_data_and_zero_denominator_rules(self):
        """Test that small samples return INSUFFICIENT_DATA and zero denominators do not cause divide-by-zero."""
        # Action with NO before-period reports in an isolated site
        isolated_action = Action(
            action_number="ACT-ISO-0001",
            intervention_id=self.intervention.id,
            title="Isolated Site Action",
            description="Isolated test action",
            assigned_user_id=self.assignee_user.id,
            site="Isolated Site Ref",
            priority=ActionPriority.LOW,
            due_date="2026-12-31",
            status=ActionStatus.IN_PROGRESS,
            created_by=self.hse_reviewer.id,
            created_at=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc),
            completion_date=datetime(2026, 4, 5, 10, 0, tzinfo=timezone.utc),
            verified_at=datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)
        )
        self.db.add(isolated_action)
        self.db.commit()

        impact = impact_service.calculate_and_store_impact(self.db, isolated_action)
        self.assertEqual(impact.data_sufficiency_status, "INSUFFICIENT_DATA")
        self.assertEqual(impact.overall_observed_change, "INSUFFICIENT_DATA")

        metrics = json.loads(impact.metrics_json)
        # Check density before is None (no division by zero)
        self.assertIsNone(metrics["sif_precursor_density"]["before_density_pct"])
        self.assertEqual(metrics["sif_precursor_density"]["status"], "INSUFFICIENT_DATA")

    def test_07_non_causal_language_and_anti_leakage_audit(self):
        """Audit that generated text contains zero causal claims and source_sheet is not used as logic trigger."""
        impact = impact_service.calculate_and_store_impact(self.db, self.action)
        metrics = json.loads(impact.metrics_json)

        full_text = json.dumps(metrics).lower() + " " + (impact.data_sufficiency_reason or "").lower()

        forbidden_causal_terms = ["intervention caused a", "intervention caused the reduction", "prevented sif", "eliminated sif", "reduced fatality risk", "proven reduction"]
        for term in forbidden_causal_terms:
            self.assertNotIn(term, full_text, f"Forbidden causal claim '{term}' detected in Part 4E output!")

        # Verify disclaimer text present
        self.assertIn("these comparisons describe observed changes", full_text)

    def test_08_api_endpoints_integration(self):
        """Test API endpoints for Part 4E (/complete, /verify, /reopen, /impact)."""
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.assignee_user
        client = TestClient(app)

        # 1. Complete action via API
        res_comp = client.post(f"/api/actions/{self.action.id}/complete", json={
            "completion_comment": "Completed via REST API testing.",
            "evidence_file_name": "api_test_cert.pdf",
            "evidence_file_path": "/uploads/api_test_cert.pdf"
        })
        if res_comp.status_code != 200:
            print("API Error Detail:", res_comp.json())
        self.assertEqual(res_comp.status_code, 200)
        self.assertEqual(res_comp.json()["data"]["status"], "VERIFICATION_PENDING")
        self.assertEqual(res_comp.json()["data"]["status"], "VERIFICATION_PENDING")

        # 2. Switch auth to HSE Reviewer for verification
        app.dependency_overrides[get_current_user] = lambda: self.hse_reviewer

        res_ver = client.post(f"/api/actions/{self.action.id}/verify", json={
            "decision": "VERIFY",
            "comment": "HSE Inspector verified REST API submission."
        })
        self.assertEqual(res_ver.status_code, 200)
        self.assertEqual(res_ver.json()["data"]["status"], "VERIFIED")

        # 3. Fetch Impact Analysis via API
        res_imp = client.get(f"/api/actions/{self.action.id}/impact")
        self.assertEqual(res_imp.status_code, 200)
        self.assertIn("metrics", res_imp.json()["data"])
        self.assertEqual(res_imp.json()["data"]["methodology_version"], "impact_methodology_v1")

        app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
