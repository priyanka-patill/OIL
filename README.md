# AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in OIL Unsafe-Act/Unsafe-Condition and Near-Miss Reports

## Project Overview
This repository contains the complete dataset engineering, cleaning, data-leakage auditing, exploratory analysis (**Part 1A**), NLP feature engineering, model training, threshold tuning, and evaluation (**Part 1B**), as well as final model packaging, reusable prediction pipeline, and explainability engine (**Part 1C**) for Oil India Limited (OIL) safety reports analytics.

The objective of Part 1C is to deliver a **self-contained, reloadable, explainable SIF prediction package** (`models/final_model/`) with a clean Python interface (`predict_sif(report)` in `src/predict.py`) that downstream Part 2 backend APIs can consume directly.

---

## Critical Leakage Safeguards & Rules

> [!CRITICAL]
> **“`source_sheet` was retained only for auditing and subgroup analysis and was not used as a machine-learning feature.”**

All 100 SIF (`High_Potential_Near_Miss = True`) records originate from sheet `12_High_Potential`. `source_sheet` and post-investigation fields (`Potential_Consequence`, `Risk_Level`, `Corrective_Action`, `Action_Status`) are strictly excluded from model feature inputs. `predict_sif()` automatically strips these fields if passed in report dictionaries.

---

## Final Production Model Package (`models/final_model/`)

- **Model Version**: `sif_model_v1`
- **Model Architecture**: Logistic Regression with `class_weight='balanced'`, L2 regularization.
- **NLP Feature Pipeline**: TF-IDF Vectorizer (unigrams + bigrams, min_df=2, max_df=0.95, negation preserved).
- **Decision Threshold**: `0.60` (validated optimal SIF F1 threshold).
- **Inference Latency**: `< 1.0 ms` per report prediction.

### Package Artifacts Location

```
models/final_model/
├── model.joblib                 # Trained Logistic Regression classifier
├── tfidf_vectorizer.joblib      # Fitted TF-IDF vectorizer
├── label_mapping.json           # {"0": "Non-SIF", "1": "SIF-Potential"}
├── feature_config.json          # Input feature configuration schema
├── threshold.json              # Operational decision threshold (0.60)
├── model_metadata.json          # Complete versioning & evaluation metadata
├── MODEL_CARD.md                # Detailed model card & human oversight rules
└── README.md                    # Package documentation
```

---

## Prediction Engine API Usage (`src/predict.py`)

### Python Quickstart

```python
from src.predict import load_model, predict_sif

# 1. Load model package artifacts (cached singleton)
model_pkg = load_model("models/final_model")

# 2. Define input report dictionary
new_report = {
    "Near_Miss_Description": "Worker entered process area without safety helmet and bypassed isolation locks during pump overhaul.",
    "Refinery_Unit": "Hydrogen Unit",
    "Equipment_ID": "P-305",
    "Work_Type": "Preventive Maintenance",
    "Department": "Contractor"
}

# 3. Generate prediction with explainability
response = predict_sif(new_report, model_package=model_pkg)
print(response)
```

### Standard Output JSON Schema

```json
{
  "prediction": "SIF-Potential",
  "classification": 1,
  "probability": 0.8421,
  "threshold": 0.60,
  "model_version": "sif_model_v1",
  "explanation": [
    {
      "type": "text_ngram",
      "feature": "without safety",
      "weight": 1.4215,
      "contribution": 0.4215
    },
    {
      "type": "text_ngram",
      "feature": "bypassed",
      "weight": 1.1052,
      "contribution": 0.3512
    }
  ],
  "human_readable_explanation": "Model prediction influenced by key safety-hazard terms: 'without safety, bypassed'.",
  "disclaimer": "This prediction is an AI safety decision-support score and requires qualified HSE professional review.",
  "warnings": []
}
```

---

## Final Performance Summary (Held-Out Test Set)

| Split | SIF Precision | SIF Recall | SIF F1 | Accuracy | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Validation Set** | 0.5714 | 0.5333 | 0.5517 | 0.9085 | 0.9638 | 0.7042 |
| **Untouched Test Set** | 0.5789 | 0.7333 | 0.6471 | 0.9021 | 0.9094 | 0.7014 |

---

## Full Repository Structure

```
ps2/
├── Indian_Refinery_Near_Miss_Datasets.xlsx
├── data/
│   └── processed/
│       ├── cleaned_near_miss_dataset.csv
│       └── cleaned_near_miss_dataset.parquet
├── docs/
│   └── part2_model_interface.md
├── models/
│   ├── candidates/
│   │   └── ConfigA_Text_LogisticRegression_Balanced.joblib
│   └── final_model/
│       ├── model.joblib
│       ├── tfidf_vectorizer.joblib
│       ├── label_mapping.json
│       ├── feature_config.json
│       ├── threshold.json
│       ├── model_metadata.json
│       └── MODEL_CARD.md
├── reports/
│   ├── dataset_profile.json
│   ├── data_quality_report.md
│   ├── leakage_audit.md
│   ├── eda_report.md
│   ├── false_negative_analysis.md
│   ├── leakage_model_stress_test.md
│   ├── model_comparison.md
│   ├── model_comparison.csv
│   ├── final_model_selection.md
│   ├── final_model_evaluation.md
│   ├── part1c_limitations.md
│   └── figures/
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── data_cleaning.py
│   ├── data_validation.py
│   ├── leakage_audit.py
│   ├── eda.py
│   ├── feature_engineering.py
│   ├── train.py
│   ├── evaluate.py
│   ├── threshold_analysis.py
│   ├── explain.py
│   └── predict.py
├── notebooks/
│   ├── 01_data_understanding.ipynb ... 08_error_analysis.ipynb
├── tests/
│   ├── test_data.py
│   ├── test_cleaning.py
│   ├── test_features.py
│   ├── test_training.py
│   ├── test_evaluation.py
│   ├── test_prediction.py
│   ├── test_model_reload.py
│   ├── test_feature_schema.py
│   ├── test_explainability.py
│   ├── test_edge_cases.py
│   └── test_model_integrity.py
├── run_part1a.py
├── run_part1b_pipeline.py
├── run_part1c_pipeline.py
├── requirements.txt
└── README.md
```

---

## How to Execute Pipelines & Tests

### 1. Execute Master Part 1C Pipeline
```powershell
python run_part1c_pipeline.py
```

### 2. Execute Complete Test Suite (38 Unit & Integration Tests)
```powershell
# Run Part 1 & Part 2 Backend Tests
python -m unittest discover -s tests -p "test_*.py"
```

---

## Part 2A Backend Server Setup & Testing

### 1. Seed Database with Demo Accounts
```powershell
python backend/seed.py
```
Seeds `data/app.db` with demo accounts (`user@oil.in`, `manager@oil.in`, `admin@oil.in`, Password: `Password123!`) and 3 initial safety reports.

### 2. Start FastAPI Backend Server
```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Specs (Swagger): `http://localhost:8000/docs`
- Redoc API Documentation: `http://localhost:8000/redoc`

### 3. Backend Architecture Documentation
Detailed schema definitions, authentication flow, and RBAC rules are documented in [`docs/part2a_backend.md`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/docs/part2a_backend.md).

