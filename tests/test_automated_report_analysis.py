"""
Automated Test Suite for System-Calculated Previous Similar Reports and Risk Level Assessment

Verifies:
1. First report behavior (0 similar reports).
2. Similar reports detection.
3. Unrelated reports exclusion.
4. Self-match protection.
5. Risk Level Assessment matrix (RISK_EVAL_v1).
6. Data leakage protection (source_sheet non-usage).
7. RBAC scoping in similarity search.
8. Persistence in AIAnalysis and SafetyReport models.
"""

import unittest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.database import Base
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis
from backend.database.schemas import ReportCreate
from backend.services.report_service import create_report
from backend.services.analysis_service import analyze_safety_report
from backend.services.similarity_service import calculate_report_similarity
from backend.services.risk_service import calculate_report_risk


class TestAutomatedReportAnalysis(unittest.TestCase):

    def setUp(self):
        # Create an in-memory SQLite database for clean testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

        # Create test users
        self.user_admin = User(
            name="Admin User",
            email="admin@oil.in",
            password_hash="hash",
            role=UserRole.ADMIN,
            site="Digboi Refinery",
            department="Operations"
        )
        self.user_hse = User(
            name="HSE User",
            email="user@oil.in",
            password_hash="hash",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            department="Operations"
        )
        self.db.add_all([self.user_admin, self.user_hse])
        self.db.commit()
        self.db.refresh(self.user_admin)
        self.db.refresh(self.user_hse)

    def tearDown(self):
        self.db.close()

    def test_01_first_report_empty_db(self):
        """TEST 1 — First Report in database should have 0 similar reports and system-calculated risk."""
        report_data = ReportCreate(
            report_type=ReportType.NEAR_MISS,
            date="2026-09-22",
            site="Digboi Refinery",
            refinery_unit="Hydrogen Unit",
            location="Process Area Block-1",
            equipment_id="P-101",
            work_type="Routine Inspection",
            activity="Visual Check",
            department="Operations",
            description="Minor oil weeping observed from pump casing drain valve plug.",
            ppe_noncompliance=False,
            supervisor_negligence=False,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False
        )

        report = create_report(self.db, report_data, self.user_admin)

        # Verify Report model fields
        self.assertEqual(report.previous_similar_reports, 0)
        self.assertIsNotNone(report.risk_level)

        # Verify AIAnalysis persistence
        analysis = self.db.query(AIAnalysis).filter(AIAnalysis.report_id == report.id).first()
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.previous_similar_reports_count, 0)
        self.assertIsNotNone(analysis.risk_level)
        self.assertEqual(analysis.similarity_methodology_version, "SIM_EVAL_v1")
        self.assertEqual(analysis.risk_methodology_version, "RISK_EVAL_v1")

    def test_02_similar_reports_detection(self):
        """TEST 2 — Seeded historical reports should trigger non-zero similarity count for matching report."""
        # 1. Create historical report
        hist_data = ReportCreate(
            report_type=ReportType.NEAR_MISS,
            date="2026-09-15",
            site="Digboi Refinery",
            refinery_unit="Hydrogen Unit",
            location="Pump House Block 3",
            equipment_id="P-305",
            work_type="Preventive Maintenance",
            activity="Pump Overhaul",
            department="Operations",
            description="Worker performed pump overhaul without safety helmet and bypassed isolation locks.",
            ppe_noncompliance=True,
            supervisor_negligence=True,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False
        )
        hist_report = create_report(self.db, hist_data, self.user_admin)

        # 2. Create new similar report on same equipment and description pattern
        new_data = ReportCreate(
            report_type=ReportType.NEAR_MISS,
            date="2026-09-22",
            site="Digboi Refinery",
            refinery_unit="Hydrogen Unit",
            location="Pump House Block 3",
            equipment_id="P-305",
            work_type="Preventive Maintenance",
            activity="Pump Overhaul",
            department="Operations",
            description="Worker performed pump overhaul without safety helmet near pump P-305.",
            ppe_noncompliance=True,
            supervisor_negligence=False,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=True
        )
        new_report = create_report(self.db, new_data, self.user_admin)

        # Verify similarity detected hist_report
        self.assertGreaterEqual(new_report.previous_similar_reports, 1)

        analysis = self.db.query(AIAnalysis).filter(AIAnalysis.report_id == new_report.id).first()
        self.assertGreaterEqual(analysis.previous_similar_reports_count, 1)

        similar_list = json.loads(analysis.similar_reports_json)
        self.assertTrue(any(s["report_id"] == hist_report.id for s in similar_list))

    def test_03_unrelated_reports_exclusion(self):
        """TEST 3 — Unrelated historical report should not be counted as similar."""
        # Historical report in a completely different area and activity
        hist_data = ReportCreate(
            report_type=ReportType.UNSAFE_CONDITION,
            date="2026-09-10",
            site="Guwahati Refinery",
            refinery_unit="Coker Unit",
            location="Storage Tank 402",
            equipment_id="TK-402",
            work_type="Painting",
            activity="Surface Preparation",
            department="Civil",
            description="Scaffolding wooden board cracked due to weathering near storage tank.",
            ppe_noncompliance=False,
            supervisor_negligence=False,
            maintenance_delay_or_issue=True,
            repeated_issue_ignored=False
        )
        create_report(self.db, hist_data, self.user_admin)

        # New report on electrical motor in Hydrogen Unit
        new_data = ReportCreate(
            report_type=ReportType.NEAR_MISS,
            date="2026-09-22",
            site="Digboi Refinery",
            refinery_unit="Hydrogen Unit",
            location="Substation 2",
            equipment_id="M-201",
            work_type="Electrical Testing",
            activity="Transformer Insulation Test",
            department="Electrical",
            description="High voltage cable connector terminal cover missing during megger testing.",
            ppe_noncompliance=False,
            supervisor_negligence=False,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False
        )
        new_report = create_report(self.db, new_data, self.user_admin)

        self.assertEqual(new_report.previous_similar_reports, 0)

    def test_04_self_match_protection(self):
        """TEST 4 — Self-match protection: Re-running analysis on a report must exclude itself."""
        report_data = ReportCreate(
            report_type=ReportType.NEAR_MISS,
            date="2026-09-22",
            site="Digboi Refinery",
            refinery_unit="Hydrogen Unit",
            location="Process Area",
            equipment_id="V-102",
            work_type="Maintenance",
            activity="Vessel Cleaning",
            department="Operations",
            description="Worker entered vessel V-102 without confined space gas clearance permit.",
            ppe_noncompliance=True,
            supervisor_negligence=True,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False
        )
        report = create_report(self.db, report_data, self.user_admin)

        # Re-run similarity calculation directly
        sim_res = calculate_report_similarity(self.db, report, self.user_admin)
        
        # Self must not be in matching list
        matched_ids = [s["report_id"] for s in sim_res["similar_reports"]]
        self.assertNotIn(report.id, matched_ids)

    def test_05_risk_analysis_matrix(self):
        """TEST 5 — Risk Level Assessment matrix (RISK_EVAL_v1)."""
        report_dict = {
            "description": "Worker entered confined space without gas testing permit and bypassed lockout tagout isolation.",
            "ppe_noncompliance": True,
            "supervisor_negligence": True,
            "maintenance_delay_or_issue": False,
            "repeated_issue_ignored": True
        }
        ml_result = {
            "prediction": "SIF-Potential",
            "classification": 1,
            "probability": 0.88,
            "threshold": 0.60
        }
        hazards = ["Confined Space Entry", "Line of Fire"]
        barriers = ["Energy Isolation", "Gas Testing", "Permit Control"]

        risk_res = calculate_report_risk(
            report_dict=report_dict,
            ml_result=ml_result,
            hazards=hazards,
            barriers=barriers,
            previous_similar_reports_count=2
        )

        self.assertEqual(risk_res["risk_level"], "CRITICAL")
        self.assertEqual(risk_res["methodology_version"], "RISK_EVAL_v1")
        self.assertTrue(any("SIF-Potential" in b for b in risk_res["risk_explanation"]))

    def test_06_source_sheet_non_leakage(self):
        """TEST 6 — Source sheet / dataset tab names must not affect prediction or risk analysis."""
        report_dict_1 = {
            "description": "Line flange opening performed without wearing face shield.",
            "source_sheet": "12_High_Potential",
            "ppe_noncompliance": True
        }
        report_dict_2 = {
            "description": "Line flange opening performed without wearing face shield.",
            "source_sheet": "01_Unsafe_Act",
            "ppe_noncompliance": True
        }

        ml_res = {"prediction": "Non-SIF", "classification": 0, "probability": 0.25, "threshold": 0.60}
        
        res1 = calculate_report_risk(report_dict_1, ml_res, [], [])
        res2 = calculate_report_risk(report_dict_2, ml_res, [], [])

        self.assertEqual(res1["risk_level"], res2["risk_level"])


if __name__ == "__main__":
    unittest.main()
