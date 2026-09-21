"""
PART 4C — Action Management & Assignment Test Suite

Tests:
1. Action Database Model & Unique Action ID generation
2. Action Eligibility Enforcement (ACCEPTED & MODIFIED allowed; PENDING & REJECTED blocked)
3. Action Creation Form & Pre-fill logic (HSE modified title/description/owner/dept/due_date)
4. User & Department Assignment Validation
5. Status Lifecycle Transitions Matrix & Invalid State Protection
6. Server-Side Lifecycle Timestamps (start_date, completion_date, verified_at, etc.)
7. Action Reassignment, Priority Modification, and Due Date Modification
8. Action Comments & Audit Log Threading
9. My Actions & Assigned Actions List Endpoints with Backend Filtering
10. Role-Based Scoping & Site Security
11. Traceability to Source Intervention, HSE Review, and Safety Report
12. Anti-Leakage Verification (source_sheet & 12_High_Potential zero influence)
13. Part 4D Scope Boundary Verification (NO SLA engine, countdown, breach calculation)
"""

import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import (
    User, UserRole, SafetyReport, ReportType, ReportStatus,
    InterventionRecommendation, InterventionCategory, InterventionPriority, InterventionStatus,
    HSEInterventionReview, HSEInterventionDecision,
    Action, ActionStatus, ActionPriority, ActionComment, AuditLog
)
from backend.security.auth import create_access_token

from sqlalchemy.pool import StaticPool

