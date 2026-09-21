# OIL SIF Precursor Detection — Model Comparison Report (Part 1B)

## Executive Summary
This report presents the empirical performance comparison of baseline and candidate machine learning models evaluated on the stratified **Validation Set** and untouched **Test Set**.

---

## Validation Set Performance Comparison

| Model Name | Configuration | SIF Precision | SIF Recall | SIF F1 | Accuracy | ROC-AUC | PR-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Majority_Class_Baseline` | Baseline | 0.0 | 0.0 | 0.0 | 0.8944 | 0.5 | 0.5528 |
| `4Factor_Rule_Baseline` | Baseline | 0.5172 | 1.0 | 0.6818 | 0.9014 | 0.9449 | 0.7586 |
| `ConfigA_Text_LogisticRegression_Balanced` | Config A (Text) | 0.2564 | 0.6667 | 0.3704 | 0.7606 | 0.8121 | 0.4191 |
| `ConfigA_Text_LogisticRegression_Standard` | Config A (Text) | 0.0 | 0.0 | 0.0 | 0.8944 | 0.7512 | 0.3916 |
| `ConfigA_Text_LinearSVC_Calibrated` | Config A (Text) | 0.0 | 0.0 | 0.0 | 0.8944 | 0.8677 | 0.4315 |
| `ConfigA_Text_ComplementNB` | Config A (Text) | 0.2143 | 0.4 | 0.2791 | 0.7817 | 0.5664 | 0.1515 |
| `ConfigA_Text_RandomForest_Balanced` | Config A (Text) | 0.5238 | 0.7333 | 0.6111 | 0.9014 | 0.9451 | 0.6038 |
| `ConfigB_Struct_LogisticRegression_Balanced` | Config B (Structured) | 0.5185 | 0.9333 | 0.6667 | 0.9014 | 0.9071 | 0.348 |
| `ConfigB_Struct_LogisticRegression_Standard` | Config B (Structured) | 0.1667 | 0.1333 | 0.1481 | 0.838 | 0.9066 | 0.3449 |
| `ConfigB_Struct_LinearSVC_Calibrated` | Config B (Structured) | 0.2 | 0.1333 | 0.16 | 0.8521 | 0.916 | 0.3696 |
| `ConfigB_Struct_RandomForest_Balanced` | Config B (Structured) | 0.4091 | 0.6 | 0.4865 | 0.8662 | 0.9152 | 0.4211 |
| `ConfigC_Comb_LogisticRegression_Balanced` | Config C (Combined) | 0.5 | 0.9333 | 0.6512 | 0.8944 | 0.9076 | 0.3474 |
| `ConfigC_Comb_LogisticRegression_Standard` | Config C (Combined) | 0.2308 | 0.2 | 0.2143 | 0.8451 | 0.9087 | 0.3495 |
| `ConfigC_Comb_LinearSVC_Calibrated` | Config C (Combined) | 0.1429 | 0.0667 | 0.0909 | 0.8592 | 0.9113 | 0.3578 |
| `ConfigC_Comb_RandomForest_Balanced` | Config C (Combined) | 0.5 | 0.7333 | 0.5946 | 0.8944 | 0.9478 | 0.637 |


---

## Untouched Test Set Performance (Final Candidate Models)

- **Selected Candidate Model**: `ConfigA_Text_LogisticRegression_Balanced`
- **Optimal Decision Threshold (Validation Tuned)**: `0.60`

| Model Name | Accuracy | SIF Prec (Thresh 0.50) | SIF Rec (Thresh 0.50) | SIF F1 (Thresh 0.50) | SIF Prec (Thresh 0.60) | SIF Rec (Thresh 0.60) | SIF F1 (Thresh 0.60) | ROC-AUC | PR-AUC | False Negatives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `ConfigA_Text_LogisticRegression_Balanced` | 0.8182 | 0.3429 | 0.8 | 0.48 | 0.5789 | 0.7333 | 0.6471 | 0.9094 | 0.7014 | 3 |
| `ConfigA_Text_LogisticRegression_Standard` | 0.8951 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.8589 | 0.6434 | 15 |
| `ConfigA_Text_LinearSVC_Calibrated` | 0.9161 | 1.0 | 0.2 | 0.3333 | 1.0 | 0.0667 | 0.125 | 0.9411 | 0.7473 | 12 |
| `ConfigA_Text_ComplementNB` | 0.7972 | 0.2308 | 0.4 | 0.2927 | 0.2632 | 0.3333 | 0.2941 | 0.6198 | 0.3842 | 9 |
| `ConfigA_Text_RandomForest_Balanced` | 0.8741 | 0.4211 | 0.5333 | 0.4706 | 0.4286 | 0.4 | 0.4138 | 0.9276 | 0.4756 | 7 |
| `ConfigB_Struct_LogisticRegression_Balanced` | 0.8881 | 0.4828 | 0.9333 | 0.6364 | 0.5 | 0.9333 | 0.6512 | 0.9344 | 0.5626 | 1 |
| `ConfigB_Struct_LogisticRegression_Standard` | 0.9161 | 0.8 | 0.2667 | 0.4 | 0.6667 | 0.1333 | 0.2222 | 0.9328 | 0.5721 | 11 |
| `ConfigB_Struct_LinearSVC_Calibrated` | 0.9161 | 0.8 | 0.2667 | 0.4 | 1.0 | 0.0667 | 0.125 | 0.9286 | 0.5402 | 11 |
| `ConfigB_Struct_RandomForest_Balanced` | 0.8881 | 0.4667 | 0.4667 | 0.4667 | 0.5385 | 0.4667 | 0.5 | 0.9359 | 0.5117 | 8 |
| `ConfigC_Comb_LogisticRegression_Balanced` | 0.8881 | 0.4828 | 0.9333 | 0.6364 | 0.5217 | 0.8 | 0.6316 | 0.9505 | 0.7199 | 1 |
| `ConfigC_Comb_LogisticRegression_Standard` | 0.9231 | 0.75 | 0.4 | 0.5217 | 1.0 | 0.2 | 0.3333 | 0.9474 | 0.7073 | 9 |
| `ConfigC_Comb_LinearSVC_Calibrated` | 0.9091 | 1.0 | 0.1333 | 0.2353 | 0.0 | 0.0 | 0.0 | 0.9339 | 0.6746 | 13 |
| `ConfigC_Comb_RandomForest_Balanced` | 0.8881 | 0.4737 | 0.6 | 0.5294 | 0.4 | 0.4 | 0.4 | 0.9365 | 0.487 | 6 |


---

## Top SIF Precursor Predictive Features (Learned NLP Terms)

### Positive SIF-Predictive Terms
- **`had`**: weight `1.7011`
- **`without`**: weight `1.6121`
- **`worker`**: weight `1.3597`
- **`continued`**: weight `1.323`
- **`been`**: weight `1.2302`
- **`safety`**: weight `1.1186`
- **`continue repeated`**: weight `1.0981`
- **`abnormal`**: weight `1.0784`
- **`been reported`**: weight `1.0767`
- **`maintenance`**: weight `1.0405`
- **`reported`**: weight `1.0306`
- **`repeatedly`**: weight `0.9817`
- **`was`**: weight `0.9718`
- **`had been`**: weight `0.9635`
- **`work`**: weight `0.9356`

### Negative / Non-SIF Terms
- **`continue pump`**: weight `-0.4221`
- **`protection pump`**: weight `-0.2692`
- **`shutdown emergency`**: weight `-0.2646`
- **`harness maintenance`**: weight `-0.2527`
- **`protection lifting`**: weight `-0.2494`
- **`protection bearing`**: weight `-0.2475`
- **`supervision pump`**: weight `-0.2395`
- **`replacement pipeline`**: weight `-0.2258`
- **`delayed emergency`**: weight `-0.2186`
- **`shoes minor`**: weight `-0.2181`
- **`deferred valve`**: weight `-0.2163`
- **`clothing repeated`**: weight `-0.2108`
- **`postponed compressor`**: weight `-0.2093`
- **`repair gas`**: weight `-0.2074`
- **`on process`**: weight `-0.2066`
