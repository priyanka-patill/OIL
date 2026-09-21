"""
Unit and Integration Test Suite for Part 3A — Analytics Foundation & Cross-Report Intelligence
"""

import unittest
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis, HSEReview, HSEDecision
from backend.security.auth import hash_password, create_access_token
from backend.main import app

from backend.analytics.data_access import AnalyticsReportDTO, get_analytics_reports
from backend.analytics.normalization import normalize_text, normalize_report
from backend.analytics.duplicates import detect_duplicates, compute_fingerprint, DuplicateGroup
from backend.analytics.correlation import calculate_correlations
from backend.analytics.patterns import detect_recurring_patterns, RecurringPattern
from backend.analytics.related_reports import find_related_reports
from backend.analytics.service import AnalyticsService
from backend.analytics.config import MISSING_VALUE_PLACEHOLDER, ANALYTICS_VERSION, ANALYTICS_MIN_PATTERN_COUNT


class TestPart3ANormalization(unittest.TestCase):
    """Test normalization behavior."""

    def test_text_normalization(self):
        self.assertEqual(normalize_text(" Pump A "), "pump a")
        self.assertEqual(normalize_text("PUMP A"), "pump a")
        self.assertEqual(normalize_text("pump   a"), "pump a")
        self.assertEqual(normalize_text(""), MISSING_VALUE_PLACEHOLDER)
        self.assertEqual(normalize_text(None), MISSING_VALUE_PLACEHOLDER)

    def test_technical_identifiers_preserved(self):
        # Technical hyphens and identifiers must be preserved distinctly
        norm1 = normalize_text("Pump A-101")
        norm2 = normalize_text("Pump A101")
        self.assertEqual(norm1, "pump a-101")
        self.assertEqual(norm2, "pump a101")
        self.assertNotEqual(norm1, norm2)

    def test_original_values_preserved_on_dto(self):
        raw_dto = AnalyticsReportDTO(
            report_id=1,
            report_number="OIL-2026-000001",
            created_by=1,
            report_type="NEAR_MISS",
            date="2026-01-10",
            status="SUBMITTED",
            site="Digboi Refinery",
            refinery_unit="Unit 3 ",
            location=" North Platform ",
            equipment_id="Pump A-101 ",
            work_type="Maintenance ",
            activity=" Valve Inspection ",
            department=" Operations ",
            description="High pressure leak detected during pump maintenance.",
            ppe_noncompliance=False,
            supervisor_negligence=False,
            maintenance_delay_or_issue=True,
            repeated_issue_ignored=False,
            previous_similar_reports=1,
        )

        norm_dto = normalize_report(raw_dto)
        # Original fields MUST remain intact
        self.assertEqual(norm_dto.equipment_id, "Pump A-101 ")
        self.assertEqual(norm_dto.work_type, "Maintenance ")

        # Normalized cache should hold canonical strings
        self.assertEqual(norm_dto.normalized["equipment_id"], "pump a-101")
        self.assertEqual(norm_dto.normalized["work_type"], "maintenance")


class TestPart3ADuplicateDetection(unittest.TestCase):
    """Test exact and near-duplicate detection."""

    def test_exact_fingerprint_duplicate(self):
        dto1 = normalize_report(
            AnalyticsReportDTO(
                report_id=1,
                report_number="OIL-2026-000001",
                created_by=1,
                report_type="NEAR_MISS",
                date="2026-01-10",
                status="SUBMITTED",
                site="Digboi Refinery",
                refinery_unit="Unit 3",
                location="North Platform",
                equipment_id="Pump A-101",
                work_type="Maintenance",
                activity="Valve Inspection",
                department="Operations",
                description="High pressure gas leak observed during valve replacement.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
            )
        )

        dto2 = normalize_report(
            AnalyticsReportDTO(
                report_id=2,
                report_number="OIL-2026-000002",
                created_by=2,
                report_type="NEAR_MISS",
                date="2026-01-10",
                status="SUBMITTED",
                site="DIGBOI REFINERY ",
                refinery_unit="Unit 3",
                location="North Platform",
                equipment_id="PUMP A-101",
                work_type="MAINTENANCE",
                activity="valve inspection",
                department="OPERATIONS",
                description="High pressure gas leak observed during valve replacement.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
            )
        )

        groups = detect_duplicates([dto1, dto2])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].duplicate_level, "LEVEL_1_EXACT")
        self.assertIn(1, groups[0].member_report_ids)
        self.assertIn(2, groups[0].member_report_ids)

    def test_near_duplicate_tfidf(self):
        dto1 = normalize_report(
            AnalyticsReportDTO(
                report_id=10,
                report_number="OIL-2026-000010",
                created_by=1,
                report_type="NEAR_MISS",
                date="2026-01-10",
                status="SUBMITTED",
                site="Digboi Refinery",
                refinery_unit="Unit 3",
                location="North Platform",
                equipment_id="Pump A",
                work_type="Maintenance",
                activity="Valve Change",
                department="Operations",
                description="Gas leak detected near high pressure control valve during routine morning inspection.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=False,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
            )
        )

        dto2 = normalize_report(
            AnalyticsReportDTO(
                report_id=11,
                report_number="OIL-2026-000011",
                created_by=1,
                report_type="NEAR_MISS",
                date="2026-01-11",
                status="SUBMITTED",
                site="Digboi Refinery",
                refinery_unit="Unit 3",
                location="South Platform",
                equipment_id="Pump B",
                work_type="Maintenance",
                activity="Valve Cleaning",
                department="Operations",
                description="Gas leak detected near high pressure control valve during routine morning inspection of unit.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=False,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
            )
        )

        groups = detect_duplicates([dto1, dto2], similarity_threshold=0.70)
        self.assertGreaterEqual(len(groups), 1)
        self.assertEqual(groups[0].duplicate_level, "LEVEL_2_NEAR_DUPLICATE")


