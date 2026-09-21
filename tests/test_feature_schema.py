import unittest
from src.predict import validate_report, predict_sif

class TestFeatureSchema(unittest.TestCase):

    def test_source_sheet_and_leakage_stripping(self):
        dirty_report = {
            "Near_Miss_Description": "Gas detector gave intermittent readings.",
            "source_sheet": "12_High_Potential",
            "Potential_Consequence": "Explosion with multiple potential fatalities",
            "Risk_Level": "Critical",
            "Corrective_Action": "Replaced unit",
            "Action_Status": "Closed"
        }

        clean_rep, warnings = validate_report(dirty_report)
        
        self.assertNotIn("source_sheet", clean_rep)
        self.assertNotIn("Potential_Consequence", clean_rep)
        self.assertNotIn("Risk_Level", clean_rep)
        self.assertTrue(any("Excluded leakage field" in w for w in warnings))

    def test_predict_sif_ignores_source_sheet(self):
        report1 = {"Near_Miss_Description": "Worker worked at height without harness."}
        report2 = {"Near_Miss_Description": "Worker worked at height without harness.", "source_sheet": "12_High_Potential"}

        res1 = predict_sif(report1)
        res2 = predict_sif(report2)

        self.assertEqual(res1["classification"], res2["classification"])
        self.assertEqual(res1["probability"], res2["probability"])

if __name__ == "__main__":
    unittest.main()