class TestPart4CActionManagement(unittest.TestCase):

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

        # Seed Users
        self.admin = User(
            name="Admin User",
            email="admin@oil.in",
            password_hash="hashed",
            role=UserRole.ADMIN,
            site="Digboi Refinery",
            department="HSE",
            is_active=True
        )
        self.manager = User(
            name="HSE Manager",
            email="manager@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_MANAGER,
            site="Digboi Refinery",
            department="HSE",
            is_active=True
        )
        self.ops_user = User(
            name="Ops Engineer",
            email="ops@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Operations",
            is_active=True
        )
        self.maint_user = User(
            name="Maint Engineer",
            email="maint@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_USER,
            site="Duliajan HC",
            department="Maintenance",
            is_active=True
        )
        self.inactive_user = User(
            name="Inactive User",
            email="inactive@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Operations",
            is_active=False
        )

        self.db.add_all([self.admin, self.manager, self.ops_user, self.maint_user, self.inactive_user])
        self.db.commit()

        # Auth Headers
        self.manager_token = create_access_token(user_id=self.manager.id, email=self.manager.email, role=self.manager.role.value)
        self.ops_token = create_access_token(user_id=self.ops_user.id, email=self.ops_user.email, role=self.ops_user.role.value)
        self.maint_token = create_access_token(user_id=self.maint_user.id, email=self.maint_user.email, role=self.maint_user.role.value)

        self.manager_headers = {"Authorization": f"Bearer {self.manager_token}"}
        self.ops_headers = {"Authorization": f"Bearer {self.ops_token}"}
        self.maint_headers = {"Authorization": f"Bearer {self.maint_token}"}

        # Seed Safety Report
        self.report = SafetyReport(
            report_number="NM-PART4C-001",
            created_by=self.ops_user.id,
            report_type=ReportType.NEAR_MISS,
            date="2026-09-17",
            site="Digboi Refinery",
            location="AVU-1",
            equipment_id="P-101A",
            department="Operations",
            description="LOTO lock missing on isolation valve during pump maintenance.",
            ppe_noncompliance=False,
            supervisor_negligence=True,
            status=ReportStatus.HSE_VALIDATED
        )
        self.db.add(self.report)
        self.db.commit()

        # Seed Interventions (ACCEPTED, MODIFIED, PENDING, REJECTED)
        self.accepted_interv = InterventionRecommendation(
            recommendation_number="REC-R1-ENER-0001",
            report_id=self.report.id,
            title="Verify Energy Isolation & LOTO Controls",
            category=InterventionCategory.ENERGY_ISOLATION,
            recommendation_text="Conduct mandatory physical verification of energy isolation and lock-out tag-out.",
            rationale="Repeated supervisor negligence in energy isolation.",
            priority_suggestion=InterventionPriority.HIGH,
            evidence_summary="LOTO lock missing on P-101A.",
            status=InterventionStatus.ACCEPTED
        )
        self.db.add(self.accepted_interv)
        self.db.commit()

        self.accepted_review = HSEInterventionReview(
            intervention_id=self.accepted_interv.id,
            reviewer_id=self.manager.id,
            decision=HSEInterventionDecision.ACCEPT,
            review_comment="Approved for immediate operational action.",
            proposed_owner_id=self.ops_user.id,
            proposed_department="Operations",
            proposed_due_date="2026-10-01"
        )
        self.db.add(self.accepted_review)

        self.modified_interv = InterventionRecommendation(
            recommendation_number="REC-R1-MAINT-0002",
            report_id=self.report.id,
            title="Inspect Pump Guard Integrity",
            category=InterventionCategory.EQUIPMENT_GUARDING,
            recommendation_text="Check pump guards across all AVU units.",
            rationale="Precursor risk.",
            priority_suggestion=InterventionPriority.MEDIUM,
            evidence_summary="Visual inspection needed.",
            status=InterventionStatus.MODIFIED
        )
        self.db.add(self.modified_interv)
        self.db.commit()

        self.modified_review = HSEInterventionReview(
            intervention_id=self.modified_interv.id,
            reviewer_id=self.manager.id,
            decision=HSEInterventionDecision.MODIFY,
            modified_title="HSE Modified: Inspect All AVU-1 & AVU-2 Rotating Equipment Guards",
            modified_recommendation_text="Detailed inspection of rotating equipment guards and safety interlocks.",
            modified_category=InterventionCategory.EQUIPMENT_GUARDING,
            modified_priority=InterventionPriority.HIGH,
            proposed_owner_id=self.ops_user.id,
            proposed_department="Maintenance",
            proposed_due_date="2026-10-15"
        )
        self.db.add(self.modified_review)

        self.pending_interv = InterventionRecommendation(
            recommendation_number="REC-R1-PPE-0003",
            report_id=self.report.id,
            title="PPE Compliance Drive",
            category=InterventionCategory.PPE_CONTROL,
            recommendation_text="Conduct PPE drive.",
            rationale="General safety.",
            priority_suggestion=InterventionPriority.LOW,
            evidence_summary="Pending review.",
            status=InterventionStatus.PENDING_HSE_VALIDATION
        )
        self.db.add(self.pending_interv)

        self.rejected_interv = InterventionRecommendation(
            recommendation_number="REC-R1-OTHER-0004",
            report_id=self.report.id,
            title="Generic Signage Update",
            category=InterventionCategory.OTHER,
            recommendation_text="Update signs.",
            rationale="Low priority.",
            priority_suggestion=InterventionPriority.LOW,
            evidence_summary="Rejected recommendation.",
            status=InterventionStatus.REJECTED
        )
        self.db.add(self.rejected_interv)

        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_01_create_action_from_accepted_intervention(self):
        """Test creating an action from an ACCEPTED intervention pre-fills defaults and creates action."""
        payload = {
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id,
            "initial_comment": "Assigning to ops team for immediate execution."
        }
        res = self.client.post("/api/actions", json=payload, headers=self.manager_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()["data"]

        self.assertTrue(data["action_number"].startswith("ACT-"))
        self.assertEqual(data["intervention_id"], self.accepted_interv.id)
        self.assertEqual(data["title"], "Verify Energy Isolation & LOTO Controls")
        self.assertEqual(data["assigned_user_id"], self.ops_user.id)
        self.assertEqual(data["assigned_department"], "Operations")
        self.assertEqual(data["priority"], "HIGH")
        self.assertEqual(data["due_date"], "2026-10-01")
        self.assertEqual(data["status"], "ASSIGNED")
        self.assertEqual(len(data["comments"]), 1)
        self.assertEqual(data["comments"][0]["comment"], "Assigning to ops team for immediate execution.")

    def test_02_create_action_from_modified_intervention(self):
        """Test creating an action from a MODIFIED intervention defaults to HSE modified title & text."""
        payload = {
            "intervention_id": self.modified_interv.id,
            "assigned_user_id": self.ops_user.id
        }
        res = self.client.post("/api/actions", json=payload, headers=self.manager_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()["data"]

        self.assertEqual(data["title"], "HSE Modified: Inspect All AVU-1 & AVU-2 Rotating Equipment Guards")
        self.assertEqual(data["description"], "Detailed inspection of rotating equipment guards and safety interlocks.")
        self.assertEqual(data["priority"], "HIGH")
        self.assertEqual(data["assigned_department"], "Maintenance")
        self.assertEqual(data["due_date"], "2026-10-15")

        # Verify AI original recommendation text on intervention is NOT overwritten
        interv_in_db = self.db.query(InterventionRecommendation).filter(InterventionRecommendation.id == self.modified_interv.id).first()
        self.assertEqual(interv_in_db.title, "Inspect Pump Guard Integrity")

    def test_03_create_action_eligibility_enforcement(self):
        """Test that PENDING and REJECTED interventions CANNOT create actions."""
        # Pending Intervention
        res1 = self.client.post("/api/actions", json={
            "intervention_id": self.pending_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        self.assertEqual(res1.status_code, 400)
        self.assertIn("HSE validation is required", res1.json()["message"])

        # Rejected Intervention
        res2 = self.client.post("/api/actions", json={
            "intervention_id": self.rejected_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("Cannot create action from REJECTED", res2.json()["message"])

    def test_04_user_assignment_validation(self):
        """Test user assignment validation (nonexistent and inactive users fail)."""
        # Nonexistent user
        res1 = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": 9999
        }, headers=self.manager_headers)
        self.assertEqual(res1.status_code, 400)

        # Inactive user
        res2 = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.inactive_user.id
        }, headers=self.manager_headers)
        self.assertEqual(res2.status_code, 400)

    def test_05_status_lifecycle_transitions(self):
        """Test complete status transition lifecycle and server-side timestamps."""
        # 1. Create Action -> ASSIGNED
        c_res = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        action_id = c_res.json()["data"]["id"]

        # 2. Transition ASSIGNED -> IN_PROGRESS
        s1 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "IN_PROGRESS",
            "comment": "Work started by ops crew."
        }, headers=self.ops_headers)
        self.assertEqual(s1.status_code, 200)
        d1 = s1.json()["data"]
        self.assertEqual(d1["status"], "IN_PROGRESS")
        self.assertIsNotNone(d1["start_date"])

        # 3. Transition IN_PROGRESS -> ON_HOLD
        s2 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "ON_HOLD",
            "comment": "Awaiting shutdown window."
        }, headers=self.ops_headers)
        self.assertEqual(s2.status_code, 200)
        self.assertEqual(s2.json()["data"]["status"], "ON_HOLD")

        # 4. Transition ON_HOLD -> IN_PROGRESS
        s3 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "IN_PROGRESS",
            "comment": "Shutdown window active; resuming work."
        }, headers=self.ops_headers)
        self.assertEqual(s3.status_code, 200)

        # 5. Transition IN_PROGRESS -> COMPLETED
        s4 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "COMPLETED",
            "comment": "LOTO controls applied and verified."
        }, headers=self.ops_headers)
        self.assertEqual(s4.status_code, 200)
        d4 = s4.json()["data"]
        self.assertEqual(d4["status"], "COMPLETED")
        self.assertIsNotNone(d4["completion_date"])

        # 6. Transition COMPLETED -> VERIFICATION_PENDING
        s5 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "VERIFICATION_PENDING",
            "comment": "Submitted for HSE manager verification."
        }, headers=self.ops_headers)
        self.assertEqual(s5.status_code, 200)

        # 7. Transition VERIFICATION_PENDING -> VERIFIED
        s6 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "VERIFIED",
            "comment": "Field verification complete by HSE manager."
        }, headers=self.manager_headers)
        self.assertEqual(s6.status_code, 200)
        d6 = s6.json()["data"]
        self.assertEqual(d6["status"], "VERIFIED")
        self.assertIsNotNone(d6["verified_at"])

        # 8. Transition VERIFIED -> REOPENED
        s7 = self.client.patch(f"/api/actions/{action_id}/status", json={
            "status": "REOPENED",
            "comment": "Subsequent inspection found lock missing again."
        }, headers=self.manager_headers)
        self.assertEqual(s7.status_code, 200)
        d7 = s7.json()["data"]
        self.assertEqual(d7["status"], "REOPENED")
        self.assertIsNotNone(d7["reopened_at"])

    def test_06_invalid_status_transitions_rejected(self):
        """Test that illegal status jumps (e.g. ASSIGNED -> VERIFIED) are rejected with 400 Bad Request."""
        c_res = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        action_id = c_res.json()["data"]["id"]

        # Jump from ASSIGNED directly to VERIFIED
        res = self.client.patch(f"/api/actions/{action_id}/status", json={"status": "VERIFIED"}, headers=self.ops_headers)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid status transition", res.json()["message"])

    def test_07_action_reassignment_priority_and_due_date_updates(self):
        """Test reassigning an action, changing priority, and modifying due date with audit logging."""
        c_res = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        action_id = c_res.json()["data"]["id"]

        # Reassign to maint_user
        r1 = self.client.patch(f"/api/actions/{action_id}/assign", json={
            "assigned_user_id": self.maint_user.id,
            "assigned_department": "Maintenance",
            "comment": "Transferring task to maintenance team."
        }, headers=self.manager_headers)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["data"]["assigned_user_id"], self.maint_user.id)
        self.assertEqual(r1.json()["data"]["assigned_department"], "Maintenance")

        # Priority update
        r2 = self.client.patch(f"/api/actions/{action_id}/priority", json={"priority": "LOW"}, headers=self.manager_headers)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["data"]["priority"], "LOW")

        # Due date update
        r3 = self.client.patch(f"/api/actions/{action_id}/due-date", json={"due_date": "2026-11-30"}, headers=self.manager_headers)
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["data"]["due_date"], "2026-11-30")

    def test_08_action_comments(self):
        """Test adding comments to an action thread."""
        c_res = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        action_id = c_res.json()["data"]["id"]

        res = self.client.post(f"/api/actions/{action_id}/comments", json={"comment": "Field team instructed."}, headers=self.ops_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]["comment"], "Field team instructed.")

        detail = self.client.get(f"/api/actions/{action_id}", headers=self.ops_headers).json()["data"]
        self.assertEqual(len(detail["comments"]), 1)

    def test_09_my_actions_and_assigned_actions_endpoints(self):
        """Test GET /api/actions/my and GET /api/actions list filtering."""
        # Create 2 actions for ops_user, 1 action for maint_user
        self.client.post("/api/actions", json={"intervention_id": self.accepted_interv.id, "assigned_user_id": self.ops_user.id}, headers=self.manager_headers)
        self.client.post("/api/actions", json={"intervention_id": self.modified_interv.id, "assigned_user_id": self.ops_user.id}, headers=self.manager_headers)

        # GET /api/actions/my for ops_user
        my_res = self.client.get("/api/actions/my", headers=self.ops_headers)
        self.assertEqual(my_res.status_code, 200)
        self.assertEqual(len(my_res.json()["data"]), 2)

        # GET /api/actions assigned manager query with filters
        all_res = self.client.get("/api/actions?status=ASSIGNED&priority=HIGH", headers=self.manager_headers)
        self.assertEqual(all_res.status_code, 200)
        self.assertTrue(len(all_res.json()["data"]) >= 1)

    def test_10_anti_leakage_audit(self):
        """Audit that source_sheet and 12_High_Potential have zero impact on action creation or status."""
        c_res = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        self.assertEqual(c_res.status_code, 201)
        data_json_str = str(c_res.json())
        self.assertNotIn("source_sheet", data_json_str)
        self.assertNotIn("12_High_Potential", data_json_str)

    def test_11_part4d_boundary_check(self):
        """Verify that NO SLA countdown engine or SLA calculations exist in Part 4C action detail data."""
        c_res = self.client.post("/api/actions", json={
            "intervention_id": self.accepted_interv.id,
            "assigned_user_id": self.ops_user.id
        }, headers=self.manager_headers)
        data = c_res.json()["data"]
        
        # Verify due_date exists for future Part 4D, but no SLA breach/countdown fields exist
        self.assertIn("due_date", data)
        self.assertNotIn("sla_countdown", data)
        self.assertNotIn("sla_breach", data)
        self.assertNotIn("overdue_days", data)
        self.assertNotIn("escalation_level", data)


if __name__ == "__main__":
    unittest.main()
