# Risk Level Assessment Methodology (`RISK_EVAL_v1`)

## Overview
This document specifies the authoritative, system-calculated **Risk Level Assessment Methodology (`RISK_EVAL_v1`)** for safety observation reports within the Oil India Limited (OIL) HSE SIF Analytics System.

The Risk Level is automatically derived by the backend system upon report submission based on empirical safety evidence extracted from the report text, structured precursor indicators, hazard/barrier analysis, cross-report historical similarity, and the Part 1C SIF Machine Learning model score.

> [!IMPORTANT]
> - **System-Calculated Only**: Risk Level Assessment is strictly system-analyzed and is not manually entered or selected by the user.
> - **Descriptive Risk Tier**: Risk Level is a transparent, evidence-based HSE prioritization tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). It is **not** a calibrated probabilistic estimate of accident or fatality occurrence.
> - **Data Leakage Safeguard**: `source_sheet` and dataset tab names such as `12_High_Potential` are strictly excluded from prediction and risk calculation.

---

## 1. Input Features & Safety Evidence

The system-calculated Risk Level uses the following available inputs:

| Input Evidence Category | Field / Signal | Source |
| :--- | :--- | :--- |
| **SIF Prediction** | ML Model Probability (`probability_or_score`) & Classification (`SIF-Potential` vs `Non-SIF`) | Part 1C ML Engine (`models/final_model`) |
| **High-Severity Hazards** | Identified hazards (e.g. Confined Space, Working at Height, Hot Work, Line of Fire, Electrical, Pressure, Chemical) | Rule-based hazard parser (`backend/services/hazard_analysis.py`) |
| **Critical Barrier Concerns** | Identified barrier degradation (e.g. Energy Isolation, Permit to Work, Gas Testing, Supervision, Fall Protection) | Rule-based barrier parser (`backend/services/barrier_analysis.py`) |
| **Precursor Flags** | `ppe_noncompliance`, `supervisor_negligence`, `maintenance_delay_or_issue`, `repeated_issue_ignored` | Structured safety precursor flags |
| **Cross-Report Similarity** | `previous_similar_reports_count` | System-calculated historical similarity search (`SIM_EVAL_v1`) |

---

## 2. Decision Logic Matrix

The Risk Level is evaluated deterministically using the following matrix:

### CRITICAL Risk Level
Assigned if **ANY** of the following conditions are met:
1. SIF ML prediction is `SIF-Potential` (Model score $\ge 0.60$) **AND** a critical barrier degradation (e.g. Energy Isolation, Permit to Work) **AND** (`previous_similar_reports_count` $\ge 2$ OR `repeated_issue_ignored` is `True`).
2. Multiple high-severity hazards ($\ge 2$) identified alongside `supervisor_negligence` / permit defect.

### HIGH Risk Level
Assigned if **ANY** of the following conditions are met (and not classified as CRITICAL):
1. SIF ML prediction is `SIF-Potential` (Model score $\ge 0.60$).
2. High-severity hazard identified (e.g., Working at Height, Confined Space Entry, Line of Fire, Hot Work, Electrical Exposure).
3. Critical barrier concern identified (e.g., Energy Isolation, Gas Testing, Permit Control).
4. `previous_similar_reports_count` $\ge 3$ **OR** `repeated_issue_ignored` is `True`.

### MEDIUM Risk Level
Assigned if **ANY** of the following conditions are met (and not classified as HIGH or CRITICAL):
1. SIF ML probability between $0.35$ and $0.59$.
2. At least one precursor flag is active (`ppe_noncompliance`, `maintenance_delay_or_issue`).
3. `previous_similar_reports_count` is 1 or 2.
4. Any general hazard or barrier concern identified.

### LOW Risk Level
Assigned if none of the above conditions are met:
- Standard safety observation / near-miss with low SIF probability ($<0.35$), no high-severity hazards, no critical barrier failures, no precursor flags, and zero similar historical reports.

---

## 3. Explanations & Evidence Bullet Points

Every calculated Risk Level is accompanied by a transparent list of contributing evidence bullets:

- `SIF-Potential ML classification detected (Model Probability: 84.2%)`
- `High-severity hazard identified: Confined Space Entry / Line of Fire`
- `Critical barrier degradation concern: Energy Isolation`
- `Repeated historical safety observations found (Count: 2)`
- `Precursor flags active: Supervisor Negligence / Permit Defect`

---

## 4. Key Terminology & Concept Distinctions

It is important to distinguish Risk Level from other analytical concepts in the system:

1. **Risk Level (`LOW` to `CRITICAL`)**: System-analyzed composite operational hazard score evaluating current safety evidence.
2. **SIF-Potential (`SIF-Potential` vs `Non-SIF`)**: Binary ML classifier predicting whether an unsafe act or near-miss had precursor attributes capable of causing serious injury or fatality.
3. **Analytical Priority (`LOW_PRIORITY` to `HIGH_PRIORITY`)**: Entity-level (site/unit/equipment) aggregation score measuring cumulative risk density and barrier trends over time.
4. **Escalation Indicators**: Active operational red flags indicating accelerating risk trends across a plant section.

---

## 5. Limitations & Human Oversight

- **Decision Support**: Risk Level is automated decision-support intelligence designed to streamline HSE review.
- **Qualified HSE Validation**: Qualified HSE professionals can review, validate, or override the analysis via the HSE Validation Workflow.
- **No Missing Data Assumptions**: Missing fields default to conservative non-triggering conditions rather than arbitrary fallback levels.
