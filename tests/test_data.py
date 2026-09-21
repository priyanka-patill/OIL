import unittest
import pandas as pd
from src.data_loader import inspect_workbook, load_raw_dataset
from src.data_cleaning import clean_dataset, MODEL_FEATURE_COLUMNS
from src.data_validation import validate_target

class TestDataLoaderAndValidation(unittest.TestCase):

    def test_inspect_workbook(self):
        profile = inspect_workbook()
        self.assertIn("workbook_filename", profile)
        self.assertEqual(profile["num_sheets"], 13)
        self.assertEqual(profile["total_raw_observation_records"], 950)

    def test_load_raw_dataset(self):
        raw_df, summary_df = load_raw_dataset()
        self.assertEqual(len(raw_df), 950)
        self.assertIn("source_sheet", raw_df.columns)
        self.assertIsNotNone(summary_df)

    def test_validate_target(self):
        raw_df, _ = load_raw_dataset()
        cleaned_df = clean_dataset(raw_df)
        stats = validate_target(cleaned_df)
        
        self.assertTrue(stats["is_binary"])
        self.assertEqual(stats["class_0_count_non_sif"], 850)
        self.assertEqual(stats["class_1_count_sif"], 100)

    def test_source_sheet_exclusion(self):
        """Crucial leakage test: source_sheet must NEVER be in MODEL_FEATURE_COLUMNS."""
        self.assertNotIn("source_sheet", MODEL_FEATURE_COLUMNS)
        self.assertNotIn("Near_Miss_ID", MODEL_FEATURE_COLUMNS)
        self.assertNotIn("Potential_Consequence", MODEL_FEATURE_COLUMNS)
        self.assertNotIn("Risk_Level", MODEL_FEATURE_COLUMNS)

if __name__ == "__main__":
    unittest.main()
