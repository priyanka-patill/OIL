"""
Unit and Integration Test Suite for Part 3B — Hotspots, SIF Density & Trend Analytics
"""

import unittest
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis, HSEReview, HSEDecision
from backend.security.auth import hash_password, create_access_token
from backend.main import app

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.normalization import normalize_report
from backend.analytics.density import calculate_sif_density, get_data_sufficiency_status
from backend.analytics.dimensions import analyze_dimension
from backend.analytics.trends import calculate_trends
from backend.analytics.hotspots import detect_hotspots
from backend.analytics.service import AnalyticsService


class TestPart3BDensity(unittest.TestCase):
    """Unit tests for SIF Precursor Density and Small-Sample Protection."""

    def _create_dto(self, report_id: int, has_ai: bool, is_sif: bool, date_str: str = "2026-01-10") -> AnalyticsReportDTO:
        dto = AnalyticsReportDTO(
            report_id=report_id,
            report_number=f"OIL-2026-{report_id:06d}",
            created_by=1,
            report_type="NEAR_MISS",
            date=date_str,
            status="AI_ANALYZED" if has_ai else "SUBMITTED",
            site="Digboi Refinery",
            refinery_unit="Unit 1",
            location="Plant A",
            equipment_id="Pump 101",
            work_type="Maintenance",
            activity="Inspection",
            department="Operations",
            description="Test report description",
            ppe_noncompliance=False,
            supervisor_negligence=False,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False,
            previous_similar_reports=0,
            has_ai_analysis=has_ai,
            ai_classification=1 if is_sif else 0,
        )
        return normalize_report(dto)

    def test_density_cases(self):
        # Case 1: 100 analyzed, 10 SIF -> 10.0%
        reports_100 = [self._create_dto(i, has_ai=True, is_sif=(i <= 10)) for i in range(1, 101)]
        res_100 = calculate_sif_density(reports_100)
        self.assertEqual(res_100.eligible_analyzed_reports, 100)
        self.assertEqual(res_100.ai_sif_potential_count, 10)
        self.assertEqual(res_100.ai_sif_precursor_density, 0.10)
        self.assertEqual(res_100.data_sufficiency, "SUFFICIENT")

        # Case 2: 40 analyzed, 10 SIF -> 25.0%
        reports_40 = [self._create_dto(i, has_ai=True, is_sif=(i <= 10)) for i in range(1, 41)]
        res_40 = calculate_sif_density(reports_40)
        self.assertEqual(res_40.eligible_analyzed_reports, 40)
        self.assertEqual(res_40.ai_sif_potential_count, 10)
        self.assertEqual(res_40.ai_sif_precursor_density, 0.25)
        self.assertEqual(res_40.data_sufficiency, "SUFFICIENT")

        # Case 3: 0 analyzed -> density is None, NOT_AVAILABLE
        reports_0 = [self._create_dto(i, has_ai=False, is_sif=False) for i in range(1, 6)]
        res_0 = calculate_sif_density(reports_0)
        self.assertEqual(res_0.eligible_analyzed_reports, 0)
        self.assertIsNone(res_0.ai_sif_precursor_density)
        self.assertEqual(res_0.data_sufficiency, "NOT_AVAILABLE")

    def test_small_sample_protection(self):
        # 1 analyzed report with 1 SIF -> density = 1.0 (100%), but sufficiency is INSUFFICIENT
        reports_1 = [self._create_dto(1, has_ai=True, is_sif=True)]
        res_1 = calculate_sif_density(reports_1)
        self.assertEqual(res_1.eligible_analyzed_reports, 1)
        self.assertEqual(res_1.ai_sif_precursor_density, 1.0)
        self.assertEqual(res_1.data_sufficiency, "INSUFFICIENT")


