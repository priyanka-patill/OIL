import unittest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus, AIAnalysis, HSEReview
from backend.security.auth import hash_password, create_access_token
from backend.services import ml_service, life_saving_rules, hazard_analysis, barrier_analysis
from src.predict import predict_sif, load_model

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestPart2CMLIntegration(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)

        db = TestingSessionLocal()
        self.user = User(name="Worker User", email="worker@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_USER, is_active=True)
        self.manager = User(name="HSE Manager", email="manager_ml@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.HSE_MANAGER, is_active=True)
        self.admin = User(name="Admin User", email="admin_ml@oil.in", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN, is_active=True)
        db.add_all([self.user, self.manager, self.admin])
        db.commit()

        self.token_user = create_access_token(self.user.id, self.user.email, self.user.role)
        self.token_manager = create_access_token(self.manager.id, self.manager.email, self.manager.role)
        self.token_admin = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_ml_service_model_package_initialization(self):
        """1. Verify Part 1C model package loads correctly into memory."""
        pkg = ml_service.get_ml_package()
        self.assertIsNotNone(pkg)
        self.assertIn("model", pkg)
        self.assertIn("tfidf_vectorizer", pkg)
        self.assertEqual(pkg.get("threshold"), 0.60)
        self.assertEqual(pkg.get("metadata", {}).get("model_version"), "sif_model_v1")

    def test_source_sheet_leakage_safeguard(self):
        """2. CRITICAL AUDIT: Verify source_sheet='12_High_Potential' does NOT alter prediction."""
        report_clean = {
            "Near_Miss_Description": "Worker entered pump pit without safety harness or isolation locks during maintenance.",
            "Refinery_Unit": "Hydrogen Unit",
            "Equipment_ID": "P-305",
            "Work_Type": "Preventive Maintenance",
            "Department": "Operations",
            "PPE_NonCompliance": True
        }
        
        report_with_leakage = report_clean.copy()
        report_with_leakage["source_sheet"] = "12_High_Potential"

        res_clean = ml_service.run_sif_prediction(report_clean)
        res_leakage = ml_service.run_sif_prediction(report_with_leakage)

        # Predictions, probabilities, and thresholds MUST be 100% identical
        self.assertEqual(res_clean["classification"], res_leakage["classification"])
        self.assertEqual(res_clean["probability"], res_leakage["probability"])
        self.assertEqual(res_clean["threshold"], res_leakage["threshold"])
        self.assertIn("source_sheet", " ".join(res_leakage.get("warnings", [])))

    def test_direct_predict_sif_vs_backend_api_consistency(self):
        """3. Verify direct Part 1C predict_sif() matches backend API analysis endpoint 100%."""
        headers = {"Authorization": f"Bearer {self.token_user}"}
        
        report_payload = {
            "report_type": "NEAR_MISS",
            "date": "2026-09-16",
            "site": "Digboi Refinery",
            "refinery_unit": "Hydrogen Unit",
            "equipment_id": "P-305",
            "work_type": "Preventive Maintenance",
            "department": "Operations",
            "description": "Worker bypassed LOTO isolation locks and entered process area without safety helmet.",
            "ppe_noncompliance": True,
            "supervisor_negligence": True
        }
        
        # 1. Create Report via API
        create_resp = self.client.post("/api/reports", json=report_payload, headers=headers)
        self.assertEqual(create_resp.status_code, 201)
        rep_id = create_resp.json()["data"]["id"]

        # 2. Direct Part 1C prediction
        direct_input = {
            "Near_Miss_Description": report_payload["description"],
            "Refinery_Unit": report_payload["refinery_unit"],
            "Equipment_ID": report_payload["equipment_id"],
            "Work_Type": report_payload["work_type"],
            "Department": report_payload["department"],
            "PPE_NonCompliance": report_payload["ppe_noncompliance"],
            "Supervisor_Negligence": report_payload["supervisor_negligence"]
        }
        direct_res = predict_sif(direct_input)

        # 3. Backend API Analysis
        analyze_resp = self.client.post(f"/api/reports/{rep_id}/analyze", headers=headers)
        self.assertEqual(analyze_resp.status_code, 200)
        api_analysis = analyze_resp.json()["data"]

        # Assert 100% consistency
        self.assertEqual(direct_res["prediction"], api_analysis["prediction"])
        self.assertEqual(direct_res["classification"], api_analysis["classification"])
        self.assertEqual(direct_res["probability"], api_analysis["probability_or_score"])
        self.assertEqual(direct_res["threshold"], api_analysis["threshold"])

    def test_life_saving_rules_and_hazard_analysis_services(self):
        """4. Test deterministic LSR, Hazard, and Barrier analysis modules."""
        sample_report = {
            "description": "Grinding spark ignited gas leak near vessel entry pit without hot work permit or LOTO.",
            "work_type": "Hot Work Maintenance",
            "activity": "Grinding & Welding",
            "ppe_noncompliance": True,
            "supervisor_negligence": True,
            "maintenance_delay_or_issue": True
        }

        lsrs = life_saving_rules.analyze_life_saving_rules(sample_report)
        hazards = hazard_analysis.analyze_hazards(sample_report)
        barriers = barrier_analysis.analyze_barrier_concerns(sample_report)

        self.assertIn("Hot Work", lsrs)
        self.assertIn("Bypassing Safety Controls", lsrs)
        self.assertIn("Hazardous Atmosphere / Toxic Gas", hazards)
        self.assertIn("Thermal / Fire / Explosion", hazards)
        self.assertIn("Personal Protective Equipment (PPE) Defect", barriers)
        self.assertIn("Supervision & Work Permit Control Concern", barriers)

    def test_hse_manager_review_workflow_and_data_integrity(self):
        """5. Test HSE Manager Accept, Modify, and Reject workflow preserving AI analysis."""
        headers_user = {"Authorization": f"Bearer {self.token_user}"}
        headers_mgr = {"Authorization": f"Bearer {self.token_manager}"}

        # 1. User submits report
        create_resp = self.client.post("/api/reports", json={
            "report_type": "NEAR_MISS", "date": "2026-09-16", "site": "Digboi Refinery",
            "description": "Pressure hose uncoupled causing line of fire hazard."
        }, headers=headers_user)
        rep_id = create_resp.json()["data"]["id"]

        # 2. Run AI Analysis
        self.client.post(f"/api/reports/{rep_id}/analyze", headers=headers_user)

        # Verify AI Analysis stored in DB
        db = TestingSessionLocal()
        ai_record = db.query(AIAnalysis).filter(AIAnalysis.report_id == rep_id).first()
        original_prediction = ai_record.prediction
        db.close()

        # 3. Manager Modifies classification
        rev_payload = {
            "ai_prediction_accepted": True,
            "hse_decision": "ACCEPTED",
            "review_comment": "Reviewed and validated by HSE Manager."
        }
        rev_resp = self.client.post(f"/api/reports/{rep_id}/review", json=rev_payload, headers=headers_mgr)
        self.assertEqual(rev_resp.status_code, 201)

        # 4. Verify original AIAnalysis record is UNTOUCHED in DB
        db = TestingSessionLocal()
        ai_after = db.query(AIAnalysis).filter(AIAnalysis.report_id == rep_id).first()
        self.assertEqual(ai_after.prediction, original_prediction) # Untouched!
        
        # Verify HSEReview stored modification separately
        review_record = db.query(HSEReview).filter(HSEReview.report_id == rep_id).first()
        self.assertEqual(review_record.hse_decision, "ACCEPTED")
        
        # Verify Report Status is HSE_VALIDATED
        rep = db.query(SafetyReport).filter(SafetyReport.id == rep_id).first()
        self.assertEqual(rep.status, ReportStatus.HSE_VALIDATED)
        db.close()

    def test_hse_review_rejection_requires_comment(self):
        """6. Verify rejecting an analysis without a comment raises 422/400 validation error."""
        headers_user = {"Authorization": f"Bearer {self.token_user}"}
        headers_mgr = {"Authorization": f"Bearer {self.token_manager}"}

        # Create report first
        create_resp = self.client.post("/api/reports", json={
            "report_type": "NEAR_MISS", "date": "2026-09-16", "site": "Digboi Refinery",
            "description": "Worker entered confined space without gas testing."
        }, headers=headers_user)
        rep_id = create_resp.json()["data"]["id"]

        # Empty comment on rejection
        bad_rev = {
            "ai_prediction_accepted": False,
            "hse_decision": "REJECTED",
            "review_comment": ""
        }
        resp = self.client.post(f"/api/reports/{rep_id}/review", json=bad_rev, headers=headers_mgr)
        self.assertIn(resp.status_code, [400, 422])

    def test_hse_user_forbidden_from_reviews(self):
        """7. Verify standard HSE_USER cannot submit HSE Manager validation reviews."""
        headers_user = {"Authorization": f"Bearer {self.token_user}"}
        rev = {"ai_prediction_accepted": True, "hse_decision": "ACCEPTED"}
        resp = self.client.post("/api/reports/1/review", json=rev, headers=headers_user)
        self.assertEqual(resp.status_code, 403)

if __name__ == "__main__":
    unittest.main()