class TestPart3ACorrelationAndPatterns(unittest.TestCase):
    """Test correlation calculation and pattern minimum support thresholding."""

    def _create_sample_reports(self, count: int, equipment: str, activity: str, barrier: str) -> list:
        reports = []
        for i in range(1, count + 1):
            dto = AnalyticsReportDTO(
                report_id=i,
                report_number=f"OIL-2026-{i:06d}",
                created_by=1,
                report_type="NEAR_MISS",
                date=f"2026-01-{i:02d}",
                status="SUBMITTED",
                site="Digboi Refinery",
                refinery_unit="Unit 1",
                location="Pump House",
                equipment_id=equipment,
                work_type="Maintenance",
                activity=activity,
                department="Operations",
                description=f"Incident report #{i} regarding {equipment} during {activity}.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
                has_ai_analysis=True,
                ai_classification=1 if i % 2 == 1 else 0,
                ai_barriers=[barrier],
            )
            reports.append(normalize_report(dto))
        return reports

    def test_correlation_count(self):
        reports = self._create_sample_reports(5, "Pump A", "Maintenance", "Energy Isolation")
        corr = calculate_correlations(reports, min_count=1)
        self.assertEqual(corr.total_reports_analyzed, 5)

        # Multi-factor correlation for Pump A + Maintenance + Energy Isolation should have count=5
        multi = corr.multi_factor_correlations
        self.assertTrue(any(item.occurrence_count == 5 for item in multi))

    def test_pattern_minimum_support(self):
        # 5 reports for Pump A (exceeds default min_support=3)
        reports_5 = self._create_sample_reports(5, "Pump A", "Maintenance", "Energy Isolation")
        patterns_5 = detect_recurring_patterns(reports_5, min_support=3)
        self.assertGreater(len(patterns_5), 0)
        self.assertEqual(patterns_5[0].occurrence_count, 5)
        self.assertEqual(len(patterns_5[0].report_ids), 5)

        # Single 1-off report for Pump X (below min_support=3)
        reports_1 = self._create_sample_reports(1, "Pump X", "Painting", "PPE")
        patterns_1 = detect_recurring_patterns(reports_1, min_support=3)
        # Should NOT yield a recurring pattern
        self.assertEqual(len(patterns_1), 0)


class TestPart3ALeakageRegression(unittest.TestCase):
    """Explicit regression test proving source_sheet does NOT affect analytics."""

    def test_source_sheet_leakage_immunity(self):
        dto1 = normalize_report(
            AnalyticsReportDTO(
                report_id=1,
                report_number="OIL-2026-000001",
                created_by=1,
                report_type="NEAR_MISS",
                date="2026-01-10",
                status="SUBMITTED",
                site="Digboi Refinery",
                refinery_unit="Unit 3",
                location="North Platform",
                equipment_id="Pump A-101",
                work_type="Maintenance",
                activity="Valve Inspection",
                department="Operations",
                description="High pressure gas leak observed during valve replacement.",
                ppe_noncompliance=False,
                supervisor_negligence=False,
                maintenance_delay_or_issue=True,
                repeated_issue_ignored=False,
                previous_similar_reports=0,
            )
        )

        fp1 = compute_fingerprint(dto1)

        # Verify that AnalyticsReportDTO doesn't even accept source_sheet as an analytical attribute
        self.assertFalse(hasattr(dto1, "source_sheet"))

        # Compute pattern detection
        patterns = detect_recurring_patterns([dto1, dto1, dto1], min_support=3)
        self.assertGreater(len(patterns), 0)
        for p in patterns:
            self.assertNotIn("source_sheet", p.dimensions)
            self.assertNotIn("12_High_Potential", str(p.dimensions))


