# Barrier Degradation Index (BDI) Methodology Specification (`BDI_v1`)

**Project**: Oil India Limited (OIL) HSE Safety Intelligence Platform  
**Version**: `BDI_v1`  
**Date**: September 17, 2026  
**Status**: Active Methodology Specification

---

## 1. Executive Summary & Purpose

The **Barrier Degradation Index (BDI_v1)** is an evidence-based, descriptive analytical framework designed to identify safety barriers that exhibit recurring, persistent, unresolved, or high-consequence weaknesses across safety reports (Unsafe Act, Unsafe Condition, Near Miss, Incident).

### Core Principles:
- **Descriptive, Not Predictive**: BDI is a descriptive indicator of observed barrier concerns in historical reports. It does **NOT** predict future accidents, fatalities, or SIF events.
- **Evidence-Backed**: Every BDI value is accompanied by an explicit, auditable evidence payload containing contributing report IDs, site distributions, activity co-occurrences, and unresolved counts.
- **Zero Arbitrary Weights & Small-Sample Protection**: BDI requires a minimum evidence threshold of **3 unique reports** ($n \ge 3$). If fewer than 3 unique reports exist, the system outputs `status = "INSUFFICIENT_DATA"` and `bdi = null`.
- **Zero Data Leakage**: `source_sheet` and `"12_High_Potential"` are strictly 100% excluded from all barrier categories, recurrence counts, trends, and BDI scores.
- **AI vs. HSE Review Distinction**: AI-generated barrier concerns and HSE-validated barrier concerns are tracked independently, preserving the original AI output while using the HSE-validated output as the primary analytical signal when available.

---

## 2. Occurrence Definition

- **Unit of Occurrence**: 1 barrier occurrence = 1 unique report containing a specific barrier concern category.
- **Prevention of Multi-Keyword Inflation**: If a single report contains multiple keywords mapped to the same category (e.g., "LOTO not applied and valve not isolated"), it is counted as **1 occurrence** for `Energy Isolation` within that report.

---

## 3. Controlled Barrier Taxonomy & Normalization

Free-text barrier descriptions and Part 2C audit flags are mapped to standard categories using explicit, documented normalization rules in `backend/analytics/barrier_normalization.py`:

| Canonical Barrier Category | Input Keyword / Pattern Examples | Part 2C Precursor Flag Equivalent |
| :--- | :--- | :--- |
| `Personal Protective Equipment (PPE)` | "helmet", "glasses", "harness", "gloves", "ppe" | `ppe_noncompliance` |
| `Energy Isolation` | "loto", "lockout", "tagout", "isolation", "de-energize", "blind" | - |
| `Supervision & Work Permit Control` | "permit", "ptw", "supervisor", "unauthorized", "clearance" | `supervisor_negligence` |
| `Equipment Maintenance & Reliability` | "maintenance", "vibration", "leak", "corroded", "valve", "seal" | `maintenance_delay_or_issue` |
| `Hazard Recurrence & Isolation Control` | "repeat", "previous", "recurring", "ignored" | `repeated_issue_ignored` |
| `Gas Testing & Environmental Monitoring` | "gas test", "h2s", "explosimeter", "oxygen level", "ventilation" | - |
| `Machine Guarding & Physical Safety` | "guard", "scaffolding", "railing", "interlock", "barrier mesh" | - |
| `Safety Communication & Tool Box Talk` | "tbt", "toolbox", "handover", "briefing", "communication" | - |
| `Unmapped / Other` | Any unmapped free-text barrier description | - |

> [!NOTE]
> Normalization preserves the `original_barrier_text` alongside the `normalized_barrier_category` to ensure full auditability.

---

## 4. BDI_v1 Score Calculation Methodology

For a barrier category with at least **3 unique reports** ($n \ge 3$) within the active date filter:

$$\text{BDI} = \min\left(100, \, \max\left(0, \, \text{Round}\left(0.30 \cdot R + 0.25 \cdot P + 0.25 \cdot U + 0.20 \cdot S + T_{\text{adj}}\right)\right)\right)$$

### Component Definitions & Normalization Formulas:

1. **Recurrence Score ($R$)**  
   Measures how frequently the barrier appears across unique reports relative to a baseline threshold of 10 reports.
   $$R = \min\left(100, \, \frac{\text{Unique Reports}}{10} \times 100\right)$$

2. **Temporal Persistence Score ($P$)**  
   Measures whether the barrier concern persists across multiple time windows (e.g., calendar months) within the selected date range.
   $$P = \frac{\text{Active Time Windows with Barrier}}{\text{Total Active Windows in Period}} \times 100$$

3. **Unresolved Status Score ($U$)**  
   Measures the proportion of reports associated with the barrier that remain unresolved or require action (`action_status != 'CLOSED'`).
   $$U = \frac{\text{Unresolved Reports}}{\text{Unique Reports}} \times 100$$

4. **SIF-Potential Association Score ($S$)**  
   Measures the proportion of reports associated with the barrier that involve SIF-Potential precursor conditions.
   $$S = \frac{\text{SIF-Potential Reports}}{\text{Unique Reports}} \times 100$$

5. **Trend Adjustment ($T_{\text{adj}}$)**  
   Adjusts score based on linear trend direction over active time windows:
   - **Increasing Trend** (+10 points): Barrier occurrence frequency is growing over time.
   - **Stable Trend** (0 points): Barrier occurrence frequency remains constant.
   - **Decreasing Trend** (-10 points): Barrier occurrence frequency is declining over time.

---

## 5. Sample Sufficiency & Small-Sample Protection

| Sample Size ($n = \text{Unique Reports}$) | BDI Score | Status Tag | Guidance |
| :--- | :--- | :--- | :--- |
| $n < 3$ | `null` | `INSUFFICIENT_DATA` | Insufficient evidence to establish barrier degradation. Expose counts only. |
| $3 \le n < 5$ | Calculated ($0\text{--}100$) | `LIMITED_DATA` | BDI available with disclaimer regarding limited sample size. |
| $n \ge 5$ | Calculated ($0\text{--}100$) | `SUFFICIENT_DATA` | Statistically reliable descriptive indicator. |

---

## 6. AI vs. HSE Review Distinction & Auditability

1. **AI Observations**: Stored in `ai_barriers` (`ai_analyses.barrier_concerns_json`).
2. **HSE Validations**: Stored in `hse_barriers` (`hse_reviews.modified_barrier_concerns_json`).
3. **Effective Analytical Barrier**: Derived via `get_effective_barriers()` (uses HSE validation when available, falling back to AI prediction).
4. **Original Preservation**: Original AI outputs are never overwritten during HSE review.

---

## 7. Mandatory Evidence Payload Schema

Every BDI API response exposes the full underlying evidence package:

```json
{
  "barrier": "Energy Isolation",
  "bdi": 68,
  "status": "SUFFICIENT_DATA",
  "period": { "start_date": "2026-01-01", "end_date": "2026-09-17" },
  "evidence": {
    "total_occurrences": 8,
    "unique_reports": 8,
    "unique_sites": 3,
    "unique_activities": 4,
    "unresolved_count": 5,
    "sif_potential_count": 5,
    "persistence_windows": "4 of 6 months",
    "trend_direction": "Increasing",
    "contributing_report_ids": [101, 104, 112, 120, 135, 142, 150, 168]
  },
  "methodology_version": "BDI_v1",
  "limitations": [
    "BDI is a descriptive indicator of historical reporting patterns, not a predictive safety model.",
    "Barrier observations depend on reporting thoroughness and HSE review coverage."
  ]
}
```
