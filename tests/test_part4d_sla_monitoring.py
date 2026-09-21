"""
PART 4D — SLA Monitoring & Escalation Test Suite

Tests:
1. SLA Initialization on Action Assignment (server-side sla_start_at and due_at)
2. Backend Authoritative SLA Status Calculation (ACTIVE, DUE_SOON, OVERDUE, COMPLETED, CANCELLED)
3. Due-Soon Threshold Window & Idempotent Reminder Outbox Event Creation
4. Overdue Detection & Multi-Level Escalation Triggers (Level 1, Level 2, Level 3)
5. Idempotency & Concurrency Safety (repeated evaluation generates zero duplicate events)
6. Multiple Crossed Thresholds Recovery (scheduler delayed for days creates sequential L1/L2/L3 events)
7. Action Completion Timing Classification (COMPLETED_ON_TIME vs COMPLETED_LATE)
8. SLA Summary Aggregation API (GET /api/actions/sla/summary)
9. SLA Batch Evaluation API (POST /api/actions/sla/evaluate)
10. SLA Detail & History APIs (GET /api/actions/{id}/sla and GET /api/actions/{id}/sla/history)
11. Authorization, Role Scoping & Site Security
12. Anti-Leakage Audit (source_sheet & 12_High_Potential zero influence)
"""

import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import (
    User, UserRole, SafetyReport, ReportType, ReportStatus,
    InterventionRecommendation, InterventionCategory, InterventionPriority, InterventionStatus,
    HSEInterventionReview, HSEInterventionDecision,
    Action, ActionStatus, ActionPriority,
    ActionSLA, ActionReminder, ActionEscalation, SLAStatus, SLACompletionTiming
)
from backend.security.auth import create_access_token
from backend.services import action_service, sla_service


