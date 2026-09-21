import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from typing import Dict, Any, List, Tuple

def perform_threshold_analysis(
    y_true: np.ndarray, 
    y_prob: np.ndarray, 
    model_name: str = "Candidate_Model",
    output_dir: str = "reports"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Sweeps thresholds from 0.05 to 0.95 on validation data to identify optimal trade-offs.
    """
    thresholds = np.linspace(0.05, 0.95, 19)
    records = []
    
    best_f1 = -1.0
    best_thresh_f1 = 0.50
    best_metrics = {}

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        
        prec = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
        rec = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
        f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
        
        rec_entry = {
            "model_name": model_name,
            "threshold": round(t, 2),
            "sif_precision": round(prec, 4),
            "sif_recall": round(rec, 4),
            "sif_f1": round(f1, 4),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        }
        records.append(rec_entry)
        
        if f1 > best_f1:
            best_f1 = f1
            best_thresh_f1 = t
            best_metrics = rec_entry

    df_thresh = pd.DataFrame(records)
    
    # Save CSV report
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "threshold_analysis.csv")
    df_thresh.to_csv(csv_path, index=False)

    # Plot Threshold Curves
    fig_dir = os.path.join(output_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df_thresh['threshold'], df_thresh['sif_precision'], 'b-o', label='SIF Precision')
    ax.plot(df_thresh['threshold'], df_thresh['sif_recall'], 'r-s', label='SIF Recall')
    ax.plot(df_thresh['threshold'], df_thresh['sif_f1'], 'g-^', label='SIF F1-Score')
    ax.axvline(x=best_thresh_f1, color='gray', linestyle='--', label=f'Optimal F1 Thresh ({best_thresh_f1:.2f})')
    
    ax.set_title(f"Threshold Analysis on Validation Set ({model_name})", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Decision Threshold", fontweight='bold')
    ax.set_ylabel("Metric Score", fontweight='bold')
    ax.legend(loc='lower left', fontsize=9)
    plt.tight_layout()
    fig.savefig(os.path.join(fig_dir, "threshold_tradeoff.png"), dpi=300)
    plt.close(fig)

    return df_thresh, best_metrics
