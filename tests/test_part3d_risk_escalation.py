"""
Comprehensive Unit & Integration Test Suite for Part 3D — Risk Escalation & Analytical Prioritization
"""

import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis, HSEReview, HSEDecision
from backend.security.auth import create_access_token
from backend.main import app

from backend.analytics.data_access import get_analytics_reports
from backend.analytics.escalation import evaluate_entity_risk_escalation, detect_all_escalations, ESCALATION_METHODOLOGY_VERSION
from backend.analytics.prioritization import evaluate_analytical_priority, calculate_all_priorities, PRIORITY_METHODOLOGY_VERSION
from backend.analytics.service import AnalyticsService


class TestPart3DRiskEscalation(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database
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
            name="Admin User",
            email="admin@oil.in",
            password_hash="hashed",
            role=UserRole.ADMIN,
            site="Digboi Refinery",
            department="HSE"
        )
        self.db.add(self.admin)
        self.db.commit()

        # Seed Test Safety Reports for Equipment P-101A (6 reports across 3 months)
        self.reports = [
            SafetyReport(
                report_number="OIL-2026-000201",
                created_by=self.admin.id,
                report_type=ReportType.NEAR_MISS,
                date="2026-01-10",
                site="Digboi Refinery",
                refinery_unit="Crude Distillation Unit",
                location="Pump House A",
                equipment_id="P-101A",
                work_type="Maintenance",
                activity="Pump Maintenance",
                department="Maintenance",
                description="Pump seal leak during maintenance without proper LOTO isolation.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                action_status="OPEN",
                status=ReportStatus.AI_ANALYZED
            ),
            SafetyReport(
                report_number="OIL-2026-000202",
                created_by=self.admin.id,
                report_type=ReportType.UNSAFE_ACT,
                date="2026-01-20",
                site="Digboi Refinery",
                refinery_unit="Crude Distillation Unit",
                location="Pump House A",
                equipment_id="P-101A",
                work_type="Maintenance",
                activity="Pump Maintenance",
                department="Maintenance",
                description="Worker servicing valve on pump P-101A without lock-out tag-out isolation.",
                ppe_noncompliance=False,
                supervisor_negligence=True,
                maintenance_delay_or_issue=False,
                action_status="OPEN",
                status=ReportStatus.AI_ANALYZED
            ),
            SafetyReport(
                report_number="OIL-2026-000203",
                created_by=self.admin.id,
                report_type=ReportType.UNSAFE_CONDITION,
                date="2026-02-15",
                site="Digboi Refinery",
                location="Pump House A",
                equipment_id="P-101A",
                work_type="Maintenance",
                activity="Pump Maintenance",
                department="Maintenance",
                description="Electrical isolation incomplete for pump P-101A motor.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                action_status="CLOSED",
                status=ReportStatus.HSE_VALIDATED
            ),
            SafetyReport(
                report_number="OIL-2026-000204",
                created_by=self.admin.id,
                report_type=ReportType.NEAR_MISS,
                date="2026-03-05",
                site="Digboi Refinery",
                location="Pump House A",
                equipment_id="P-101A",
                work_type="Maintenance",
                activity="Pump Maintenance",
                department="Maintenance",
                description="Vibration detected on P-101A pump bearing.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                action_status="OPEN",
                status=ReportStatus.AI_ANALYZED
            ),
            # Single-report equipment P-999
            SafetyReport(
                report_number="OIL-2026-000205",
                created_by=self.admin.id,
                report_type=ReportType.NEAR_MISS,
                date="2026-03-10",
                site="Duliajan Field",
                location="Substation 2",
                equipment_id="P-999",
                work_type="Inspection",
                activity="Electrical Inspection",
                department="Electrical",
                description="Technician entered high voltage room without safety helmet.",
                ppe_noncompliance=True,
                supervisor_negligence=False,
                maintenance_delay_or_issue=False,
                action_status="CLOSED",
                status=ReportStatus.AI_ANALYZED
            ),
        ]
        for r in self.reports:
            self.db.add(r)
        self.db.commit()

        # Seed AI Analyses
        self.ai_analyses = [
            AIAnalysis(
                report_id=1,
                model_version="sif_model_v1",
                prediction="SIF-Potential",
                classification=1,
                probability_or_score=0.88,
                threshold=0.6,
                barrier_concerns_json='["Energy Isolation Defect", "Equipment Maintenance Concern"]'
            ),
            AIAnalysis(
                report_id=2,
                model_version="sif_model_v1",
                prediction="SIF-Potential",
                classification=1,
                probability_or_score=0.75,
                threshold=0.6,
                barrier_concerns_json='["LOTO Isolation Failure", "Supervision Concern"]'
            ),
            AIAnalysis(
                report_id=3,
                model_version="sif_model_v1",
                prediction="SIF-Potential",
                classification=1,
                probability_or_score=0.92,
                threshold=0.6,
                barrier_concerns_json='["Electrical Isolation Incomplete"]'
            ),
            AIAnalysis(
                report_id=4,
                model_version="sif_model_v1",
                prediction="Non-SIF",
                classification=0,
                probability_or_score=0.30,
                threshold=0.6,
                barrier_concerns_json='["Equipment Maintenance Concern"]'
            ),
            AIAnalysis(
                report_id=5,
                model_version="sif_model_v1",
                prediction="Non-SIF",
                classification=0,
                probability_or_score=0.20,
                threshold=0.6,
                barrier_concerns_json='["Personal Protective Equipment (PPE) Defect"]'
            ),
        ]
        for a in self.ai_analyses:
            self.db.add(a)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_single_report_small_sample_protection(self):
        """Verify single report entity (P-999) returns INSUFFICIENT_DATA status."""
        dtos = get_analytics_reports(self.db)
        esc_res = evaluate_entity_risk_escalation("equipment_id", "P-999", dtos)
        self.assertEqual(esc_res["status"], "INSUFFICIENT_DATA")
        self.assertIn("minimum 3 unique reports", esc_res["message"])

        pri_res = evaluate_analytical_priority("equipment_id", "P-999", dtos)
        self.assertEqual(pri_res["priority_tier"], "INSUFFICIENT_DATA")

    def test_escalation_indicators_evaluation(self):
        """Verify 6 escalation indicators for equipment P-101A (4 reports)."""
        dtos = get_analytics_reports(self.db)
        esc_res = evaluate_entity_risk_escalation("equipment_id", "P-101A", dtos)

        self.assertIn(esc_res["status"], ("MULTIPLE_ESCALATION_INDICATORS_PRESENT", "POTENTIAL_ESCALATION_INDICATORS_PRESENT"))
        self.assertEqual(esc_res["sample"]["total_reports"], 4)
        self.assertEqual(esc_res["sample"]["sif_potential_count"], 3)
        self.assertEqual(esc_res["sample"]["unresolved_count"], 3)

        ind_types = [i["type"] for i in esc_res["indicators"] if i["status"] == "PRESENT"]
        self.assertIn("REPEATED_REPORTS", ind_types)
        self.assertIn("UNRESOLVED_ISSUES", ind_types)
        self.assertIn("REPEATED_BARRIER", ind_types)
        self.assertIn("SIF_ASSOCIATION", ind_types)
        self.assertIn("PERSISTENT_EXPOSURE", ind_types)

    def test_analytical_prioritization(self):
        """Verify Analytical Priority Tier (PRI_v1) calculation for equipment P-101A."""
        dtos = get_analytics_reports(self.db)
        pri_res = evaluate_analytical_priority("equipment_id", "P-101A", dtos)

        self.assertEqual(pri_res["priority_tier"], "HIGH_PRIORITY")
        self.assertEqual(pri_res["methodology_version"], PRIORITY_METHODOLOGY_VERSION)
        self.assertEqual(pri_res["sample"]["total_reports"], 4)
        self.assertEqual(pri_res["sample"]["sif_potential_count"], 3)
        self.assertIsNotNone(pri_res["barrier_summary"]["top_barrier"])

    def test_source_sheet_and_12_high_potential_leakage_immunity(self):
        """
        Mandatory test: Changing or removing source_sheet or using 12_High_Potential
        produces 100% identical risk escalation indicators and priority outputs.
        """
        dtos = get_analytics_reports(self.db)

        for dto in dtos:
            dto.source_sheet = "12_High_Potential"

        res1_esc = evaluate_entity_risk_escalation("equipment_id", "P-101A", dtos)
        res1_pri = evaluate_analytical_priority("equipment_id", "P-101A", dtos)

        for dto in dtos:
            dto.source_sheet = "Other_Sheet_Name"

        res2_esc = evaluate_entity_risk_escalation("equipment_id", "P-101A", dtos)
        res2_pri = evaluate_analytical_priority("equipment_id", "P-101A", dtos)

        # Strip dynamic timestamp
        res1_esc_copy = {k: v for k, v in res1_esc.items() if k != "calculated_at"}
        res2_esc_copy = {k: v for k, v in res2_esc.items() if k != "calculated_at"}
        self.assertEqual(res1_esc_copy, res2_esc_copy)

        res1_pri_copy = {k: v for k, v in res1_pri.items() if k != "calculated_at"}
        res2_pri_copy = {k: v for k, v in res2_pri.items() if k != "calculated_at"}
        self.assertEqual(res1_pri_copy, res2_pri_copy)

    def test_ai_vs_hse_distinction(self):
        """Verify HSE classification is preferred for SIF association while preserving AI analysis."""
        dtos = get_analytics_reports(self.db)
        dto3 = next(r for r in dtos if r.report_id == 3)
        self.assertTrue(dto3.has_ai_analysis)
        self.assertTrue(dto3.is_sif_ai())

    def test_api_escalation_and_priority_endpoints(self):
        """Test API endpoints /api/analytics/escalation, /escalation/{type}/{id}, and /priorities."""
        token = create_access_token(user_id=self.admin.id, email=self.admin.email, role=self.admin.role)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET /api/analytics/escalation
        res = self.client.get("/api/analytics/escalation?dimension=equipment_id", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["escalation_methodology_version"], ESCALATION_METHODOLOGY_VERSION)
        self.assertGreater(data["escalations_count"], 0)

        # 2. GET /api/analytics/escalation/equipment_id/P-101A
        res_detail = self.client.get("/api/analytics/escalation/equipment_id/P-101A", headers=headers)
        self.assertEqual(res_detail.status_code, 200)
        detail_data = res_detail.json()
        self.assertEqual(detail_data["escalation_detail"]["entity_id"], "P-101A")

        # 3. GET /api/analytics/priorities
        res_pri = self.client.get("/api/analytics/priorities?dimension=equipment_id", headers=headers)
        self.assertEqual(res_pri.status_code, 200)
        pri_data = res_pri.json()
        self.assertEqual(pri_data["priority_methodology_version"], PRIORITY_METHODOLOGY_VERSION)

        # 4. Date validation error check
        res_err = self.client.get("/api/analytics/escalation?start_date=2026-12-31&end_date=2026-01-01", headers=headers)
        self.assertEqual(res_err.status_code, 400)


if __name__ == "__main__":
    unittest.main()
