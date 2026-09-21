import unittest
import pandas as pd
from src.data_cleaning import clean_text_description, normalize_boolean, clean_dataset

class TestDataCleaning(unittest.TestCase):

    def test_clean_text_description_negation_preservation(self):
        # Verify negation words are preserved intact
        sample_text = "  LOTO NOT completed and worker worked without safety helmet  "
        cleaned = clean_text_description(sample_text)
        
        self.assertIn("NOT", cleaned)
        self.assertIn("without", cleaned)
        self.assertEqual(cleaned, "LOTO NOT completed and worker worked without safety helmet")

    def test_normalize_boolean(self):
        self.assertTrue(normalize_boolean(True))
        self.assertTrue(normalize_boolean("True"))
        self.assertTrue(normalize_boolean("1"))
        self.assertTrue(normalize_boolean("Yes"))
        
        self.assertFalse(normalize_boolean(False))
        self.assertFalse(normalize_boolean("False"))
        self.assertFalse(normalize_boolean("0"))
        self.assertFalse(normalize_boolean("No"))

    def test_clean_dataset_target_binary(self):
        raw_data = {
            "Near_Miss_ID": ["01_P-001", "12_H-001"],
            "Near_Miss_Description": ["Worker without helmet", "LOTO bypassed"],
            "PPE_NonCompliance": ["True", "False"],
            "High_Potential_Near_Miss": [False, True],
            "Previous_Similar_Reports": ["2", "0"],
            "Date": ["2025-10-16", "2025-08-27"],
            "source_sheet": ["01_PPE_NonCompliance", "12_High_Potential"]
        }
        df = pd.DataFrame(raw_data)
        cleaned = clean_dataset(df)
        
        self.assertEqual(cleaned["High_Potential_Near_Miss"].tolist(), [0, 1])
        self.assertEqual(cleaned["PPE_NonCompliance"].tolist(), [True, False])
        self.assertEqual(cleaned["Previous_Similar_Reports"].tolist(), [2, 0])

if __name__ == "__main__":
    unittest.main()
