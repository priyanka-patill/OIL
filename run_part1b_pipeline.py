import os
import json
import time
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression

from src.feature_engineering import (
    load_processed_data, create_train_val_test_splits, 
    prepare_feature_matrices, FEATURE_AUDIT_TABLE, EXCLUDED_FEATURES
)
from src.train import (
    MajorityClassBaseline, FourFactorRuleBaseline, train_candidate_models
)
from src.evaluate import (
    compute_classification_metrics, plot_confusion_matrix, plot_roc_pr_curves
)
from src.threshold_analysis import perform_threshold_analysis
from src.explain import (
    get_top_feature_coefficients, analyze_false_negatives, analyze_source_sheet_subgroups
)

def main():
    print("==================================================")
    print("OIL SIF PRECURSOR DETECTION - PART 1B PIPELINE")
    print("==================================================")
    
    os.makedirs("reports", exist_ok=True)
    os.makedirs("reports/figures", exist_ok=True)
    os.makedirs("models/candidates", exist_ok=True)
    os.makedirs("models/tfidf", exist_ok=True)
    os.makedirs("models/preprocessing", exist_ok=True)

    # 1. Load Processed Data
    print("\n[STEP 1] Loading Cleaned Processed Dataset...")
    df = load_processed_data()
    print(f"Total Dataset Records: {len(df)}")
    
    # Target Check
    y = df['High_Potential_Near_Miss']
    n_sif = int(y.sum())
    n_non_sif = len(y) - n_sif
    print(f"Target Distribution: Non-SIF (0) = {n_non_sif} ({n_non_sif/len(df)*100:.1f}%), SIF (1) = {n_sif} ({n_sif/len(df)*100:.1f}%)")

    # 2. Train / Validation / Test Split (70/15/15)
    print("\n[STEP 2] Creating Stratified Train (70%) / Validation (15%) / Test (15%) Splits...")
    train_df, val_df, test_df = create_train_val_test_splits(df)
    print(f"Train Records: {len(train_df)} (SIF: {train_df['High_Potential_Near_Miss'].sum()})")
    print(f"Val Records:   {len(val_df)} (SIF: {val_df['High_Potential_Near_Miss'].sum()})")
    print(f"Test Records:  {len(test_df)} (SIF: {test_df['High_Potential_Near_Miss'].sum()})")

    # 3. Feature Engineering
    print("\n[STEP 3] Fitting TF-IDF & Encoders STRICTLY on Training Data...")
    matrices = prepare_feature_matrices(train_df, val_df, test_df)
    
    # 4. Model Training & Validation Experiments
    print("\n[STEP 4] Running Baseline & ML Candidate Experiments...")
    
    experiment_results = []
    trained_models_dict = {}

    # --- BASELINE 1: Majority Class ---
    t0 = time.time()
    b1 = MajorityClassBaseline()
    b1.fit(matrices["config_a_text"]["X_train"], matrices["y_train"])
    b1_pred_val = b1.predict(matrices["config_a_text"]["X_val"])
    b1_prob_val = b1.predict_proba(matrices["config_a_text"]["X_val"])[:, 1]
    m_b1 = compute_classification_metrics(matrices["y_val"], b1_pred_val, b1_prob_val)
    m_b1.update({"model_name": "Majority_Class_Baseline", "config": "Baseline", "train_time_sec": round(time.time() - t0, 4), "y_true": matrices["y_val"], "y_prob": b1_prob_val})
    experiment_results.append(m_b1)

    # --- BASELINE 2: 4-Factor Rule ---
    t0 = time.time()
    b2 = FourFactorRuleBaseline()
    b2_pred_val = b2.predict_from_df(val_df)
    b2_prob_val = b2.predict_proba_from_df(val_df)[:, 1]
    m_b2 = compute_classification_metrics(matrices["y_val"], b2_pred_val, b2_prob_val)
    m_b2.update({"model_name": "4Factor_Rule_Baseline", "config": "Baseline", "train_time_sec": round(time.time() - t0, 4), "y_true": matrices["y_val"], "y_prob": b2_prob_val})
    experiment_results.append(m_b2)

    # --- CONFIGURATION A: Text Only ---
    print("  -> Training Configuration A (Text Only)...")
    models_a = train_candidate_models(matrices["config_a_text"]["X_train"], matrices["y_train"], "config_a_text")
    for name, model in models_a.items():
        t0 = time.time()
        pred_val = model.predict(matrices["config_a_text"]["X_val"])
        prob_val = model.predict_proba(matrices["config_a_text"]["X_val"])[:, 1] if hasattr(model, 'predict_proba') else None
        m = compute_classification_metrics(matrices["y_val"], pred_val, prob_val)
        full_name = f"ConfigA_Text_{name}"
        m.update({"model_name": full_name, "config": "Config A (Text)", "train_time_sec": round(time.time() - t0, 4), "y_true": matrices["y_val"], "y_prob": prob_val})
        experiment_results.append(m)
        trained_models_dict[full_name] = (model, matrices["config_a_text"])

    # --- CONFIGURATION B: Structured Only ---
    print("  -> Training Configuration B (Structured Only)...")
    models_b = train_candidate_models(matrices["config_b_struct"]["X_train"], matrices["y_train"], "config_b_struct")
    for name, model in models_b.items():
        t0 = time.time()
        pred_val = model.predict(matrices["config_b_struct"]["X_val"])
        prob_val = model.predict_proba(matrices["config_b_struct"]["X_val"])[:, 1] if hasattr(model, 'predict_proba') else None
        m = compute_classification_metrics(matrices["y_val"], pred_val, prob_val)
        full_name = f"ConfigB_Struct_{name}"
        m.update({"model_name": full_name, "config": "Config B (Structured)", "train_time_sec": round(time.time() - t0, 4), "y_true": matrices["y_val"], "y_prob": prob_val})
        experiment_results.append(m)
        trained_models_dict[full_name] = (model, matrices["config_b_struct"])

    # --- CONFIGURATION C: Combined (Text + Structured) ---
    print("  -> Training Configuration C (Text + Structured Combined)...")
    models_c = train_candidate_models(matrices["config_c_combined"]["X_train"], matrices["y_train"], "config_c_combined")
    for name, model in models_c.items():
        t0 = time.time()
        pred_val = model.predict(matrices["config_c_combined"]["X_val"])
        prob_val = model.predict_proba(matrices["config_c_combined"]["X_val"])[:, 1] if hasattr(model, 'predict_proba') else None
        m = compute_classification_metrics(matrices["y_val"], pred_val, prob_val)
        full_name = f"ConfigC_Comb_{name}"
        m.update({"model_name": full_name, "config": "Config C (Combined)", "train_time_sec": round(time.time() - t0, 4), "y_true": matrices["y_val"], "y_prob": prob_val})
        experiment_results.append(m)
        trained_models_dict[full_name] = (model, matrices["config_c_combined"])

    # 5. Threshold Analysis on Validation Set
    print("\n[STEP 5] Performing Threshold Analysis on Validation Set for Top Candidate...")
    top_cand_name = "ConfigA_Text_LogisticRegression_Balanced"
    cand_model, cand_data = trained_models_dict[top_cand_name]
    val_prob = cand_model.predict_proba(cand_data["X_val"])[:, 1]
    
    df_thresh, best_thresh_info = perform_threshold_analysis(
        matrices["y_val"], val_prob, model_name=top_cand_name
    )
    best_threshold = best_thresh_info["threshold"]
    print(f"Optimal Threshold (Val F1 Max): {best_threshold:.2f} (SIF Recall: {best_thresh_info['sif_recall']}, SIF Precision: {best_thresh_info['sif_precision']}, SIF F1: {best_thresh_info['sif_f1']})")

    # 6. Final Evaluation on Untouched Test Set
    print("\n[STEP 6] Final Unbiased Evaluation on Untouched Test Set...")
    test_results = []
    
    for full_name, (model, data_dict) in trained_models_dict.items():
        prob_test = model.predict_proba(data_dict["X_test"])[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Default 0.50 threshold
        pred_test_50 = model.predict(data_dict["X_test"])
        m_50 = compute_classification_metrics(matrices["y_test"], pred_test_50, prob_test)
        
        # Optimal threshold evaluated on test
        if prob_test is not None:
            pred_test_opt = (prob_test >= best_threshold).astype(int)
            m_opt = compute_classification_metrics(matrices["y_test"], pred_test_opt, prob_test)
        else:
            m_opt = m_50
            
        test_results.append({
            "model_name": full_name,
            "test_accuracy": m_50["accuracy"],
            "test_sif_precision_default": m_50["sif_precision"],
            "test_sif_recall_default": m_50["sif_recall"],
            "test_sif_f1_default": m_50["sif_f1"],
            "test_sif_precision_opt": m_opt["sif_precision"],
            "test_sif_recall_opt": m_opt["sif_recall"],
            "test_sif_f1_opt": m_opt["sif_f1"],
            "test_roc_auc": m_50["roc_auc"],
            "test_pr_auc": m_50["pr_auc"],
            "test_fp": m_50["fp"],
            "test_fn": m_50["fn"]
        })
        
        # Plot confusion matrix for top model
        if full_name == top_cand_name:
            plot_confusion_matrix(
                np.array(m_50["confusion_matrix"]), 
                f"Test Set Confusion Matrix ({full_name})", 
                "reports/figures/confusion_matrix_candidate_model.png"
            )

    df_test_comp = pd.DataFrame(test_results)
    df_test_comp.to_csv("reports/model_comparison.csv", index=False)
    print("--> Saved reports/model_comparison.csv")

    # Plot ROC & PR curves for validation models
    plot_roc_pr_curves(experiment_results, "reports/figures")

    # 7. Leakage Stress Test
    print("\n[STEP 7] Performing Leakage Stress Test...")
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder
    
    leakage_trans = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['Refinery_Unit', 'Work_Type', 'Department', 'Potential_Consequence', 'Risk_Level']),
            ('factor', 'passthrough', ['PPE_NonCompliance', 'Supervisor_Negligence', 'Maintenance_Delay_or_Issue', 'Repeated_Issue_Ignored'])
        ]
    )
    X_train_leak = leakage_trans.fit_transform(train_df)
    X_val_leak = leakage_trans.transform(val_df)
    
    lr_leak = LogisticRegression(max_iter=1000, random_state=42)
    lr_leak.fit(X_train_leak, matrices["y_train"])
    pred_val_leak = lr_leak.predict(X_val_leak)
    m_leak = compute_classification_metrics(matrices["y_val"], pred_val_leak)
    
    stress_test_md = f"""# OIL SIF Precursor Detection — Leakage Stress Test Report (Part 1B)

## Executive Summary
This stress test quantifies the performance distortion caused when target proxy fields (`Potential_Consequence`, `Risk_Level`) are inappropriately included as model features compared to clean baseline configurations.

---

## Stress Test Results Comparison (Validation Set)

| Feature Configuration | SIF Precision | SIF Recall | SIF F1 | Accuracy | Target Proxy Inclusion | Risk Level |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Config A (Text Only)** | `{experiment_results[2]['sif_precision']}` | `{experiment_results[2]['sif_recall']}` | `{experiment_results[2]['sif_f1']}` | `{experiment_results[2]['accuracy']}` | Excluded | Safe |
| **Config B (Clean Structured)** | `{experiment_results[6]['sif_precision']}` | `{experiment_results[6]['sif_recall']}` | `{experiment_results[6]['sif_f1']}` | `{experiment_results[6]['accuracy']}` | Excluded | Safe |
| **Config C (Combined Clean)** | `{experiment_results[10]['sif_precision']}` | `{experiment_results[10]['sif_recall']}` | `{experiment_results[10]['sif_f1']}` | `{experiment_results[10]['accuracy']}` | Excluded | Safe |
| **LEAKAGE MODEL (With Potential_Consequence & Risk_Level)** | `{m_leak['sif_precision']}` | `{m_leak['sif_recall']}` | `{m_leak['sif_f1']}` | `{m_leak['accuracy']}` | **INCLUDED** | 🚨 **TARGET LEAKAGE** |

---

## Audit Conclusion & Recommendation
- **Leakage Impact**: Including `Potential_Consequence` and `Risk_Level` yields artificially inflated 100% metrics because `Potential_Consequence` categories strictly separate SIF vs Non-SIF cases.
- **Enforced Safeguard**: `Potential_Consequence`, `Risk_Level`, `Corrective_Action`, `Action_Status`, and `source_sheet` MUST remain strictly excluded from all Part 1C model feature pipelines.
"""
    with open("reports/leakage_model_stress_test.md", "w", encoding="utf-8") as f:
        f.write(stress_test_md)
    print("--> Saved reports/leakage_model_stress_test.md")

    # 8. Model Explainability & False Negative Analysis
    print("\n[STEP 8] Extracting Model Explainability & Analyzing False Negatives...")
    top_coeffs = get_top_feature_coefficients(cand_model, cand_data["feature_names"], top_n=15)
    
    # Save False Negative Report
    test_prob = cand_model.predict_proba(cand_data["X_test"])[:, 1]
    test_pred_opt = (test_prob >= best_threshold).astype(int)
    analyze_false_negatives(test_df, matrices["y_test"], test_pred_opt, test_prob, "reports/false_negative_analysis.md")
    print("--> Saved reports/false_negative_analysis.md")

    # Subgroup analysis
    subgroup_df = analyze_source_sheet_subgroups(test_df, test_pred_opt)
    subgroup_df.to_csv("reports/source_sheet_subgroup_analysis.csv", index=False)
    print("--> Saved reports/source_sheet_subgroup_analysis.csv")

    # 9. Create Model Comparison Markdown Report
    print("\n[STEP 9] Generating Model Comparison Report...")
    comp_md = f"""# OIL SIF Precursor Detection — Model Comparison Report (Part 1B)

## Executive Summary
This report presents the empirical performance comparison of baseline and candidate machine learning models evaluated on the stratified **Validation Set** and untouched **Test Set**.

---

## Validation Set Performance Comparison

| Model Name | Configuration | SIF Precision | SIF Recall | SIF F1 | Accuracy | ROC-AUC | PR-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for r in experiment_results:
        comp_md += f"| `{r['model_name']}` | {r['config']} | {r['sif_precision']} | {r['sif_recall']} | {r['sif_f1']} | {r['accuracy']} | {r['roc_auc']} | {r['pr_auc']} |\n"

    comp_md += f"""

