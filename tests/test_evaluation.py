import unittest
import numpy as np
import os
import joblib
from src.evaluate import compute_classification_metrics
from src.threshold_analysis import perform_threshold_analysis

class TestEvaluation(unittest.TestCase):

    def test_compute_classification_metrics(self):
        y_true = np.array([0, 0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1, 0])
        y_prob = np.array([0.1, 0.2, 0.6, 0.9, 0.4])
        
        metrics = compute_classification_metrics(y_true, y_pred, y_prob)
        
        self.assertEqual(metrics["tp"], 1)
        self.assertEqual(metrics["fn"], 1)
        self.assertEqual(metrics["fp"], 1)
        self.assertEqual(metrics["tn"], 2)
        self.assertEqual(metrics["accuracy"], 0.6)
        self.assertEqual(metrics["sif_precision"], 0.5)
        self.assertEqual(metrics["sif_recall"], 0.5)

    def test_perform_threshold_analysis(self):
        y_true = np.array([0]*90 + [1]*10)
        y_prob = np.linspace(0, 1, 100)
        
        df_thresh, best_metrics = perform_threshold_analysis(y_true, y_prob, model_name="TestModel")
        
        self.assertEqual(len(df_thresh), 19)
        self.assertIn("sif_precision", best_metrics)
        self.assertIn("sif_recall", best_metrics)

if __name__ == "__main__":
    unittest.main()
