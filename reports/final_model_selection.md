# OIL SIF Precursor Detection — Final Model Selection Report (Part 1C)

## Executive Summary
This report documents the selection rationale for the final deployed SIF prediction model package (`sif_model_v1`).

- **Selected Architecture**: `LogisticRegression` with balanced class weights on TF-IDF text features.
- **Model Version**: `sif_model_v1`
- **Saved Package Location**: `models/final_model/`

---

## Selection Rationale & Trade-off Analysis

1. **Text-Only NLP Reliability**: Configuration A (Text Only) avoids dependence on post-investigation or constructed structured fields (`Potential_Consequence`, `Risk_Level`).
2. **Safety-Critical Recall**: Balanced Logistic Regression delivers strong SIF Recall while maintaining an interpretable linear decision boundary.
3. **Low Inference Complexity**: Latency averages `0.886 ms` per report, ideal for real-time backend API scoring in Part 2.
4. **Transparent Explainability**: N-gram coefficients map directly to safety hazard terms (*isolated*, *bypassed*, *harness*, *gas detector*).
