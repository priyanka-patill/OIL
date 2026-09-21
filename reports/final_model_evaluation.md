# OIL SIF Precursor Detection — Final Model Evaluation Report (Part 1C)

## Executive Summary
Evaluation results for `sif_model_v1` on the stratified Validation Set and untouched Test Set.

- **Optimal Decision Threshold**: `0.60`
- **Average Inference Latency**: `0.886 ms`

---

## Metric Breakdown

| Dataset Split | Accuracy | SIF Precision | SIF Recall | SIF F1 | ROC-AUC | PR-AUC | False Negatives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Validation Set** | `0.9085` | `0.5714` | `0.5333` | `0.5517` | `0.8121` | `0.4191` | `7` |
| **Untouched Test Set** | `0.9161` | `0.5789` | `0.7333` | `0.6471` | `0.9094` | `0.7014` | `4` |
