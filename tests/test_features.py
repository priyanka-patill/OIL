import unittest
import pandas as pd
from src.feature_engineering import (
    load_processed_data, create_train_val_test_splits, 
    prepare_feature_matrices, EXCLUDED_FEATURES
)

class TestFeatureEngineering(unittest.TestCase):

    def setUp(self):
        self.df = load_processed_data()

    def test_feature_exclusion_list(self):
        """Crucial test: source_sheet and target proxies MUST be in EXCLUDED_FEATURES."""
        self.assertIn("source_sheet", EXCLUDED_FEATURES)
        self.assertIn("Near_Miss_ID", EXCLUDED_FEATURES)
        self.assertIn("Potential_Consequence", EXCLUDED_FEATURES)
        self.assertIn("Risk_Level", EXCLUDED_FEATURES)

    def test_train_val_test_splits(self):
        train_df, val_df, test_df = create_train_val_test_splits(self.df, train_size=0.70, val_size=0.15, test_size=0.15)
        
        self.assertEqual(len(train_df) + len(val_df) + len(test_df), len(self.df))
        self.assertEqual(len(train_df), 665)
        self.assertEqual(len(val_df), 142)
        self.assertEqual(len(test_df), 143)
        
        # Verify stratification
        self.assertEqual(train_df['High_Potential_Near_Miss'].sum(), 70)
        self.assertEqual(val_df['High_Potential_Near_Miss'].sum(), 15)
        self.assertEqual(test_df['High_Potential_Near_Miss'].sum(), 15)

    def test_prepare_feature_matrices_leakless(self):
        train_df, val_df, test_df = create_train_val_test_splits(self.df)
        matrices = prepare_feature_matrices(train_df, val_df, test_df)
        
        self.assertIn("config_a_text", matrices)
        self.assertIn("config_b_struct", matrices)
        self.assertIn("config_c_combined", matrices)
        
        # Check shapes
        self.assertEqual(matrices["config_a_text"]["X_train"].shape[0], 665)
        self.assertEqual(matrices["config_a_text"]["X_val"].shape[0], 142)
        self.assertEqual(matrices["config_a_text"]["X_test"].shape[0], 143)

if __name__ == "__main__":
    unittest.main()
