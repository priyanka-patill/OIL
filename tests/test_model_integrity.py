import unittest
import os
import json

class TestModelIntegrity(unittest.TestCase):

    def setUp(self):
        self.model_dir = "models/final_model"

    def test_package_files_exist(self):
        expected_files = [
            "model.joblib",
            "tfidf_vectorizer.joblib",
            "label_mapping.json",
            "feature_config.json",
            "threshold.json",
            "model_metadata.json",
            "MODEL_CARD.md"
        ]
        for f in expected_files:
            path = os.path.join(self.model_dir, f)
            self.assertTrue(os.path.exists(path), f"Missing package artifact {f}")

    def test_metadata_structure(self):
        meta_path = os.path.join(self.model_dir, "model_metadata.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.assertEqual(meta["model_version"], "sif_model_v1")
        self.assertIn("validation_metrics", meta)
        self.assertIn("test_metrics", meta)

if __name__ == "__main__":
    unittest.main()
