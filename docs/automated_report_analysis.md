# Automated Safety Report Analysis Specification (`SIM_EVAL_v1` & `RISK_EVAL_v1`)

## Overview
This document specifies the end-to-end automated analysis pipeline triggered upon safety observation report submission in the Oil India Limited (OIL) HSE SIF Analytics application.

> [!NOTE]
> **Key Architecture Rule**:
> Manual user inputs for **Previous Similar Reports (Count)** and **Risk Level Assessment** have been removed from the frontend form. Both values are authoritative, system-calculated outcomes derived by the backend services upon report submission and persisted in the database.

---

## 1. End-to-End Submission & Analysis Workflow

```
[ USER FILLS OBSERVATION FORM ]
              │ (Only observation & hazard context; NO manual risk or similar count)
              ▼
[ POST /api/v1/reports ]
              │
              ├─► 1. Persist SafetyReport (Status: SUBMITTED)
              │
              ├─► 2. Enforce RBAC Scoping & Fetch Persisted Reports
              │
              ├─► 3. Execute Historical Similarity Engine (SIM_EVAL_v1)
              │       └─► Calculate Previous Similar Reports Count & Match List
              │
              ├─► 4. Run Part 1C ML Model (sif_model_v1)
              │       └─► Predict SIF-Potential Probability & Explainability
              │
              ├─► 5. Execute LSR, Hazard & Barrier Parsers
              │
              ├─► 6. Execute Risk Assessment Engine (RISK_EVAL_v1)
              │       └─► Calculate Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
              │
              ├─► 7. Persist AIAnalysis & Update SafetyReport Record
              │       └─► Status: AI_ANALYZED
              │
              ▼
[ RETURN AUTHORITATIVE RESPONSE TO FRONTEND ]
              │
              ▼
[ FRONTEND DISPLAYS SYSTEM ANALYSIS ]
```

---

## 2. Historical Cross-Report Similarity Methodology (`SIM_EVAL_v1`)

### 2.1 Rules & Safeguards
- **Persisted Reports Search**: The similarity engine searches existing database records (`safety_reports`).
- **Self-Match Exclusion**: The newly submitted report (`target_report_id`) is strictly excluded from candidate matching.
- **RBAC Authorization**: Users can only search reports within their authorized data scope (site/department constraints for `HSE_USER`).
- **Data Leakage Safeguard**: `source_sheet` and dataset tab names are excluded.
- **No Mock Data**: All matched reports and similarity scores correspond to actual persisted database records.

### 2.2 Matching Engine
1. **Multi-Dimension Categorical Matching**:
   - `equipment_id` (Weight: 3.0)
   - `activity` (Weight: 2.0)
   - `location` (Weight: 2.0)
   - `refinery_unit` (Weight: 1.5)
   - `work_type` (Weight: 1.0)
   - `department` (Weight: 1.0)
   - Shared Hazards / Barriers (Weight: 1.5 per item)
2. **NLP Text Similarity**:
   - TF-IDF unigram + bigram vectorizer cosine similarity on normalized `description` text.
   - Contributes `text_sim * 4.0` if cosine similarity $> 0.30$.
3. **Thresholding**:
   - Configurable `ANALYTICS_SIMILARITY_THRESHOLD` ($0.75$ for text near-duplicates, combined overlap score $\ge 3.0$ for related reports).
4. **Empty Database / First Report Behavior**:
   - If 0 historical reports exist, `previous_similar_reports_count = 0`, matching list is `[]`, and explanation indicates `"No historical reports available for comparison."`

---

## 3. Risk Assessment Methodology (`RISK_EVAL_v1`)

For full details, see [`docs/risk_level_methodology.md`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/docs/risk_level_methodology.md).

Risk Level is derived deterministically from:
1. Part 1C ML SIF Probability
2. High-severity hazard indicators
3. Critical barrier degradation concerns
4. Precursor flags (`ppe_noncompliance`, `supervisor_negligence`, `maintenance_delay_or_issue`, `repeated_issue_ignored`)
5. Calculated `previous_similar_reports_count`

Output levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

---

## 4. Database Persistence & Audit Traceability

Calculated outcomes are stored across two tables:

### 1. `safety_reports` Table
- `previous_similar_reports`: System-calculated integer count.
- `risk_level`: System-calculated string (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### 2. `ai_analyses` Table
- `previous_similar_reports_count`: Integer count.
- `similar_reports_json`: Structured JSON payload of matched reports, similarity scores, and evidence reasons.
- `risk_level`: System-calculated risk tier.
- `risk_explanation_json`: Structured JSON list of contributing risk evidence bullets.
- `risk_methodology_version`: `"RISK_EVAL_v1"`
- `similarity_methodology_version`: `"SIM_EVAL_v1"`
- `analysis_status`: `"COMPLETED"`

---

## 5. API Response Contract

Upon submitting a report or requesting report details, the API returns the calculated values:

```json
{
  "success": true,
  "message": "Safety report created successfully.",
  "data": {
    "id": 42,
    "report_number": "OIL-2026-000042",
    "previous_similar_reports": 2,
    "risk_level": "HIGH",
    "ai_analysis": {
      "prediction": "SIF-Potential",
      "probability_or_score": 0.8421,
      "previous_similar_reports_count": 2,
      "risk_level": "HIGH",
      "risk_explanation_json": "[\"SIF-Potential ML classification detected (Model Probability: 84.2%)\", \"Critical barrier degradation concern: Energy Isolation\", \"Repeated historical safety observations found (Count: 2)\"]",
      "similar_reports_json": "[{\"related_report_number\": \"OIL-2026-000018\", \"similarity_score\": 0.84, \"evidence_explanation\": \"Matching Equipment Tag: P-305; Description Text Similarity: 84.0%\"}]",
      "risk_methodology_version": "RISK_EVAL_v1",
      "similarity_methodology_version": "SIM_EVAL_v1"
    }
  }
}
```
