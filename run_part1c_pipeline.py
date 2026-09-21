import os
import json
import time
import joblib
import pandas as pd
import numpy as np

from src.feature_engineering import load_processed_data, create_train_val_test_splits, build_tfidf_vectorizer, EXCLUDED_FEATURES
from src.train import train_candidate_models
from src.evaluate import compute_classification_metrics
from src.predict import load_model, predict_sif

def main():
    print("==================================================")
    print("OIL SIF PRECURSOR DETECTION - PART 1C PIPELINE")
    print("==================================================")

    os.makedirs("models/final_model", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    # 1. Load Processed Data & Train Candidate
    print("\n[STEP 1] Loading Dataset & Training Final Production Model Package...")
    df = load_processed_data()
    train_df, val_df, test_df = create_train_val_test_splits(df)

    # Fit TF-IDF Vectorizer
    tfidf = build_tfidf_vectorizer()
    X_train_text = tfidf.fit_transform(train_df["Near_Miss_Description"].fillna(""))
    X_val_text = tfidf.transform(val_df["Near_Miss_Description"].fillna(""))
    X_test_text = tfidf.transform(test_df["Near_Miss_Description"].fillna(""))

    # Train Final Candidate Model (LogisticRegression_Balanced)
    from sklearn.linear_model import LogisticRegression
    final_model = LogisticRegression(C=1.0, class_weight='balanced', max_iter=1000, random_state=42)
    final_model.fit(X_train_text, train_df["High_Potential_Near_Miss"].values)

    # Evaluate on Val & Test
    val_probs = final_model.predict_proba(X_val_text)[:, 1]
    test_probs = final_model.predict_proba(X_test_text)[:, 1]

    m_val = compute_classification_metrics(val_df["High_Potential_Near_Miss"].values, (val_probs >= 0.60).astype(int), val_probs)
    m_test = compute_classification_metrics(test_df["High_Potential_Near_Miss"].values, (test_probs >= 0.60).astype(int), test_probs)

    print(f"Validation Metrics (Thresh 0.60): SIF Prec = {m_val['sif_precision']}, SIF Rec = {m_val['sif_recall']}, SIF F1 = {m_val['sif_f1']}")
    print(f"Test Metrics (Thresh 0.60):       SIF Prec = {m_test['sif_precision']}, SIF Rec = {m_test['sif_recall']}, SIF F1 = {m_test['sif_f1']}")

    # 2. Save Final Package Artifacts to models/final_model/
    print("\n[STEP 2] Saving Complete Self-Contained Package to models/final_model/...")
    final_dir = "models/final_model"

    joblib.dump(final_model, os.path.join(final_dir, "model.joblib"))
    joblib.dump(tfidf, os.path.join(final_dir, "tfidf_vectorizer.joblib"))

    label_map = {"0": "Non-SIF", "1": "SIF-Potential"}
    with open(os.path.join(final_dir, "label_mapping.json"), "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2)

    feature_cfg = {
        "text_features": ["Near_Miss_Description"],
        "categorical_features": ["Refinery_Unit", "Equipment_ID", "Work_Type", "Department"],
        "numeric_features": ["Previous_Similar_Reports"],
        "boolean_features": ["PPE_NonCompliance", "Supervisor_Negligence", "Maintenance_Delay_or_Issue", "Repeated_Issue_Ignored"],
        "excluded_features": EXCLUDED_FEATURES
    }
    with open(os.path.join(final_dir, "feature_config.json"), "w", encoding="utf-8") as f:
        json.dump(feature_cfg, f, indent=2)

    thresh_cfg = {
        "optimal_threshold": 0.60,
        "default_threshold": 0.50,
        "selection_method": "Validation set SIF F1 score maximization"
    }
    with open(os.path.join(final_dir, "threshold.json"), "w", encoding="utf-8") as f:
        json.dump(thresh_cfg, f, indent=2)

    metadata = {
        "model_version": "sif_model_v1",
        "project": "OIL SIF Precursor Detection Engine",
        "model_type": "LogisticRegression (Balanced L2 Regularized)",
        "feature_config_type": "Configuration A (Text Only TF-IDF)",
        "target_col": "High_Potential_Near_Miss",
        "training_records": len(train_df),
        "validation_records": len(val_df),
        "test_records": len(test_df),
        "random_state": 42,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validation_metrics": m_val,
        "test_metrics": m_test
    }
    with open(os.path.join(final_dir, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # MODEL_CARD.md
    model_card = f"""# SIF Model Card — `sif_model_v1`

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
- **SIF Precision**: `{m_test['sif_precision']}`
- **SIF Recall**: `{m_test['sif_recall']}`
- **SIF F1-Score**: `{m_test['sif_f1']}`
- **ROC-AUC**: `{m_test['roc_auc']}`
- **PR-AUC**: `{m_test['pr_auc']}`

## 6. Human Oversight Requirement
Every prediction includes a mandatory disclaimer:
*"This prediction is an AI safety decision-support score and requires qualified HSE professional review."*
"""
    with open(os.path.join(final_dir, "MODEL_CARD.md"), "w", encoding="utf-8") as f:
        f.write(model_card)

    print("--> Saved models/final_model package artifacts.")

    # 3. Reload Test & Sample Predictions
    print("\n[STEP 3] Testing Saved Artifact Reload & New Report Predictions...")
    model_pkg = load_model(final_dir)

    sample_reports = [
        {
            "Near_Miss_Description": "During pump maintenance, worker started job without confirming that equipment was isolated.",
            "Refinery_Unit": "Utilities",
            "Work_Type": "Maintenance",
            "Department": "Mechanical"
        },
        {
            "Near_Miss_Description": "Welder worked at height without connecting safety harness near gas line.",
            "Refinery_Unit": "Hydrogen Unit",
            "Work_Type": "Hot Work",
            "Department": "Contractor"
        },
        {
            "Near_Miss_Description": "Gas detector gave intermittent readings during confined space entry.",
            "Refinery_Unit": "HCU",
            "Work_Type": "Inspection",
            "Department": "HSE"
        },
        {
            "Near_Miss_Description": "Minor oil weeping observed from valve gland packing during routine rounds.",
            "Refinery_Unit": "Crude Unit",
            "Work_Type": "Routine Operation",
            "Department": "Operations"
        },
        {
            "Near_Miss_Description": "Worker entered process area without safety glasses.",
            "Refinery_Unit": "Offsites",
            "Work_Type": "Routine Operation",
            "Department": "Operations"
        }
    ]

    print("\nSample Report Predictions:")
    for idx, rep in enumerate(sample_reports, 1):
        res = predict_sif(rep, model_package=model_pkg)
        print(f"\nReport #{idx}: {rep['Near_Miss_Description'][:60]}...")
        print(f"  --> Prediction:  {res['prediction']} (Class {res['classification']})")
        print(f"  --> Probability: {res['probability']} (Threshold: {res['threshold']})")
        print(f"  --> Explanation: {res['human_readable_explanation']}")

    # 4. Latency Benchmark
    print("\n[STEP 4] Measuring Prediction Inference Latency...")
    t_start = time.time()
    for _ in range(100):
        predict_sif(sample_reports[0], model_package=model_pkg)
    total_time_ms = (time.time() - t_start) * 1000
    avg_latency_ms = round(total_time_ms / 100, 3)
    print(f"100 Predictions Total Time: {total_time_ms:.2f} ms")
    print(f"Average Inference Latency per Report: {avg_latency_ms} ms")

    # 5. Generate Part 1C Reports
    print("\n[STEP 5] Generating Final Reports (Selection, Evaluation, Limitations)...")
    
    # 5a. final_model_selection.md
    selection_md = f"""# OIL SIF Precursor Detection — Final Model Selection Report (Part 1C)

## Executive Summary
This report documents the selection rationale for the final deployed SIF prediction model package (`sif_model_v1`).

- **Selected Architecture**: `LogisticRegression` with balanced class weights on TF-IDF text features.
- **Model Version**: `sif_model_v1`
- **Saved Package Location**: `models/final_model/`

---

## Selection Rationale & Trade-off Analysis

1. **Text-Only NLP Reliability**: Configuration A (Text Only) avoids dependence on post-investigation or constructed structured fields (`Potential_Consequence`, `Risk_Level`).
2. **Safety-Critical Recall**: Balanced Logistic Regression delivers strong SIF Recall while maintaining an interpretable linear decision boundary.
3. **Low Inference Complexity**: Latency averages `{avg_latency_ms} ms` per report, ideal for real-time backend API scoring in Part 2.
4. **Transparent Explainability**: N-gram coefficients map directly to safety hazard terms (*isolated*, *bypassed*, *harness*, *gas detector*).
"""
    with open("reports/final_model_selection.md", "w", encoding="utf-8") as f:
        f.write(selection_md)

    # 5b. final_model_evaluation.md
    evaluation_md = f"""# OIL SIF Precursor Detection — Final Model Evaluation Report (Part 1C)

## Executive Summary
Evaluation results for `sif_model_v1` on the stratified Validation Set and untouched Test Set.

- **Optimal Decision Threshold**: `0.60`
- **Average Inference Latency**: `{avg_latency_ms} ms`

---

## Metric Breakdown

| Dataset Split | Accuracy | SIF Precision | SIF Recall | SIF F1 | ROC-AUC | PR-AUC | False Negatives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Validation Set** | `{m_val['accuracy']}` | `{m_val['sif_precision']}` | `{m_val['sif_recall']}` | `{m_val['sif_f1']}` | `{m_val['roc_auc']}` | `{m_val['pr_auc']}` | `{m_val['fn']}` |
| **Untouched Test Set** | `{m_test['accuracy']}` | `{m_test['sif_precision']}` | `{m_test['sif_recall']}` | `{m_test['sif_f1']}` | `{m_test['roc_auc']}` | `{m_test['pr_auc']}` | `{m_test['fn']}` |
"""
    with open("reports/final_model_evaluation.md", "w", encoding="utf-8") as f:
        f.write(evaluation_md)

    # 5c. part1c_limitations.md
    limitations_md = """# OIL SIF Precursor Detection — Model Limitations & Guidelines (Part 1C)

## 1. Known Technical Limitations
1. **Dataset Construction Artifacts**: Synthetic text generation pattern in the training dataset where clauses are concatenated.
2. **Vocabulary Boundary**: Novel terminology or regional oilfield jargon not present in training data will receive zero TF-IDF weights.
3. **Decision Threshold Dependence**: The model score is calibrated to threshold 0.60; lowering threshold boosts recall at the expense of precision.

## 2. Operational & Human Oversight Guidelines
- **Decision-Support Only**: Must be paired with HSE professional review.
- **Continuous Monitoring**: Model outputs should be periodically audited against ground-truth incident investigations.
"""
    with open("reports/part1c_limitations.md", "w", encoding="utf-8") as f:
        f.write(limitations_md)

    print("--> Saved reports/final_model_selection.md")
    print("--> Saved reports/final_model_evaluation.md")
    print("--> Saved reports/part1c_limitations.md")

    print("\n==================================================")
    print("PART 1C PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    main()
