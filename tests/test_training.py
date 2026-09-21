import unittest
import numpy as np
import pandas as pd
from src.feature_engineering import load_processed_data, create_train_val_test_splits, prepare_feature_matrices
from src.train import MajorityClassBaseline, FourFactorRuleBaseline, train_candidate_models

class TestTraining(unittest.TestCase):

    def setUp(self):
        self.df = load_processed_data()
        self.train_df, self.val_df, self.test_df = create_train_val_test_splits(self.df)
        self.matrices = prepare_feature_matrices(self.train_df, self.val_df, self.test_df)

    def test_majority_class_baseline(self):
        b1 = MajorityClassBaseline()
        b1.fit(self.matrices["config_a_text"]["X_train"], self.matrices["y_train"])
        preds = b1.predict(self.matrices["config_a_text"]["X_val"])
        
        self.assertEqual(len(preds), 142)
        self.assertTrue(np.all(preds == 0))

    def test_four_factor_rule_baseline(self):
        b2 = FourFactorRuleBaseline()
        preds = b2.predict_from_df(self.val_df)
        
        self.assertEqual(len(preds), 142)
        # Verify binary output
        self.assertTrue(set(preds).issubset({0, 1}))

    def test_train_candidate_models(self):
        models = train_candidate_models(
            self.matrices["config_a_text"]["X_train"], 
            self.matrices["y_train"], 
            "config_a_text"
        )
        self.assertIn("LogisticRegression_Balanced", models)
        self.assertIn("LinearSVC_Calibrated", models)
        
        lr = models["LogisticRegression_Balanced"]
        preds = lr.predict(self.matrices["config_a_text"]["X_val"])
        probs = lr.predict_proba(self.matrices["config_a_text"]["X_val"])
        
        self.assertEqual(len(preds), 142)
        self.assertEqual(probs.shape, (142, 2))

if __name__ == "__main__":
    unittest.main()
