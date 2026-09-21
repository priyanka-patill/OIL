import unittest
from src.predict import predict_sif

class TestEdgeCases(unittest.TestCase):

    def test_empty_description(self):
        rep = {"Near_Miss_Description": ""}
        res = predict_sif(rep)
        
        self.assertIn("prediction", res)
        self.assertTrue(any("empty or missing" in w for w in res["warnings"]))

    def test_none_description(self):
        rep = {"Near_Miss_Description": None}
        res = predict_sif(rep)
        
        self.assertIn("prediction", res)

    def test_missing_optional_fields(self):
        rep = {"Near_Miss_Description": "Hydrocarbon leakage from flange."}
        res = predict_sif(rep)
        
        self.assertIn("prediction", res)
        self.assertIn("probability", res)

    def test_unknown_categorical_values(self):
        rep = {
            "Near_Miss_Description": "Hydrocarbon leakage from flange.",
            "Refinery_Unit": "UNSEEN_UNIT_99",
            "Equipment_ID": "EQ_UNKNOWN"
        }
        res = predict_sif(rep)
        
        self.assertIn("prediction", res)
        self.assertIn("probability", res)

if __name__ == "__main__":
    unittest.main()
