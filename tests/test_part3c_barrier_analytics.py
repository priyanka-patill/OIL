"""
Comprehensive Unit & Integration Test Suite for Part 3C — Barrier Intelligence & BDI
"""

import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis, HSEReview, HSEDecision
from backend.main import app

from backend.analytics.data_access import AnalyticsReportDTO, get_analytics_reports
from backend.analytics.barrier_normalization import (
    map_barrier_text_to_category,
    extract_normalized_barriers_from_dto,
    BARRIER_PPE,
    BARRIER_ENERGY_ISOLATION,
    BARRIER_SUPERVISION_PERMIT,
    BARRIER_MAINTENANCE,
    BARRIER_UNMAPPED
)
from backend.analytics.barrier_analytics import calculate_barrier_frequency, extract_barrier_recurrence, get_barrier_detail_profile
from backend.analytics.barrier_trends import calculate_barrier_trends
from backend.analytics.bdi import calculate_bdi_for_barrier, calculate_all_bdi, BDI_MIN_REPORTS, BDI_METHODOLOGY_VERSION
from backend.analytics.service import AnalyticsService


class TestPart3CBarrierAnalytics(unittest.TestCase):

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

        # Seed Test Safety Reports
        self.reports = [
            SafetyReport(
                report_number="OIL-2026-000101",
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
                report_number="OIL-2026-000102",
                created_by=self.admin.id,
                report_type=ReportType.UNSAFE_ACT,
                date="2026-02-15",
                site="Digboi Refinery",
                refinery_unit="Crude Distillation Unit",
                location="Pump House A",
                equipment_id="P-101A",
                work_type="Maintenance",
                activity="Pump Maintenance",
                department="Maintenance",
                description="Worker servicing valve without lock-out tag-out isolation.",
                ppe_noncompliance=False,
                supervisor_negligence=True,
                maintenance_delay_or_issue=False,
                action_status="OPEN",
                status=ReportStatus.AI_ANALYZED
            ),
            SafetyReport(
                report_number="OIL-2026-000103",
                created_by=self.admin.id,
                report_type=ReportType.UNSAFE_CONDITION,
                date="2026-03-20",
                site="Duliajan Field",
                location="Rig 4",
                equipment_id="P-101A",
                work_type="Maintenance",
                activity="Pump Maintenance",
                department="Drilling",
                description="Electrical isolation incomplete for high voltage pump motor.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                action_status="CLOSED",
                status=ReportStatus.HSE_VALIDATED
            ),
            SafetyReport(
                report_number="OIL-2026-000104",
                created_by=self.admin.id,
                report_type=ReportType.NEAR_MISS,
                date="2026-04-05",
                site="Digboi Refinery",
                location="Substation 2",
                work_type="Inspection",
                activity="Electrical Inspection",
                department="Electrical",
                description="Technician entered high voltage room without safety helmet and glasses.",
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

        # Seed AI Analyses & HSE Reviews
        self.ai_analyses = [
            AIAnalysis(
                report_id=1,
                model_version="sif_model_v1",
                prediction="SIF-Potential",
                classification=1,
                probability_or_score=0.88,
                threshold=0.6,
                barrier_concerns_json='["Energy Isolation Defect", "Equipment Maintenance & Reliability Concern"]'
            ),
            AIAnalysis(
                report_id=2,
                model_version="sif_model_v1",
                prediction="SIF-Potential",
                classification=1,
                probability_or_score=0.75,
                threshold=0.6,
                barrier_concerns_json='["LOTO Isolation Failure", "Supervision & Work Permit Control Concern"]'
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
                probability_or_score=0.20,
                threshold=0.6,
                barrier_concerns_json='["Personal Protective Equipment (PPE) Defect"]'
            ),
        ]
        for a in self.ai_analyses:
            self.db.add(a)
        self.db.commit()

        # Add 1 HSE review for report #3 (accepted SIF)
        self.hse_review = HSEReview(
            report_id=3,
            reviewer_id=self.admin.id,
            ai_prediction_accepted=True,
            hse_decision=HSEDecision.ACCEPTED,
            modified_classification=1,
            modified_barrier_concerns_json='["Energy Isolation"]'
        )
        self.db.add(self.hse_review)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_barrier_normalization(self):
        """Verify free-text barrier mapping to standard taxonomy while preserving raw text."""
        cat1 = map_barrier_text_to_category("LOTO isolation incomplete")
        self.assertEqual(cat1, BARRIER_ENERGY_ISOLATION)

        cat2 = map_barrier_text_to_category("No helmet worn")
        self.assertEqual(cat2, BARRIER_PPE)

        cat3 = map_barrier_text_to_category("Custom obscure barrier description")
        self.assertEqual(cat3, BARRIER_UNMAPPED)

    def test_unit_of_occurrence_per_report(self):
        """Verify 1 occurrence per category per report even if multiple keywords exist."""
        dto = AnalyticsReportDTO(
            report_id=99,
            report_number="OIL-99",
            created_by=1,
            report_type="NEAR_MISS",
            date="2026-05-01",
            status="SUBMITTED",
            site="Digboi",
            refinery_unit="",
            location="",
            equipment_id="",
            work_type="",
            activity="",
            department="",
            description="",
            ppe_noncompliance=False,
            supervisor_negligence=False,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False,
            previous_similar_reports=0,
            has_ai_analysis=True,
            ai_barriers=["LOTO not applied", "Isolation valve defective", "Lockout failure"]
        )
        obs = extract_normalized_barriers_from_dto(dto)
        energy_obs = [o for o in obs if o.canonical_category == BARRIER_ENERGY_ISOLATION]
        # Should fold into 1 occurrence for Energy Isolation
        self.assertEqual(len(energy_obs), 1)

    def test_barrier_frequency_and_recurrence(self):
        """Verify frequency and recurrence calculation across test reports."""
        dtos = get_analytics_reports(self.db)
        freq = calculate_barrier_frequency(dtos)
        
        energy_item = next((item for item in freq if item["barrier_category"] == BARRIER_ENERGY_ISOLATION), None)
        self.assertIsNotNone(energy_item)
        # Reports 1, 2, and 3 all contain Energy Isolation
        self.assertEqual(energy_item["unique_reports"], 3)
        self.assertEqual(energy_item["occurrences"], 3)
        self.assertEqual(energy_item["sif_potential_association"], 3)
        self.assertEqual(energy_item["unresolved_count"], 2)

        recurring = extract_barrier_recurrence(dtos, min_support=2)
        rec_categories = [r["barrier_category"] for r in recurring]
        self.assertIn(BARRIER_ENERGY_ISOLATION, rec_categories)

    def test_barrier_trends(self):
        """Verify time-series trends grouped by month."""
        dtos = get_analytics_reports(self.db)
        trends = calculate_barrier_trends(dtos, period="month")
        self.assertGreaterEqual(len(trends), 3)

        periods = [t["period"] for t in trends]
        self.assertIn("2026-01", periods)
        self.assertIn("2026-02", periods)
        self.assertIn("2026-03", periods)

    def test_bdi_small_sample_protection(self):
        """Verify small sample protection (n < 3 reports yields INSUFFICIENT_DATA and bdi = None)."""
        dtos = get_analytics_reports(self.db)
        
        # PPE barrier only has 1 report (#4)
        bdi_ppe = calculate_bdi_for_barrier(BARRIER_PPE, dtos)
        self.assertEqual(bdi_ppe["status"], "INSUFFICIENT_DATA")
        self.assertIsNone(bdi_ppe["bdi"])

        # Energy Isolation barrier has 3 reports (#1, #2, #3)
        bdi_energy = calculate_bdi_for_barrier(BARRIER_ENERGY_ISOLATION, dtos)
        self.assertIn(bdi_energy["status"], ("SUFFICIENT_DATA", "LIMITED_DATA"))
        self.assertIsNotNone(bdi_energy["bdi"])
        self.assertGreaterEqual(bdi_energy["bdi"], 0)
        self.assertLessEqual(bdi_energy["bdi"], 100)

    def test_source_sheet_and_12_high_potential_leakage_immunity(self):
        """
        Mandatory test: Changing or removing source_sheet or using 12_High_Potential
        produces 100% identical barrier analytics and BDI outputs.
        """
        dtos1 = get_analytics_reports(self.db)
        
        # Inject fake source_sheet attribute on DTOs
        for dto in dtos1:
            dto.source_sheet = "12_High_Potential"

        res1 = calculate_all_bdi(dtos1)

        # Clear source_sheet
        for dto in dtos1:
            dto.source_sheet = "Another_Sheet_Name"

        res2 = calculate_all_bdi(dtos1)

        # Compare BDI and evidence stripping dynamic calculated_at timestamps
        for item1, item2 in zip(res1, res2):
            item1_copy = {k: v for k, v in item1.items() if k != "calculated_at"}
            item2_copy = {k: v for k, v in item2.items() if k != "calculated_at"}
            self.assertEqual(item1_copy, item2_copy)

    def test_ai_vs_hse_distinction(self):
        """Verify HSE review takes precedence for effective barrier while preserving AI source."""
        dtos = get_analytics_reports(self.db)
        dto3 = next(r for r in dtos if r.report_id == 3)
        
        self.assertTrue(dto3.has_ai_analysis)
        self.assertTrue(dto3.has_hse_review)
        self.assertIn("Electrical Isolation Incomplete", dto3.ai_barriers)
        self.assertIn("Energy Isolation", dto3.hse_barriers)
        self.assertEqual(dto3.get_effective_barriers(), ["Energy Isolation"])

    def test_api_barrier_endpoints(self):
        """Test API endpoints /api/analytics/barriers, /bdi, and /bdi/trends."""
        from backend.security.auth import create_access_token

        token = create_access_token(user_id=self.admin.id, email=self.admin.email, role=self.admin.role)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET /api/analytics/barriers
        res = self.client.get("/api/analytics/barriers", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["bdi_methodology_version"], BDI_METHODOLOGY_VERSION)
        self.assertGreater(data["total_reports_analyzed"], 0)

        # 2. GET /api/analytics/barriers/Energy Isolation
        res = self.client.get("/api/analytics/barriers/Energy Isolation", headers=headers)
        self.assertEqual(res.status_code, 200)

        # 3. GET /api/analytics/bdi
        res = self.client.get("/api/analytics/bdi", headers=headers)
        self.assertEqual(res.status_code, 200)

        # 4. GET /api/analytics/bdi/trends
        res = self.client.get("/api/analytics/bdi/trends?period=month", headers=headers)
        self.assertEqual(res.status_code, 200)

        # 5. Date validation error check
        res_err = self.client.get("/api/analytics/barriers?start_date=2026-12-31&end_date=2026-01-01", headers=headers)
        self.assertEqual(res_err.status_code, 400)


if __name__ == "__main__":
    unittest.main()
