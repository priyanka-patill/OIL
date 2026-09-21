import unittest
import os
import joblib
from src.predict import load_model, predict_sif, _MODEL_CACHE

class TestModelReload(unittest.TestCase):

    def test_model_reload_consistency(self):
        # Clear global model cache
        _MODEL_CACHE.clear()
        
        # Load fresh model package from disk
        pkg = load_model("models/final_model")
        self.assertIsNotNone(pkg["model"])
        self.assertIsNotNone(pkg["tfidf_vectorizer"])

        sample_report = {
            "Near_Miss_Description": "Lifting operation continued despite unsafe weather conditions and missing permit."
        }

        res1 = predict_sif(sample_report, model_package=pkg)
        
        # Reload second time
        pkg2 = load_model("models/final_model")
        res2 = predict_sif(sample_report, model_package=pkg2)

        self.assertEqual(res1["classification"], res2["classification"])
        self.assertAlmostEqual(res1["probability"], res2["probability"], places=4)
        self.assertEqual(res1["prediction"], res2["prediction"])

if __name__ == "__main__":
    unittest.main()