class TestPart3BDimensionsAndTrends(unittest.TestCase):
    """Unit tests for dimension aggregation and time-trend calculations."""

    def _create_sample_reports(self) -> list:
        reports = []
        for i in range(1, 11):
            dto = AnalyticsReportDTO(
                report_id=i,
                report_number=f"OIL-2026-{i:06d}",
                created_by=1,
                report_type="NEAR_MISS",
                date=f"2026-01-{i:02d}",
                status="AI_ANALYZED",
                site="Digboi Refinery" if i <= 7 else "Duliajan HQ",
                refinery_unit="Unit 1",
                location="Cracker Plant",
                equipment_id="Pump P-101" if i <= 5 else "Compressor C-200",
                work_type="Maintenance",
                activity="Seal Change",
                department="Mechanical",
                description=f"Description for report {i}",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
                has_ai_analysis=True,
                ai_classification=1 if i % 2 == 1 else 0,
            )
            reports.append(normalize_report(dto))
        return reports

    def test_dimension_analysis(self):
        reports = self._create_sample_reports()
        site_profiles = analyze_dimension(reports, "site")
        self.assertGreaterEqual(len(site_profiles), 2)
        # Digboi Refinery has 7 reports, Duliajan HQ has 3
        self.assertEqual(site_profiles[0].original_value, "Digboi Refinery")
        self.assertEqual(site_profiles[0].total_reports, 7)
        self.assertIn("calculated_at", site_profiles[0].__dict__)

    def test_trends_calculation(self):
        reports = self._create_sample_reports()
        trend_res = calculate_trends(reports, period_type="month")
        self.assertEqual(trend_res.period_type, "month")
        self.assertGreater(len(trend_res.trend_points), 0)
        self.assertEqual(trend_res.total_reports_analyzed, 10)
        self.assertIn("calculated_at", trend_res.__dict__)

    def test_custom_date_range_validation_error(self):
        reports = self._create_sample_reports()
        # Invalid range: start_date > end_date
        with self.assertRaises(ValueError):
            calculate_trends(reports, custom_start_date="2026-05-01", custom_end_date="2026-01-01")


class TestPart3BHotspots(unittest.TestCase):
    """Unit tests for hotspot detection and non-punitive evidence output."""

    def test_hotspot_detection(self):
        reports = []
        for i in range(1, 6):
            dto = normalize_report(
                AnalyticsReportDTO(
                    report_id=i,
                    report_number=f"OIL-2026-{i:06d}",
                    created_by=1,
                    report_type="NEAR_MISS",
                    date=f"2026-01-0{i}",
                    status="AI_ANALYZED",
                    site="Digboi Refinery",
                    refinery_unit="Unit 3",
                    location="Main Boiler",
                    equipment_id="Boiler B-500",
                    work_type="Maintenance",
                    activity="Hot Work",
                    department="Mechanical",
                    description="Steam leak detected near Boiler B-500.",
                    ppe_noncompliance=False,
                    supervisor_negligence=False,
                    maintenance_delay_or_issue=True,
                    repeated_issue_ignored=False,
                    previous_similar_reports=0,
                    has_ai_analysis=True,
                    ai_classification=1,
                    ai_hazards=["High Temperature"],
                    ai_barriers=["Thermal Insulation"],
                )
            )
            reports.append(dto)

        res = detect_hotspots(reports, max_results=5)
        self.assertGreater(res.hotspots_count, 0)
        first_hotspot = res.hotspots[0]
        # Verify non-punitive evidence terms used
        self.assertIn("Observed Concentration", first_hotspot.evidence_reason)
        self.assertNotIn("Worst Site", first_hotspot.evidence_reason)
        self.assertNotIn("Most Dangerous", first_hotspot.evidence_reason)
        self.assertIn("calculated_at", res.__dict__)


class TestPart3BLeakageRegression(unittest.TestCase):
    """Explicit regression test proving source_sheet does NOT affect Part 3B analytics."""

    def test_source_sheet_leakage_immunity_part3b(self):
        dto = normalize_report(
            AnalyticsReportDTO(
                report_id=1,
                report_number="OIL-2026-000001",
                created_by=1,
                report_type="NEAR_MISS",
                date="2026-01-10",
                status="AI_ANALYZED",
                site="Digboi Refinery",
                refinery_unit="Unit 3",
                location="Plant A",
                equipment_id="Pump P-1",
                work_type="Maintenance",
                activity="Inspection",
                department="Operations",
                description="Test description",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=False,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
                has_ai_analysis=True,
                ai_classification=1,
            )
        )

        density = calculate_sif_density([dto])
        self.assertEqual(density.ai_sif_precursor_density, 1.0)
        self.assertFalse(hasattr(dto, "source_sheet"))

        hotspots = detect_hotspots([dto])
        for h in hotspots.hotspots:
            self.assertNotIn("source_sheet", h.evidence_reason)
            self.assertNotIn("12_High_Potential", h.evidence_reason)


