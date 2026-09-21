import unittest
import os
from src.predict import load_model, predict_sif

class TestPrediction(unittest.TestCase):

    def setUp(self):
        self.model_dir = "models/final_model"
        self.sample_report = {
            "Near_Miss_Description": "Worker entered process area without safety helmet and bypassed isolation locks during pump overhaul.",
            "Refinery_Unit": "Hydrogen Unit",
            "Equipment_ID": "P-305",
            "Work_Type": "Preventive Maintenance",
            "Department": "Contractor"
        }

    def test_predict_sif_valid_output(self):
        result = predict_sif(self.sample_report, model_dir=self.model_dir)
        
        self.assertIn("prediction", result)
        self.assertIn("classification", result)
        self.assertIn("probability", result)
        self.assertIn("threshold", result)
        self.assertIn("model_version", result)
        self.assertIn("explanation", result)
        self.assertIn("human_readable_explanation", result)
        
        self.assertIn(result["classification"], [0, 1])
        self.assertIn(result["prediction"], ["Non-SIF", "SIF-Potential"])
        self.assertTrue(0.0 <= result["probability"] <= 1.0)
        self.assertEqual(result["model_version"], "sif_model_v1")

if __name__ == "__main__":
    unittest.main()
