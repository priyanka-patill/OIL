# SIF Model Card — `sif_model_v1`

## 1. Model Purpose
This model is designed for Oil India Limited (OIL) as a **Safety Decision-Support Engine** to flag Serious Injury & Fatality (SIF) Precursors in near-miss and unsafe-act/condition text reports.

## 2. Intended Use
- Automated preliminary screening of incoming safety observation text reports.
- Prioritizing high-risk reports for urgent HSE intervention.

## 3. NOT Intended Use
- **Not an Autonomous Safety Decision-Maker**: Must not be used to replace human HSE inspection or approve work permits automatically.
- **Not a Legal / Causal Determination Tool**: Predictions are statistical precursor probabilities, not guaranteed accident forecasts.

## 4. Model Architecture & Parameters
- **Classifier**: Logistic Regression with `class_weight='balanced'`, `C=1.0`, L2 regularization.
- **NLP Vectorizer**: TF-IDF (unigrams + bigrams, min_df=2, max_df=0.95, negation preserved).
- **Decision Threshold**: `0.60` (Validation F1 max tuned).

## 5. Performance Metrics (Held-Out Test Set)
- **SIF Precision**: `0.5789`
- **SIF Recall**: `0.7333`
- **SIF F1-Score**: `0.6471`
- **ROC-AUC**: `0.9094`
- **PR-AUC**: `0.7014`

## 6. Human Oversight Requirement
Every prediction includes a mandatory disclaimer:
*"This prediction is an AI safety decision-support score and requires qualified HSE professional review."*