from sqlalchemy.pool import StaticPool

class TestPart3AIntegration(unittest.TestCase):
    """Full database & API integration test for Part 3A."""

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

        # Seed Database
        db = self.TestingSessionLocal()
        self.admin_user = User(
            name="Admin User",
            email="admin_p3a@oil.in",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
        )
        self.digboi_user = User(
            name="Digboi User",
            email="digboi_p3a@oil.in",
            password_hash=hash_password("UserPass123!"),
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
        )
        self.duliajan_user = User(
            name="Duliajan User",
            email="duliajan_p3a@oil.in",
            password_hash=hash_password("UserPass123!"),
            role=UserRole.HSE_USER,
            site="Duliajan HQ",
        )
        db.add_all([self.admin_user, self.digboi_user, self.duliajan_user])
        db.commit()

        # Seed 5 Digboi reports with identical equipment & activity
        for i in range(1, 6):
            r = SafetyReport(
                report_number=f"OIL-DIG-2026-{i:03d}",
                created_by=self.digboi_user.id,
                report_type=ReportType.NEAR_MISS,
                date=f"2026-02-{i:02d}",
                site="Digboi Refinery",
                refinery_unit="Unit 3",
                location="Cracker Plant",
                equipment_id="Pump P-101",
                work_type="Maintenance",
                activity="Seal Replacement",
                department="Mechanical",
                description="High pressure hydrocarbon gas leak observed during seal replacement on Pump P-101.",
                maintenance_delay_or_issue=True,
                status=ReportStatus.AI_ANALYZED,
            )
            db.add(r)
            db.flush()

            ai = AIAnalysis(
                report_id=r.id,
                model_version="sif_model_v1",
                prediction="SIF-Potential",
                classification=1,
                probability_or_score=0.85,
                threshold=0.60,
                hazards_json=json.dumps(["Unexpected Energy", "Flammable Gas"]),
                barrier_concerns_json=json.dumps(["Energy Isolation"]),
                life_saving_rules_json=json.dumps(["Bypass Safeguards"]),
            )
            db.add(ai)

        # Seed 1 Duliajan report (restricted to Duliajan HSE_USER)
        r_dul = SafetyReport(
            report_number="OIL-DUL-2026-001",
            created_by=self.duliajan_user.id,
            report_type=ReportType.UNSAFE_CONDITION,
            date="2026-02-10",
            site="Duliajan HQ",
            refinery_unit="HQ Main",
            location="Substation 1",
            equipment_id="Transformer T-1",
            work_type="Electrical",
            activity="Testing",
            department="Electrical",
            description="Exposed cable detected at substation Transformer T-1.",
            status=ReportStatus.SUBMITTED,
        )
        db.add(r_dul)
        db.commit()

        self.admin_token = create_access_token(self.admin_user.id, self.admin_user.email, self.admin_user.role)
        self.digboi_token = create_access_token(self.digboi_user.id, self.digboi_user.email, self.digboi_user.role)
        self.duliajan_token = create_access_token(self.duliajan_user.id, self.duliajan_user.email, self.duliajan_user.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        app.dependency_overrides.clear()

    def test_api_get_patterns_admin(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.get("/api/analytics/patterns", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("patterns", data)
        self.assertGreater(data["patterns_count"], 0)
        first_pat = data["patterns"][0]
        self.assertEqual(first_pat["occurrence_count"], 5)
        self.assertEqual(first_pat["ai_sif_count"], 5)

    def test_api_rbac_authorization_pre_filtering(self):
        # Duliajan user (only has 1 report at Duliajan HQ) should see 0 recurring patterns when min_support=3
        headers = {"Authorization": f"Bearer {self.duliajan_token}"}
        resp = self.client.get("/api/analytics/patterns", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Duliajan user MUST NOT see Digboi's 5 reports in aggregate patterns!
        self.assertEqual(data["patterns_count"], 0)

    def test_api_related_reports(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.get("/api/analytics/related-reports/1", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["target_report_id"], 1)
        self.assertGreater(data["related_count"], 0)
        first_rel = data["related_reports"][0]
        self.assertIn("Pump P-101", first_rel["evidence_explanation"])

    def test_api_duplicate_detection(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.get("/api/analytics/duplicates", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("duplicate_groups", data)
        self.assertGreater(data["duplicate_groups_count"], 0)

    def test_api_correlations(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.get("/api/analytics/correlation", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("multi_factor_correlations", data)


if __name__ == "__main__":
    unittest.main()
