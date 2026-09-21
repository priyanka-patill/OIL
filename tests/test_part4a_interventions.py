"""
Comprehensive Unit & Integration Test Suite for Part 4A — Intervention Recommendation Foundation
"""

import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.database.models import (
    User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis,
    InterventionRecommendation, InterventionCategory, InterventionPriority, InterventionStatus
)
from backend.security.auth import create_access_token
from backend.main import app

from backend.services.intervention_recommendation_engine import (
    generate_recommendation_payload, RECOMMENDATION_ENGINE_VERSION
)
from backend.services import intervention_service


class TestPart4AInterventions(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database for testing
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
            site=None,
            department="HSE"
        )
        self.operator = User(
            name="Field Worker",
            email="worker@oil.in",
            password_hash="hashed",
            role=UserRole.HSE_USER,
            site="Duliajan Complex",
            department="Operations"
        )
        self.db.add_all([self.admin, self.operator])
        self.db.commit()

        # Auth Tokens
        self.admin_token = create_access_token(user_id=self.admin.id, email=self.admin.email, role=self.admin.role)
        self.operator_token = create_access_token(user_id=self.operator.id, email=self.operator.email, role=self.operator.role)

        # Seed Test Safety Reports & AI Analysis
        self.report_loto = SafetyReport(
            report_number="OIL-2026-000401",
            report_type=ReportType.UNSAFE_ACT,
            status=ReportStatus.SUBMITTED,
            site="Digboi Refinery",
            location="Compressor Area",
            refinery_unit="AVU-1",
            work_type="Electrical Maintenance",
            department="Electrical",
            equipment_id="P-101A",
            date="2026-02-10",
            description="LOTO padlock missing on circuit breaker CB-4 during pump maintenance work. Electrician was working without zero energy isolation check.",
            ppe_noncompliance=False,
            supervisor_negligence=True,
            maintenance_delay_or_issue=True,
            repeated_issue_ignored=True,
            created_by=self.admin.id,
        )
        self.db.add(self.report_loto)
        self.db.commit()

        self.analysis_loto = AIAnalysis(
            report_id=self.report_loto.id,
            model_version="sif_model_v1",
            prediction="SIF-Potential",
            classification=1,
            probability_or_score=0.88,
            threshold=0.5,
            explanation_json='{"reason": "High severity electrical isolation hazard"}',
            life_saving_rules_json='["Energy Isolation"]',
            hazards_json='["Electrical", "Energy"]',
            barrier_concerns_json='["Energy Isolation"]',
        )
        self.db.add(self.analysis_loto)

        # Seed Confined Space Report
        self.report_cs = SafetyReport(
            report_number="OIL-2026-000402",
            report_type=ReportType.NEAR_MISS,
            status=ReportStatus.SUBMITTED,
            site="Duliajan Complex",
            location="Storage Tank T-42",
            refinery_unit="Tank Farm",
            work_type="Internal Inspection",
            department="Operations",
            date="2026-02-12",
            description="Entrant stepped into diesel storage tank without gas testing certificate. H2S monitor was uncalibrated.",
            ppe_noncompliance=True,
            supervisor_negligence=True,
            maintenance_delay_or_issue=False,
            repeated_issue_ignored=False,
            created_by=self.operator.id,
        )
        self.db.add(self.report_cs)
        self.db.commit()

        self.analysis_cs = AIAnalysis(
            report_id=self.report_cs.id,
            model_version="sif_model_v1",
            prediction="SIF-Potential",
            classification=1,
            probability_or_score=0.92,
            threshold=0.5,
            explanation_json='{"reason": "Toxic gas exposure risk"}',
            life_saving_rules_json='["Confined Space"]',
            hazards_json='["Chemical", "Hazardous Atmosphere"]',
            barrier_concerns_json='["Gas Testing"]',
        )
        self.db.add(self.analysis_cs)
        self.db.commit()

    def test_01_recommendation_engine_loto_rule(self):
        """Verify recommendation engine maps LOTO findings to ENERGY_ISOLATION category."""
        report_dict = {
            "id": self.report_loto.id,
            "report_number": self.report_loto.report_number,
            "description": self.report_loto.description,
            "site": self.report_loto.site,
            "equipment_id": self.report_loto.equipment_id,
            "work_type": self.report_loto.work_type,
            "date": self.report_loto.date,
            "ppe_noncompliance": self.report_loto.ppe_noncompliance,
            "supervisor_negligence": self.report_loto.supervisor_negligence,
            "maintenance_delay_or_issue": self.report_loto.maintenance_delay_or_issue,
            "repeated_issue_ignored": self.report_loto.repeated_issue_ignored,
        }
        ai_dict = {
            "prediction": self.analysis_loto.prediction,
            "life_saving_rules_json": self.analysis_loto.life_saving_rules_json,
            "hazards_json": self.analysis_loto.hazards_json,
            "barrier_concerns_json": self.analysis_loto.barrier_concerns_json,
            "model_version": self.analysis_loto.model_version,
        }
        pattern_dict = {"occurrence_count": 3, "pattern_id": "PAT-001"}
        rec_data = generate_recommendation_payload(report_dict, ai_dict, pattern_data=pattern_dict)
        
        self.assertEqual(rec_data["category"], InterventionCategory.ENERGY_ISOLATION)
        self.assertEqual(rec_data["priority_suggestion"], InterventionPriority.HIGH)
        self.assertIn("Verify Energy Isolation", rec_data["title"])
        self.assertEqual(rec_data["model_version"], "sif_model_v1")
        self.assertEqual(rec_data["methodology_version"], RECOMMENDATION_ENGINE_VERSION)
        self.assertEqual(rec_data["sif_classification"], "SIF-Potential")

    def test_02_recommendation_engine_confined_space(self):
        """Verify recommendation engine maps Confined Space finding to CONFINED_SPACE_CONTROL category."""
        report_dict = {
            "id": self.report_cs.id,
            "report_number": self.report_cs.report_number,
            "description": self.report_cs.description,
            "site": self.report_cs.site,
            "equipment_id": self.report_cs.equipment_id,
            "work_type": self.report_cs.work_type,
            "date": self.report_cs.date,
            "ppe_noncompliance": self.report_cs.ppe_noncompliance,
            "supervisor_negligence": self.report_cs.supervisor_negligence,
            "maintenance_delay_or_issue": self.report_cs.maintenance_delay_or_issue,
            "repeated_issue_ignored": self.report_cs.repeated_issue_ignored,
        }
        ai_dict = {
            "prediction": self.analysis_cs.prediction,
            "life_saving_rules_json": self.analysis_cs.life_saving_rules_json,
            "hazards_json": self.analysis_cs.hazards_json,
            "barrier_concerns_json": self.analysis_cs.barrier_concerns_json,
            "model_version": self.analysis_cs.model_version,
        }
        rec_data = generate_recommendation_payload(report_dict, ai_dict)
        
        self.assertEqual(rec_data["category"], InterventionCategory.CONFINED_SPACE_CONTROL)
        self.assertEqual(rec_data["priority_suggestion"], InterventionPriority.MEDIUM)
        self.assertIn("Confined Space", rec_data["title"])

    def test_03_anti_leakage_audit(self):
        """Mandatory Leakage Protection Audit: Ensure source_sheet and 12_High_Potential have ZERO impact."""
        report_dict = {
            "id": 999,
            "report_number": "OIL-2026-LEAK01",
            "description": "Routine housekeeping issue with loose wooden pallet near walkway.",
            "site": "Digboi Refinery",
            "work_type": "Housekeeping",
            "date": "2026-02-15",
            "ppe_noncompliance": False,
            "supervisor_negligence": False,
            "maintenance_delay_or_issue": False,
            "repeated_issue_ignored": False,
            "source_sheet": "12_High_Potential"  # Potential leakage column!
        }
        ai_dict = {
            "prediction": "Non-SIF-Potential",
            "hazards_json": '["Tripping"]',
            "model_version": "sif_model_v1",
        }
        
        rec_data = generate_recommendation_payload(report_dict, ai_dict)
        
        # Must produce LOW priority, NOT HIGH priority (source_sheet must be ignored completely!)
        self.assertEqual(rec_data["priority_suggestion"], InterventionPriority.LOW)
        self.assertNotEqual(rec_data["category"], InterventionCategory.ENERGY_ISOLATION)
        self.assertEqual(rec_data["sif_classification"], "Non-SIF-Potential")

    def test_04_insufficient_data_handling(self):
        """Verify report with very short description returns INSUFFICIENT_DATA priority or fallback."""
        report_dict = {
            "id": 998,
            "report_number": "OIL-2026-SHORT",
            "description": "Bad valve",  # Under 10 words
            "site": "Digboi Refinery",
            "date": "2026-02-16",
        }
        rec_data = generate_recommendation_payload(report_dict, None)
        self.assertEqual(rec_data["priority_suggestion"], InterventionPriority.LOW)
        self.assertEqual(rec_data["category"], InterventionCategory.OTHER)

    def test_05_service_persistence_and_idempotency(self):
        """Verify service layer persists InterventionRecommendation and prevents duplicate insertions."""
        rec1 = intervention_service.generate_recommendation_for_report(
            db=self.db, report_id=self.report_loto.id, current_user=self.admin
        )
        self.assertIsNotNone(rec1.id)
        self.assertEqual(rec1.status, InterventionStatus.PENDING_HSE_VALIDATION)
        self.assertEqual(rec1.report_id, self.report_loto.id)

        # Trigger second generation call for same report and category
        rec2 = intervention_service.generate_recommendation_for_report(
            db=self.db, report_id=self.report_loto.id, current_user=self.admin
        )
        # Idempotency must return existing record ID, not create a duplicate database row
        self.assertEqual(rec1.id, rec2.id)

    def test_06_api_endpoints_and_json_consistency(self):
        """Verify REST API generation and detail retrieval match database fields."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # POST /api/interventions/generate
        resp = self.client.post("/api/interventions/generate", json={"report_id": self.report_cs.id}, headers=headers)
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertTrue(body["success"])
        data = body["data"]

        self.assertEqual(data["report_id"], self.report_cs.id)
        self.assertEqual(data["category"], "CONFINED_SPACE_CONTROL")
        self.assertEqual(data["status"], "PENDING_HSE_VALIDATION")
        self.assertEqual(data["validation_notice"], "AI-Suggested Intervention — HSE Validation Required")

        # GET /api/interventions/{id}
        inter_id = data["id"]
        get_resp = self.client.get(f"/api/interventions/{inter_id}", headers=headers)
        self.assertEqual(get_resp.status_code, 200)
        get_data = get_resp.json()["data"]
        self.assertEqual(get_data["recommendation_number"], data["recommendation_number"])

        # GET /api/interventions/report/{report_id}
        rep_resp = self.client.get(f"/api/interventions/report/{self.report_cs.id}", headers=headers)
        self.assertEqual(rep_resp.status_code, 200)
        self.assertEqual(len(rep_resp.json()["data"]), 1)

    def test_07_site_level_security_authorization(self):
        """Verify operator restricted to Duliajan cannot view Digboi intervention recommendations."""
        # First generate recommendation for Digboi Refinery report
        rec_digboi = intervention_service.generate_recommendation_for_report(
            db=self.db, report_id=self.report_loto.id, current_user=self.admin
        )

        # Access with operator token (Site = Duliajan Complex)
        op_headers = {"Authorization": f"Bearer {self.operator_token}"}
        resp = self.client.get(f"/api/interventions/{rec_digboi.id}", headers=op_headers)
        self.assertEqual(resp.status_code, 403)

    def test_08_real_database_consistency_check(self):
        """Verify consistency between direct database model query and API response for real data."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        rec = intervention_service.generate_recommendation_for_report(
            db=self.db, report_id=self.report_loto.id, current_user=self.admin
        )

        # DB Direct Query
        db_rec = self.db.query(InterventionRecommendation).filter(InterventionRecommendation.id == rec.id).first()
        self.assertIsNotNone(db_rec)

        # API Query
        api_resp = self.client.get(f"/api/interventions/{rec.id}", headers=headers).json()["data"]

        self.assertEqual(db_rec.recommendation_number, api_resp["recommendation_number"])
        self.assertEqual(db_rec.title, api_resp["title"])
        self.assertEqual(db_rec.category.value, api_resp["category"])
        self.assertEqual(db_rec.priority_suggestion.value, api_resp["priority_suggestion"])
        self.assertEqual(db_rec.sif_classification, api_resp["sif_classification"])


if __name__ == "__main__":
    unittest.main()
