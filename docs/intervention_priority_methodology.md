# Intervention Recommendation Priority Methodology
## Oil India Limited (OIL) HSE Safety Intelligence Platform

### 1. Overview & Purpose
This document defines the transparent analytical methodology used to assign a **Suggested Priority** (`HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT_DATA`) to AI/system-generated intervention recommendations in Part 4A.

#### Critical Distinction:
- **Suggested Priority is NOT an Action Urgency or SLA Clock**.
- **Suggested Priority is NOT a Fatality Probability or Risk Percentage**.
- **It is strictly an analytical indicator** highlighting the depth of evidence, recurrence, and potential severity supporting the recommendation.

---

### 2. Analytical Inputs

The priority calculation logic evaluates 6 evidence dimensions:

1. **AI SIF Classification**: `SIF-Potential` vs `Non-SIF-Potential`
2. **Precursor Severity Audit Flags**: `repeated_issue_ignored`, `supervisor_negligence`, `maintenance_delay_or_issue`, `ppe_noncompliance`
3. **Cross-Report Recurrence**: Presence of a linked Part 3A `RecurringPattern`
4. **Barrier Degradation Index (BDI_v1)**: Numerical BDI score (0.0 to 100.0) where available
5. **Potential Escalation Indicators**: Number of active Part 3D risk persistence flags
6. **Data Completeness**: Observation text word count and field completeness

---

### 3. Classification Rules & Thresholds

#### A. `HIGH` Suggested Priority
Assigned when the recommendation is backed by high-severity precursor evidence or strong cross-report recurrence:
- **Condition H1**: `sif_classification == 'SIF-Potential'` AND (Linked `RecurringPattern` exists OR `BDI_score >= 75.0` OR `escalation_count >= 2`).
- **Condition H2**: `sif_classification == 'SIF-Potential'` AND `report.repeated_issue_ignored == True`.
- **Condition H3**: `BDI_score >= 80.0` OR `escalation_count >= 3` regardless of SIF classification.

#### B. `MEDIUM` Suggested Priority
Assigned for moderate risk precursor findings or isolated SIF potential observations:
- **Condition M1**: `sif_classification == 'SIF-Potential'` without high cross-report recurrence.
- **Condition M2**: `sif_classification == 'Non-SIF-Potential'` AND (Linked `RecurringPattern` exists OR `BDI_score >= 50.0` OR `report.supervisor_negligence == True` OR `report.maintenance_delay_or_issue == True`).

#### C. `LOW` Suggested Priority
Assigned for isolated routine safety observations with limited precursor complexity:
- **Condition L1**: `sif_classification == 'Non-SIF-Potential'` with no recurring patterns, low BDI (< 50.0), and standard procedural/PPE controls.

#### D. `INSUFFICIENT_DATA` Suggested Priority
Assigned when underlying report data lacks sufficient context for high-confidence analytical prioritization:
- **Condition I1**: Description contains fewer than 10 words or lacks work environment context.

---

### 4. Prohibited Terminology & Analytic Limits

- **Forbidden Phrases**: "Risk probability", "Fatality probability", "87% chance of accident".
- **Analytical Bound**: The system does NOT forecast future events or calculate probabilistic risk matrices.
- **Evidence Language**: Outputs state: *"Priority suggested based on SIF classification, precursor severity flags, and cross-report recurrence evidence."*

---

### 5. Summary Matrix

| Priority | SIF Classification | Recurrence / BDI / Escalation | Precursor Flags |
| :--- | :--- | :--- | :--- |
| **`HIGH`** | SIF-Potential | Recurring Pattern OR BDI ≥ 75 OR Escalation ≥ 2 | Repeated Issue Ignored = True |
| **`MEDIUM`** | SIF-Potential | Isolated observation (No pattern) | Any single precursor flag |
| **`MEDIUM`** | Non-SIF-Potential | Recurring Pattern OR BDI ≥ 50 | Supervisor / Maintenance flag |
| **`LOW`** | Non-SIF-Potential | No pattern, BDI < 50 | No severe audit flags |
| **`INSUFFICIENT_DATA`** | Any | Missing / Short description (< 10 words) | Incomplete fields |
