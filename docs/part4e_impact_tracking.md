# Part 4E — Completion, Verification & Impact Tracking Documentation

## 1. Executive Summary & Architectural Overview

Part 4E introduces time-aware operational action completion, human-in-the-loop HSE verification, multi-cycle reopen audit trails, and an **observational Before/After Impact Tracking Engine** (`impact_service.py`) for the Oil India Limited (OIL) HSE Safety Intelligence Platform.

```
+-----------------------------------------------------------------------------------+
|                            ACTION LIFECYCLE (Part 4E)                             |
+-----------------------------------------------------------------------------------+
|  ASSIGNED / IN_PROGRESS                                                           |
|        |                                                                          |
|        v [Assignee: Complete Action + Upload Evidence + Mandatory Comment]        |
|  COMPLETED -> VERIFICATION_PENDING (Server timestamp recorded)                    |
|        |                                                                          |
|        +-------------------------+-------------------------+                      |
|        | [HSE Reviewer: VERIFY]  |                         | [HSE: REOPEN]        |
|        v                         v                         v                      |
|     VERIFIED                  REOPENED                CANCELLED                   |
|  (Triggers Impact Analysis) (Cycle preserved)         (Closed)                    |
+-----------------------------------------------------------------------------------+
```

---

## 2. Action Completion & HSE Verification Workflows

### 2.1 Assignee Action Completion Workflow
- **State Transition**: `IN_PROGRESS` / `REOPENED` / `ASSIGNED` $\rightarrow$ `COMPLETED` $\rightarrow$ `VERIFICATION_PENDING`.
- **Mandatory Requirements**:
  - Assignee must submit a non-empty `completion_comment`.
  - Server automatically records `completion_date` (UTC).
  - Optional evidence metadata (`file_name`, `file_path`, `description`) attached as `ActionEvidence`.
- **SLA Timing Preservation**:
  - The SLA engine calculates `COMPLETED_ON_TIME` vs `COMPLETED_LATE` upon completion and freezes the clock.

### 2.2 HSE Reviewer Verification & Reopen Workflow
- **State Transition**: `VERIFICATION_PENDING` / `COMPLETED` $\rightarrow$ `VERIFIED` or `REOPENED`.
- **VERIFY**:
  - Sets server `verified_at` timestamp.
  - Automatically triggers Part 4E Observational Impact Analysis.
- **REOPEN**:
  - Requires a mandatory `reopen_reason`.
  - Sets server `reopened_at` timestamp.
  - Action transitions to `REOPENED`, allowing assignee to submit subsequent completion cycles.

### 2.3 Multi-Cycle Completion History (`ActionCompletionHistory`)
- Preserves full audit history across multiple completion/reopen attempts without overwriting previous data.
- Each cycle records: `cycle_number`, `completed_at`, `completed_by`, `completion_comment`, `verification_status`, `verified_at`, `verified_by`, `verification_comment`, `reopened_at`, `reopened_by`, `reopen_reason`.

---

## 3. Observational Before/After Impact Engine Methodology (`impact_methodology_v1`)

### 3.1 Observation Windows & Intervention Date
- **Intervention Date**: Derived from `verified_at`, falling back to `completion_date` or current UTC time.
- **Before Period**: 90-day window (`intervention_date - 90 days` to `intervention_date`).
- **After Period**: 90-day window (`intervention_date + 1 day` to `intervention_date + 90 days`).

### 3.2 5 Safety Indicators Comparison Framework
1. **Related Report Recurrence**: Count of precursor safety reports matching intervention scope in Before vs. After periods.
2. **SIF-Potential Precursor Reports**: Count and proportion of SIF-potential precursors (`SIF_POTENTIAL`, `HIGH`, `classification == 1`) in Before vs. After periods.
3. **Barrier Recurrence**: Count of precursor occurrences associated with the action's specific safety barrier category.
4. **SIF Precursor Density**: Percentage of SIF precursors out of all site-analyzed reports ($(\text{SIF Reports} / \text{Total Analyzed}) \times 100$). Zero denominators are handled safely returning `N/A`.
5. **Recurring Pattern Frequency**: Frequency of precursor reports associated with the action's specific recurring pattern ID.

### 3.3 Data Sufficiency Rules & Zero Denominator Protection
- **Rule**: Minimum of **2 relevant precursor reports** required in the Before period for descriptive comparison.
- **Status**: If sample $< 2$ or zero total site reports exist in the Before period, the system returns `INSUFFICIENT_DATA` rather than misleading zero or 100% percentages.
- **Zero Denominator Protection**: All ratio calculations check divisors prior to division, preventing `ZeroDivisionError`.

### 3.4 Non-Causal Framing & Anti-Leakage Safeguards
- **Strict Non-Causal Terminology**: All text descriptions are strictly observational (*"Observed count changed from X to Y"*).
- **Forbidden Causal Terms**: Terms like *"caused"*, *"prevented"*, *"eliminated"*, *"proven reduction"*, or *"reduced fatality risk"* are strictly prohibited in generated output.
- **Disclaimer**: Mandatory methodology disclaimer included in all outputs:
  > *"These comparisons describe observed changes between the defined before and after periods. They do not establish that the intervention caused the observed change."*
- **Anti-Leakage**: `source_sheet` and `"12_High_Potential"` metadata have ZERO influence on impact calculations.

---

## 4. API Endpoints Specification

| Endpoint | Method | Role Access | Description |
| :--- | :--- | :--- | :--- |
| `/api/actions/{id}/complete` | `POST` | Assignee / HSE | Submit action completion with mandatory comment & evidence. |
| `/api/actions/{id}/verify` | `POST` | HSE Reviewer / Admin | Verify (`VERIFY`) or reopen (`REOPEN`) completed action. |
| `/api/actions/{id}/reopen` | `POST` | HSE Reviewer / Admin | Explicitly reopen action with mandatory reason. |
| `/api/actions/{id}/evidence` | `POST` | Authenticated | Attach evidence file metadata to an action. |
| `/api/actions/{id}/completion-history` | `GET` | Authenticated | Retrieve multi-cycle completion history audit trail. |
| `/api/actions/{id}/impact` | `GET` | Authenticated | Retrieve latest observational Before/After Impact Analysis snapshot. |
| `/api/actions/{id}/impact/recalculate` | `POST` | HSE Reviewer / Admin | Manually trigger re-calculation of observational impact snapshot. |

---

## 5. Contract for Part 4F Integration

1. **Impact Snapshot Availability**: `Action.impact_analysis` payload is serialized directly in action detail responses for seamless rendering in the HSE Action Center (Part 4F).
2. **Audit & Compliance**: `ActionCompletionHistory` provides complete traceability required for HSE compliance dashboards in Part 4F.