class TestPart3BEndToEndComprehensive(unittest.TestCase):
    """Comprehensive end-to-end acceptance test for Part 3B (Requirement #97)."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Seed Database across 2 sites, multiple activities, equipment, locations, departments, dates
        db = self.TestingSessionLocal()
        self.admin = User(name="Admin", email="admin_e2e@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN)
        self.digboi_user = User(name="Digboi User", email="digboi_e2e@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, site="Digboi Refinery")
        self.duliajan_user = User(name="Duliajan User", email="duliajan_e2e@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, site="Duliajan HQ")
        db.add_all([self.admin, self.digboi_user, self.duliajan_user])
        db.commit()

        # Site 1: Digboi Refinery reports (Jan, Feb, Mar 2026)
        reports_data = [
            ("OIL-DIG-001", "2026-01-10", "Unit 1", "Cracker Plant", "Pump P-101", "Maintenance", "Seal Replacement", "Mechanical", True, 1, True, True),
            ("OIL-DIG-002", "2026-01-15", "Unit 1", "Cracker Plant", "Pump P-101", "Maintenance", "Seal Replacement", "Mechanical", True, 1, False, None),
            ("OIL-DIG-003", "2026-01-20", "Unit 1", "Cracker Plant", "Pump P-101", "Maintenance", "Seal Replacement", "Mechanical", True, 0, False, None),
            ("OIL-DIG-004", "2026-02-05", "Unit 2", "Boiler House", "Boiler B-500", "Hot Work", "Welding", "Operations", True, 1, True, True),
            ("OIL-DIG-005", "2026-02-12", "Unit 2", "Boiler House", "Boiler B-500", "Hot Work", "Welding", "Operations", True, 1, False, None),
            ("OIL-DIG-006", "2026-02-18", "Unit 2", "Boiler House", "Boiler B-500", "Hot Work", "Welding", "Operations", False, None, False, None), # Un-analyzed
            ("OIL-DIG-007", "2026-03-02", "Unit 3", "Substation 1", "Transformer T-1", "Electrical", "Testing", "Electrical", True, 0, False, None),
            ("OIL-DIG-008", "2026-03-10", "Unit 3", "Substation 1", "Transformer T-1", "Electrical", "Testing", "Electrical", True, 0, True, False), # Modified to non-SIF by HSE
        ]

        for num, dt_str, unit, loc, eq, wt, act, dept, has_ai, sif_cls, has_hse, hse_cls in reports_data:
            r = SafetyReport(
                report_number=num,
                created_by=self.digboi_user.id,
                report_type=ReportType.NEAR_MISS,
                date=dt_str,
                site="Digboi Refinery",
                refinery_unit=unit,
                location=loc,
                equipment_id=eq,
                work_type=wt,
                activity=act,
                department=dept,
                description=f"Description for report {num}",
                status=ReportStatus.AI_ANALYZED if has_ai else ReportStatus.SUBMITTED,
            )
            db.add(r)
            db.flush()

            if has_ai:
                ai = AIAnalysis(
                    report_id=r.id,
                    model_version="sif_model_v1",
                    prediction="SIF-Potential" if sif_cls == 1 else "Non-SIF",
                    classification=sif_cls,
                    probability_or_score=0.85 if sif_cls == 1 else 0.20,
                    threshold=0.60,
                    hazards_json=json.dumps(["Unexpected Energy"]),
                    barrier_concerns_json=json.dumps(["Energy Isolation"]),
                )
                db.add(ai)

            if has_hse:
                rev = HSEReview(
                    report_id=r.id,
                    reviewer_id=self.admin.id,
                    ai_prediction_accepted=(sif_cls == hse_cls),
                    hse_decision=HSEDecision.ACCEPTED if sif_cls == hse_cls else HSEDecision.MODIFIED,
                    modified_classification=1 if hse_cls else 0,
                    review_comment="HSE review completed.",
                )
                db.add(rev)

        # Site 2: Duliajan HQ report (1 report, no AI)
        r_dul = SafetyReport(
            report_number="OIL-DUL-001",
            created_by=self.duliajan_user.id,
            report_type=ReportType.UNSAFE_CONDITION,
            date="2026-02-15",
            site="Duliajan HQ",
            refinery_unit="HQ Main",
            location="Yard B",
            equipment_id="Crane C-40",
            work_type="Lifting",
            activity="Rigging",
            department="Logistics",
            description="Exposed wire on Crane C-40.",
            status=ReportStatus.SUBMITTED,
        )
        db.add(r_dul)
        db.commit()

        self.admin_token = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        self.digboi_token = create_access_token(self.digboi_user.id, self.digboi_user.email, self.digboi_user.role)
        self.duliajan_token = create_access_token(self.duliajan_user.id, self.duliajan_user.email, self.duliajan_user.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        app.dependency_overrides.clear()

    def test_e2e_all_part3b_features(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # 1. Site Analytics
        resp_sites = self.client.get("/api/analytics/sites", headers=headers)
        self.assertEqual(resp_sites.status_code, 200)
        data_sites = resp_sites.json()
        self.assertEqual(data_sites["profiles_count"], 2)
        digboi_prof = next(p for p in data_sites["profiles"] if p["original_value"] == "Digboi Refinery")
        self.assertEqual(digboi_prof["total_reports"], 8)
        self.assertEqual(digboi_prof["eligible_analyzed_reports"], 7)
        self.assertEqual(digboi_prof["ai_sif_count"], 4)
        self.assertEqual(len(digboi_prof["contributing_report_ids"]), 8)

        # 2. Activity Analytics
        resp_acts = self.client.get("/api/analytics/activities", headers=headers)
        self.assertEqual(resp_acts.status_code, 200)
        data_acts = resp_acts.json()
        self.assertGreaterEqual(data_acts["profiles_count"], 3)

        # 3. Equipment Analytics
        resp_eq = self.client.get("/api/analytics/equipment", headers=headers)
        self.assertEqual(resp_eq.status_code, 200)
        data_eq = resp_eq.json()
        pump_prof = next(p for p in data_eq["profiles"] if "Pump" in p["original_value"])
        self.assertEqual(pump_prof["total_reports"], 3)
        self.assertEqual(pump_prof["ai_sif_count"], 2)

        # 4. Location & Refinery Unit Analytics
        resp_loc = self.client.get("/api/analytics/locations", headers=headers)
        self.assertEqual(resp_loc.status_code, 200)

        resp_unit = self.client.get("/api/analytics/refinery-units", headers=headers)
        self.assertEqual(resp_unit.status_code, 200)

        # 5. Department Analytics
        resp_dept = self.client.get("/api/analytics/departments", headers=headers)
        self.assertEqual(resp_dept.status_code, 200)

        # 6. SIF Precursor Density (7 analyzed, 4 SIF -> 4/7 = 57.14%)
        resp_den = self.client.get("/api/analytics/density?site=Digboi%20Refinery", headers=headers)
        self.assertEqual(resp_den.status_code, 200)
        metrics = resp_den.json()["density_metrics"]
        self.assertEqual(metrics["eligible_analyzed_reports"], 7)
        self.assertEqual(metrics["ai_sif_potential_count"], 4)
        self.assertEqual(metrics["ai_sif_precursor_density"], round(4 / 7, 4))
        self.assertEqual(metrics["data_sufficiency"], "LIMITED")  # 7 is between 3 and 9

        # 7. Trends (Monthly & Weekly)
        resp_m_trend = self.client.get("/api/analytics/trends?period=month", headers=headers)
        self.assertEqual(resp_m_trend.status_code, 200)
        t_data = resp_m_trend.json()["trend_data"]
        self.assertEqual(t_data["total_periods"], 3)  # Jan, Feb, Mar 2026

        resp_w_trend = self.client.get("/api/analytics/trends?period=week", headers=headers)
        self.assertEqual(resp_w_trend.status_code, 200)

        # 8. Hotspot Analysis
        resp_hot = self.client.get("/api/analytics/hotspots", headers=headers)
        self.assertEqual(resp_hot.status_code, 200)
        data_hot = resp_hot.json()
        self.assertGreater(data_hot["hotspots_count"], 0)
        top_hot = data_hot["hotspots"][0]
        self.assertIn("contributing_report_ids", top_hot)
        self.assertIn("calculated_at", data_hot)

        # 9. RBAC Authorization Security
        hdr_dul = {"Authorization": f"Bearer {self.duliajan_token}"}
        resp_dul_sites = self.client.get("/api/analytics/sites", headers=hdr_dul)
        self.assertEqual(resp_dul_sites.status_code, 200)
        dul_data = resp_dul_sites.json()
        # Duliajan HSE_USER can ONLY see Duliajan HQ
        self.assertEqual(dul_data["profiles_count"], 1)
        self.assertEqual(dul_data["profiles"][0]["original_value"], "Duliajan HQ")


if __name__ == "__main__":
    unittest.main()
