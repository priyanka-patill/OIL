import unittest
from src.predict import load_model, generate_explanation, predict_sif

class TestExplainability(unittest.TestCase):

    def setUp(self):
        self.pkg = load_model("models/final_model")

    def test_generate_explanation(self):
        text = "Worker removed gloves during maintenance and bypassed LOTO isolation."
        explanations, readable = generate_explanation(text, self.pkg["tfidf_vectorizer"], self.pkg["model"])

        self.assertIsInstance(explanations, list)
        self.assertIsInstance(readable, str)
        self.assertTrue(len(readable) > 0)
        
        if len(explanations) > 0:
            item = explanations[0]
            self.assertIn("feature", item)
            self.assertIn("weight", item)
            self.assertIn("contribution", item)

if __name__ == "__main__":
    unittest.main()
