"""
Part 3E — Safety Intelligence Dashboard Integration Tests

Verifies backend API integration, global filter propagation, auditability,
and strict anti-leakage constraints (zero source_sheet and zero 12_High_Potential influence).
"""

import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.database import Base, get_db
from backend.database.models import User, SafetyReport, AIAnalysis, HSEReview, UserRole
from backend.security.auth import create_access_token


class TestPart3ESafetyIntelligenceDashboard(unittest.TestCase):
    def setUp(self):
        # Create in-memory SQLite database
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
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

        # Create test users
        self.user = User(
            email="hse_user@oilindia.in",
            password_hash="hashed_password",
            name="HSE User",
            role=UserRole.HSE_USER,
            site="Digboi Refinery",
            is_active=True,
        )
        self.manager = User(
            email="manager@oilindia.in",
            password_hash="hashed_password",
            name="HSE Manager",
            role=UserRole.HSE_MANAGER,
            site=None,
            is_active=True,
        )
        self.db.add(self.user)
        self.db.add(self.manager)
        self.db.commit()
        self.db.refresh(self.user)
        self.db.refresh(self.manager)

        self.user_token = create_access_token(self.user.id, self.user.email, self.user.role)
        self.manager_token = create_access_token(self.manager.id, self.manager.email, self.manager.role)

        # Populate sample reports for Part 3E verification
        reports_data = [
            {
                "report_number": "OIL-2026-000001",
                "site": "Digboi Refinery",
                "refinery_unit": "HCU",
                "department": "Maintenance",
                "work_type": "Electrical Isolation",
                "equipment_id": "P-101A",
                "location": "Pump House 1",
                "report_type": "UNSAFE_ACT",
                "description": "Electrician found working without LOTO padlock applied on feeder breaker panel.",
                "date": "2026-03-01",
                "created_by": self.user.id,
            },
            {
                "report_number": "OIL-2026-000002",
                "site": "Digboi Refinery",
                "refinery_unit": "HCU",
                "department": "Maintenance",
                "work_type": "Electrical Isolation",
                "equipment_id": "P-101A",
                "location": "Pump House 1",
                "report_type": "NEAR_MISS",
                "description": "Feeder breaker operated while maintenance crew was servicing motor cable box.",
                "date": "2026-03-05",
                "created_by": self.user.id,
            },
            {
                "report_number": "OIL-2026-000003",
                "site": "Guwahati Refinery",
                "refinery_unit": "CDU",
                "department": "Operations",
                "work_type": "Confined Space Entry",
                "equipment_id": "V-201",
                "location": "Vessel Bay",
                "report_type": "UNSAFE_CONDITION",
                "description": "Gas detector alarm ignored prior to vessel inspection entry.",
                "date": "2026-03-10",
                "created_by": self.user.id,
            },
        ]

        for r_dict in reports_data:
            rep = SafetyReport(**r_dict)
            self.db.add(rep)
        self.db.commit()

        # Add AI analysis and HSE review
        ai1 = AIAnalysis(
            report_id=1,
            model_version="sif_model_v1",
            prediction="SIF-Potential",
            classification=1,
            probability_or_score=0.85,
            threshold=0.6,
            life_saving_rules_json='["Energy Isolation"]',
            barrier_concerns_json='["Energy Isolation"]',
        )
        ai2 = AIAnalysis(
            report_id=2,
            model_version="sif_model_v1",
            prediction="SIF-Potential",
            classification=1,
            probability_or_score=0.92,
            threshold=0.6,
            life_saving_rules_json='["Energy Isolation"]',
            barrier_concerns_json='["Energy Isolation"]',
        )
        ai3 = AIAnalysis(
            report_id=3,
            model_version="sif_model_v1",
            prediction="Non-SIF-Potential",
            classification=0,
            probability_or_score=0.15,
            threshold=0.6,
            life_saving_rules_json='["Atmospheric Testing"]',
            barrier_concerns_json='["Atmospheric Testing"]',
        )
        self.db.add(ai1)
        self.db.add(ai2)
        self.db.add(ai3)

        rev1 = HSEReview(
            report_id=1,
            reviewer_id=self.manager.id,
            ai_prediction_accepted=True,
            hse_decision="ACCEPTED",
            review_comment="Confirmed LOTO protocol bypass.",
        )
        self.db.add(rev1)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        app.dependency_overrides.clear()

    def test_01_density_endpoint(self):
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        res = self.client.get("/api/analytics/density", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("density_metrics", data)
        metrics = data["density_metrics"]
        self.assertIn("total_reports", metrics)
        self.assertIn("eligible_analyzed_reports", metrics)
        self.assertEqual(metrics["total_reports"], 3)
        self.assertEqual(metrics["eligible_analyzed_reports"], 3)

    def test_02_recurring_patterns_endpoint(self):
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        res = self.client.get("/api/analytics/patterns?min_support=2", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("patterns", data)
        self.assertGreaterEqual(len(data["patterns"]), 1)

    def test_03_barrier_analytics_and_bdi(self):
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        b_res = self.client.get("/api/analytics/barriers", headers=headers)
        self.assertEqual(b_res.status_code, 200)

        bdi_res = self.client.get("/api/analytics/bdi", headers=headers)
        self.assertEqual(bdi_res.status_code, 200)
        bdi_data = bdi_res.json()
        self.assertIn("bdi_methodology_version", bdi_data)
        self.assertEqual(bdi_data["bdi_methodology_version"], "BDI_v1")

    def test_04_escalation_and_priority_endpoints(self):
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        esc_res = self.client.get("/api/analytics/escalation?dimension=equipment_id", headers=headers)
        self.assertEqual(esc_res.status_code, 200)

        pri_res = self.client.get("/api/analytics/priorities?dimension=equipment_id", headers=headers)
        self.assertEqual(pri_res.status_code, 200)
        pri_data = pri_res.json()
        self.assertIn("priority_methodology_version", pri_data)
        self.assertEqual(pri_data["priority_methodology_version"], "PRI_v1")

    def test_05_anti_leakage_audit(self):
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        endpoints = [
            "/api/analytics/density",
            "/api/analytics/patterns",
            "/api/analytics/barriers",
            "/api/analytics/bdi",
            "/api/analytics/escalation",
            "/api/analytics/priorities",
        ]
        for ep in endpoints:
            res = self.client.get(ep, headers=headers)
            content_str = res.text
            self.assertNotIn("source_sheet", content_str)
            self.assertNotIn("12_High_Potential", content_str)

    def test_06_authorization_enforcement(self):
        headers = {"Authorization": f"Bearer {self.user_token}"}
        res = self.client.get("/api/analytics/density", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("density_metrics", data)
        # Digboi Refinery user should see 2 reports
        self.assertEqual(data["density_metrics"]["total_reports"], 2)


if __name__ == "__main__":
    unittest.main()