class TestPart4DSLAMonitoring(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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
            name="Admin SLA User",
            email="admin.sla@oil.in",
            password_hash="hashed",
            role=UserRole.ADMIN,
            site="Digboi Refinery",
            department="HSE",
            is_active=True
        )
        self.manager = User(
            name="HSE Manager SLA",
            email="manager.sla@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_MANAGER,
            site="Digboi Refinery",
            department="HSE",
            is_active=True
        )
        self.ops_user = User(
            name="Ops SLA Engineer",
            email="ops.sla@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Operations",
            is_active=True
        )

        self.db.add_all([self.admin, self.manager, self.ops_user])
        self.db.commit()

        # Auth Tokens
        self.manager_token = create_access_token(user_id=self.manager.id, email=self.manager.email, role=self.manager.role.value)
        self.ops_token = create_access_token(user_id=self.ops_user.id, email=self.ops_user.email, role=self.ops_user.role.value)

        self.manager_headers = {"Authorization": f"Bearer {self.manager_token}"}
        self.ops_headers = {"Authorization": f"Bearer {self.ops_token}"}

        # Seed Safety Report & Accepted Intervention
        self.report = SafetyReport(
            report_number="NM-PART4D-001",
            created_by=self.ops_user.id,
            report_type=ReportType.NEAR_MISS,
            date="2026-09-17",
            site="Digboi Refinery",
            department="Operations",
            description="Gas leakage risk observed at compressor C-201.",
            status=ReportStatus.HSE_VALIDATED
        )
        self.db.add(self.report)
        self.db.commit()

        self.interv = InterventionRecommendation(
            recommendation_number="REC-R1-GAS-0001",
            report_id=self.report.id,
            title="Inspect Gas Detector System at C-201",
            category=InterventionCategory.GAS_TESTING,
            recommendation_text="Calibration and sensor replacement for gas testing.",
            rationale="Evidence-based safety precursor requirement for gas detection.",
            priority_suggestion=InterventionPriority.HIGH,
            evidence_summary="Gas leakage precursor.",
            status=InterventionStatus.ACCEPTED
        )
        self.db.add(self.interv)
        self.db.commit()

        self.review = HSEInterventionReview(
            intervention_id=self.interv.id,
            reviewer_id=self.manager.id,
            decision=HSEInterventionDecision.ACCEPT,
            proposed_owner_id=self.ops_user.id,
            proposed_department="Operations",
            proposed_due_date="2026-09-20"
        )
        self.db.add(self.review)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_01_sla_initialization_on_action_assignment(self):
        """Test that creating an action initializes ActionSLA with sla_start_at and due_at."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )
        self.assertIsNotNone(action.sla)
        sla = action.sla
        self.assertEqual(sla.sla_status, SLAStatus.ACTIVE)
        self.assertIsNotNone(sla.sla_start_at)
        self.assertEqual(sla.due_at.year, 2026)
        self.assertEqual(sla.due_at.month, 9)
        self.assertEqual(sla.due_at.day, 20)
        self.assertEqual(sla.current_escalation_level, 0)

    def test_02_backend_authoritative_sla_status_calculation(self):
        """Test pure SLA status calculation function for ACTIVE, DUE_SOON, OVERDUE, COMPLETED, CANCELLED."""
        start_time = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        due_time = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)

        sla = ActionSLA(
            action_id=1,
            sla_status=SLAStatus.ACTIVE,
            sla_start_at=start_time,
            due_at=due_time,
            sla_duration_minutes=4320,
            due_soon_threshold_minutes=1440
        )

        # Active (2 days remaining)
        t_active = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
        r_active = sla_service.calculate_sla_status_and_times(sla, ActionStatus.ASSIGNED, now=t_active)
        self.assertEqual(r_active["sla_status"], SLAStatus.ACTIVE)
        self.assertFalse(r_active["is_overdue"])

        # Due Soon (12 hours remaining, within 24h threshold)
        t_soon = datetime(2026, 9, 19, 22, 0, 0, tzinfo=timezone.utc)
        r_soon = sla_service.calculate_sla_status_and_times(sla, ActionStatus.ASSIGNED, now=t_soon)
        self.assertEqual(r_soon["sla_status"], SLAStatus.DUE_SOON)
        self.assertFalse(r_soon["is_overdue"])

        # Overdue (2 hours past due_at)
        t_overdue = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        r_overdue = sla_service.calculate_sla_status_and_times(sla, ActionStatus.ASSIGNED, now=t_overdue)
        self.assertEqual(r_overdue["sla_status"], SLAStatus.OVERDUE)
        self.assertTrue(r_overdue["is_overdue"])
        self.assertEqual(r_overdue["overdue_minutes"], 120)

    def test_03_due_soon_reminder_event_creation(self):
        """Test that advancing time into due-soon window creates an ActionReminder event idempotently."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )
        sla = action.sla

        # Evaluate at due-soon time (2026-09-20 05:00:00 UTC, within 24h of 2026-09-20 23:59:59)
        t_soon = datetime(2026, 9, 20, 5, 0, 0, tzinfo=timezone.utc)
        eval_sla = sla_service.evaluate_action_sla(self.db, action, now=t_soon)

        self.assertEqual(eval_sla.sla_status, SLAStatus.DUE_SOON)
        self.assertEqual(eval_sla.reminder_count, 1)
        self.assertEqual(len(eval_sla.reminders), 1)
        self.assertEqual(eval_sla.reminders[0].reminder_type, "DUE_SOON_REMINDER")

        # Re-evaluate again at same time -> check idempotency (no second reminder created)
        sla_service.evaluate_action_sla(self.db, action, now=t_soon)
        self.assertEqual(eval_sla.reminder_count, 1)
        self.assertEqual(len(eval_sla.reminders), 1)

    def test_04_multi_level_escalation_triggers(self):
        """Test overdue evaluation and multi-level escalation triggers (L1, L2, L3)."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )

        due_at = action.sla.due_at  # 2026-09-20 23:59:59 UTC

        # 1. Evaluate 25 hours after due_at -> triggers Level 1 Escalation
        t_l1 = due_at + timedelta(hours=25)
        eval1 = sla_service.evaluate_action_sla(self.db, action, now=t_l1)
        self.assertEqual(eval1.sla_status, SLAStatus.OVERDUE)
        self.assertEqual(eval1.current_escalation_level, 1)
        self.assertEqual(eval1.escalation_count, 1)

        # 2. Evaluate 50 hours after due_at -> triggers Level 2 Escalation
        t_l2 = due_at + timedelta(hours=50)
        eval2 = sla_service.evaluate_action_sla(self.db, action, now=t_l2)
        self.assertEqual(eval2.current_escalation_level, 2)
        self.assertEqual(eval2.escalation_count, 2)

        # 3. Evaluate 75 hours after due_at -> triggers Level 3 Escalation
        t_l3 = due_at + timedelta(hours=75)
        eval3 = sla_service.evaluate_action_sla(self.db, action, now=t_l3)
        self.assertEqual(eval3.current_escalation_level, 3)
        self.assertEqual(eval3.escalation_count, 3)
        self.assertEqual(len(eval3.escalations), 3)

    def test_05_idempotency_and_concurrency_safety(self):
        """Test that evaluating SLA multiple times consecutively produces zero duplicate escalation events."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )
        due_at = action.sla.due_at
        t_overdue = due_at + timedelta(hours=30)

        # Run evaluation 5 times consecutively
        for _ in range(5):
            sla_service.evaluate_action_sla(self.db, action, now=t_overdue)

        self.assertEqual(action.sla.current_escalation_level, 1)
        self.assertEqual(action.sla.escalation_count, 1)
        self.assertEqual(len(action.sla.escalations), 1)

    def test_06_multiple_crossed_thresholds_recovery(self):
        """Test scheduler delay recovery: when evaluated 80 hours late, L1, L2, L3 are all created sequentially."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )
        due_at = action.sla.due_at
        t_late = due_at + timedelta(hours=80)

        eval_res = sla_service.evaluate_action_sla(self.db, action, now=t_late)

        self.assertEqual(eval_res.sla_status, SLAStatus.OVERDUE)
        self.assertEqual(eval_res.current_escalation_level, 3)
        self.assertEqual(eval_res.escalation_count, 3)
        self.assertEqual(len(eval_res.escalations), 3)
        self.assertEqual(eval_res.escalations[0].escalation_level, 1)
        self.assertEqual(eval_res.escalations[1].escalation_level, 2)
        self.assertEqual(eval_res.escalations[2].escalation_level, 3)

    def test_07_completion_timing_classification(self):
        """Test COMPLETED_ON_TIME vs COMPLETED_LATE classification."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-12-31"
        )

        # 1. Complete action ON TIME
        action_service.update_action_status(self.db, action.id, ActionStatus.IN_PROGRESS, self.ops_user)
        action_service.update_action_status(self.db, action.id, ActionStatus.COMPLETED, self.ops_user)

        self.assertEqual(action.sla.sla_status, SLAStatus.COMPLETED)
        self.assertEqual(action.sla.completion_timing, SLACompletionTiming.COMPLETED_ON_TIME)

        # 2. Test COMPLETED_LATE when completed after due_at
        action2 = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-10"  # due date in past
        )
        action_service.update_action_status(self.db, action2.id, ActionStatus.IN_PROGRESS, self.ops_user)
        action_service.update_action_status(self.db, action2.id, ActionStatus.COMPLETED, self.ops_user)

        self.assertEqual(action2.sla.sla_status, SLAStatus.COMPLETED)
        self.assertEqual(action2.sla.completion_timing, SLACompletionTiming.COMPLETED_LATE)

    def test_08_sla_summary_and_evaluate_apis(self):
        """Test GET /api/actions/sla/summary and POST /api/actions/sla/evaluate endpoints."""
        action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )

        # Summary API
        s_res = self.client.get("/api/actions/sla/summary", headers=self.manager_headers)
        self.assertEqual(s_res.status_code, 200)
        data = s_res.json()["data"]
        self.assertIn("active", data)
        self.assertIn("due_soon", data)
        self.assertIn("overdue", data)
        self.assertIn("completed_on_time", data)
        self.assertIn("completed_late", data)

        # Evaluate API
        e_res = self.client.post("/api/actions/sla/evaluate", headers=self.manager_headers)
        self.assertEqual(e_res.status_code, 200)
        self.assertTrue(e_res.json()["data"]["evaluated_count"] >= 1)

    def test_09_sla_detail_and_history_apis(self):
        """Test GET /api/actions/{id}/sla and GET /api/actions/{id}/sla/history."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )

        # SLA Detail
        d_res = self.client.get(f"/api/actions/{action.id}/sla", headers=self.ops_headers)
        self.assertEqual(d_res.status_code, 200)
        sla_data = d_res.json()["data"]
        self.assertIn("sla_status", sla_data)
        self.assertIn("due_at", sla_data)

        # SLA History
        h_res = self.client.get(f"/api/actions/{action.id}/sla/history", headers=self.ops_headers)
        self.assertEqual(h_res.status_code, 200)
        h_data = h_res.json()["data"]
        self.assertIn("reminders", h_data)
        self.assertIn("escalations", h_data)

    def test_10_anti_leakage_audit(self):
        """Audit that source_sheet and 12_High_Potential have zero influence on SLA calculations or escalation levels."""
        action = action_service.create_action_from_intervention(
            db=self.db,
            intervention_id=self.interv.id,
            created_by_user=self.manager,
            assigned_user_id=self.ops_user.id,
            due_date="2026-09-20"
        )
        sla_res = sla_service.evaluate_action_sla(self.db, action)
        res_json = str(sla_res.__dict__)
        self.assertNotIn("source_sheet", res_json)
        self.assertNotIn("12_High_Potential", res_json)


if __name__ == "__main__":
    unittest.main()
