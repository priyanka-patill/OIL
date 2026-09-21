# OIL SIF Precursor Detection — Model Limitations & Guidelines (Part 1C)

## 1. Known Technical Limitations
1. **Dataset Construction Artifacts**: Synthetic text generation pattern in the training dataset where clauses are concatenated.
2. **Vocabulary Boundary**: Novel terminology or regional oilfield jargon not present in training data will receive zero TF-IDF weights.
3. **Decision Threshold Dependence**: The model score is calibrated to threshold 0.60; lowering threshold boosts recall at the expense of precision.

## 2. Operational & Human Oversight Guidelines
- **Decision-Support Only**: Must be paired with HSE professional review.
- **Continuous Monitoring**: Model outputs should be periodically audited against ground-truth incident investigations.
