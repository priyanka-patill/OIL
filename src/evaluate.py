import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, confusion_matrix, roc_curve
)
from typing import Dict, Any, Tuple, List

def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None) -> Dict[str, Any]:
    """
    Computes comprehensive evaluation metrics with a focus on SIF (Class 1).
    """
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    acc = float(accuracy_score(y_true, y_pred))
    prec_sif = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    rec_sif = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1_sif = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))
    
    roc_auc = None
    pr_auc = None
    
    if y_prob is not None:
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
            p_curve, r_curve, _ = precision_recall_curve(y_true, y_prob)
            pr_auc = float(auc(r_curve, p_curve))
        except Exception:
            roc_auc = None
            pr_auc = None

    return {
        "accuracy": round(acc, 4),
        "sif_precision": round(prec_sif, 4),
        "sif_recall": round(rec_sif, 4),
        "sif_f1": round(f1_sif, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else "N/A",
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else "N/A",
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "fn_rate": round(float(fn / (tp + fn)), 4) if (tp + fn) > 0 else 0.0,
        "confusion_matrix": cm.tolist()
    }

def plot_confusion_matrix(cm: np.ndarray, title: str, output_path: str):
    """Plots and saves a styled confusion matrix figure."""
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Non-SIF (0)', 'SIF (1)'],
                yticklabels=['Non-SIF (0)', 'SIF (1)'], ax=ax)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel("Predicted Class", fontweight='bold')
    ax.set_ylabel("Actual Class", fontweight='bold')
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

def plot_roc_pr_curves(eval_results: List[Dict[str, Any]], output_dir: str = "reports/figures"):
    """Plots ROC and Precision-Recall curves for top models."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. ROC Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    for res in eval_results:
        if res.get('y_prob') is not None and res.get('roc_auc') != 'N/A':
            fpr, tpr, _ = roc_curve(res['y_true'], res['y_prob'])
            ax.plot(fpr, tpr, label=f"{res['model_name']} (AUC = {res['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], 'k--', label='Random Chance')
    ax.set_title("ROC Curves Comparison", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("False Positive Rate", fontweight='bold')
    ax.set_ylabel("True Positive Rate (Recall)", fontweight='bold')
    ax.legend(loc='lower right', fontsize=9)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "roc_curves_comparison.png"), dpi=300)
    plt.close(fig)

    # 2. PR Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    for res in eval_results:
        if res.get('y_prob') is not None and res.get('pr_auc') != 'N/A':
            p_curve, r_curve, _ = precision_recall_curve(res['y_true'], res['y_prob'])
            ax.plot(r_curve, p_curve, label=f"{res['model_name']} (PR-AUC = {res['pr_auc']:.3f})")
    ax.set_title("Precision-Recall Curves Comparison", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Recall (SIF)", fontweight='bold')
    ax.set_ylabel("Precision (SIF)", fontweight='bold')
    ax.legend(loc='lower left', fontsize=9)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "pr_curves_comparison.png"), dpi=300)
    plt.close(fig)
