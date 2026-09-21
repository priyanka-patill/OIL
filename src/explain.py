import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

def get_top_feature_coefficients(model, feature_names: List[str], top_n: int = 15) -> Dict[str, List[Tuple[str, float]]]:
    """
    Extracts top positive (SIF-predictive) and negative (Non-SIF) feature weights from a linear model.
    """
    if hasattr(model, 'coef_'):
        coefs = model.coef_[0]
    elif hasattr(model, 'calibrated_classifiers_'):
        # CalibratedClassifierCV wrapper
        coefs = np.mean([clf.estimator.coef_[0] for clf in model.calibrated_classifiers_], axis=0)
    else:
        return {"top_sif_features": [], "top_non_sif_features": []}

    top_pos_idx = np.argsort(coefs)[-top_n:][::-1]
    top_neg_idx = np.argsort(coefs)[:top_n]

    top_sif = [(feature_names[i], round(float(coefs[i]), 4)) for i in top_pos_idx]
    top_non_sif = [(feature_names[i], round(float(coefs[i]), 4)) for i in top_neg_idx]

    return {
        "top_sif_features": top_sif,
        "top_non_sif_features": top_non_sif
    }

def analyze_false_negatives(
    eval_df: pd.DataFrame, 
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    y_prob: np.ndarray = None,
    output_path: str = "reports/false_negative_analysis.md"
) -> Dict[str, Any]:
    """
    Performs detailed error analysis on False Negative SIF records.
    """
    eval_df = eval_df.copy()
    eval_df['actual'] = y_true
    eval_df['predicted'] = y_pred
    if y_prob is not None:
        eval_df['sif_probability'] = y_prob
        
    fn_df = eval_df[(eval_df['actual'] == 1) & (eval_df['predicted'] == 0)]
    tp_df = eval_df[(eval_df['actual'] == 1) & (eval_df['predicted'] == 1)]
    fp_df = eval_df[(eval_df['actual'] == 0) & (eval_df['predicted'] == 1)]
    
    total_sif = len(eval_df[eval_df['actual'] == 1])
    fn_count = len(fn_df)
    fn_rate = round(fn_count / total_sif, 4) if total_sif > 0 else 0.0

    # Markdown Report Construction
    md = f"""# OIL SIF Precursor Detection — False Negative Analysis (Part 1B)

## Executive Summary
False Negatives represent actual SIF-Potential cases missed by the model (predicted as Non-SIF). In high-hazard refinery operations, False Negatives are the most critical safety failure mode.

- **Total Actual SIF Records Evaluated**: `{total_sif}`
- **True Positives (SIF Detected)**: `{len(tp_df)}`
- **False Negatives (SIF Missed)**: `{fn_count}`
- **False Negative Rate**: `{fn_rate * 100:.1f}%`
- **False Positives (False Alarms)**: `{len(fp_df)}`

---

## False Negative Records Detail

"""
    if fn_count > 0:
        md += "| Record ID | Source Sheet | Work Type | Department | Probability | Description |\n"
        md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for idx, row in fn_df.iterrows():
            rec_id = row.get('Near_Miss_ID', f'IDX_{idx}')
            sheet = row.get('source_sheet', 'N/A')
            wt = row.get('Work_Type', 'N/A')
            dept = row.get('Department', 'N/A')
            prob_str = f"{row['sif_probability']:.3f}" if 'sif_probability' in row else 'N/A'
            desc = str(row.get('Near_Miss_Description', '')).replace('|', '\\|')
            md += f"| `{rec_id}` | `{sheet}` | {wt} | {dept} | `{prob_str}` | {desc} |\n"
    else:
        md += "✅ **Zero False Negatives recorded on the evaluated set.** All SIF precursor reports were successfully flagged by the candidate model.\n"

    md += """

---

## Pattern Analysis & Root Causes

1. **Short / Ambiguous Descriptions**: Near-miss descriptions with very concise wording or missing explicit hazard keywords.
2. **Precursor Factor Masking**: Scenarios where safety factors are active but phrasing resembles routine operational maintenance.
3. **Template Variations**: Novel clause combinations present in test/validation sets not seen in training.
4. **Safeguards for Part 1C**:
   - Apply optimal decision threshold (e.g., lower threshold to boost SIF recall).
   - Implement an automated high-risk keyword trigger alongside model prediction scores.
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
        
    return {
        "total_sif": total_sif,
        "false_negatives": fn_count,
        "false_negative_rate": fn_rate,
        "fn_records": fn_df.to_dict(orient='records')
    }

def analyze_source_sheet_subgroups(eval_df: pd.DataFrame, y_pred: np.ndarray) -> pd.DataFrame:
    """
    Evaluates predictions post-hoc across source_sheet subgroups to audit performance by origin sheet.
    NOTE: source_sheet is used ONLY post-hoc for auditing, NEVER as an ML feature.
    """
    df_audit = eval_df.copy()
    df_audit['predicted_sif'] = y_pred
    
    subgroup = df_audit.groupby('source_sheet').agg(
        total_records=('High_Potential_Near_Miss', 'count'),
        actual_sif=('High_Potential_Near_Miss', 'sum'),
        predicted_sif=('predicted_sif', 'sum')
    ).reset_index()
    
    subgroup['actual_sif_rate'] = (subgroup['actual_sif'] / subgroup['total_records']).round(3)
    subgroup['predicted_sif_rate'] = (subgroup['predicted_sif'] / subgroup['total_records']).round(3)
    
    return subgroup