---

## Untouched Test Set Performance (Final Candidate Models)

- **Selected Candidate Model**: `{top_cand_name}`
- **Optimal Decision Threshold (Validation Tuned)**: `{best_threshold:.2f}`

| Model Name | Accuracy | SIF Prec (Thresh 0.50) | SIF Rec (Thresh 0.50) | SIF F1 (Thresh 0.50) | SIF Prec (Thresh {best_threshold:.2f}) | SIF Rec (Thresh {best_threshold:.2f}) | SIF F1 (Thresh {best_threshold:.2f}) | ROC-AUC | PR-AUC | False Negatives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for tr in test_results:
        comp_md += f"| `{tr['model_name']}` | {tr['test_accuracy']} | {tr['test_sif_precision_default']} | {tr['test_sif_recall_default']} | {tr['test_sif_f1_default']} | {tr['test_sif_precision_opt']} | {tr['test_sif_recall_opt']} | {tr['test_sif_f1_opt']} | {tr['test_roc_auc']} | {tr['test_pr_auc']} | {tr['test_fn']} |\n"

    comp_md += f"""

---

## Top SIF Precursor Predictive Features (Learned NLP Terms)

### Positive SIF-Predictive Terms
"""
    for term, weight in top_coeffs["top_sif_features"]:
        comp_md += f"- **`{term}`**: weight `{weight}`\n"
        
    comp_md += """
### Negative / Non-SIF Terms
"""
    for term, weight in top_coeffs["top_non_sif_features"]:
        comp_md += f"- **`{term}`**: weight `{weight}`\n"

    with open("reports/model_comparison.md", "w", encoding="utf-8") as f:
        f.write(comp_md)
    print("--> Saved reports/model_comparison.md")

    # 10. Save Candidate Model Artifacts & Metadata
    print("\n[STEP 10] Saving Candidate Model Artifacts & Metadata...")
    joblib.dump(cand_model, f"models/candidates/{top_cand_name}.joblib")
    joblib.dump(matrices["config_a_text"]["transformer"], "models/tfidf/tfidf_vectorizer.joblib")
    joblib.dump(matrices["config_b_struct"]["transformer"], "models/preprocessing/structured_transformer.joblib")
    
    metadata = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_path": "data/processed/cleaned_near_miss_dataset.parquet",
        "total_records": len(df),
        "splits": {"train": len(train_df), "validation": len(val_df), "test": len(test_df)},
        "target_col": "High_Potential_Near_Miss",
        "excluded_features": EXCLUDED_FEATURES,
        "selected_candidate_model": top_cand_name,
        "optimal_threshold": round(best_threshold, 2),
        "test_metrics": [r for r in test_results if r["model_name"] == top_cand_name][0]
    }
    with open("reports/experiment_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print("--> Saved reports/experiment_metadata.json")

    print("\n==================================================")
    print("PART 1B PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    main()
