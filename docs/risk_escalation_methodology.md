# Risk Escalation Methodology Specification (`RE_v1`)

**Project**: Oil India Limited (OIL) HSE Safety Intelligence Platform  
**Version**: `RE_v1`  
**Date**: September 17, 2026  
**Status**: Active Methodology Specification

---

## 1. Executive Summary & Purpose

The **Risk Escalation Methodology (`RE_v1`)** provides a transparent, evidence-based analytical framework for identifying safety precursors, barriers, equipment, or organizational entities that exhibit persistent, repeated, unresolved, or accelerating risk patterns across historical safety reports.

### Core Principles:
- **Descriptive & Non-Predictive**: Risk escalation is a descriptive summary of observed historical precursor evidence. It does **NOT** predict future accidents, fatalities, or SIF event probabilities.
- **Zero Arbitrary Probability Claims**: The system never outputs pseudo-scientific probabilities such as "Fatality Risk = 87%" or "Accident Likelihood = 72%".
- **Zero Subjective Blame**: Entities are evaluated using objective, auditable report counts and evidence flags. Entities are never labeled with punitive terms like "worst site" or "most dangerous department".
- **Small-Sample Protection**: Risk escalation requires a minimum evidence threshold of **3 unique reports** ($n \ge 3$). If fewer than 3 unique reports exist for an entity, the system outputs `status = "INSUFFICIENT_DATA"`.
- **Zero Data Leakage**: `source_sheet` and `"12_High_Potential"` are 100% excluded from all escalation logic, indicator scoring, and priority assignments.

---

## 2. Conceptual Safety Chain vs. Observed Report Evidence

```
Unsafe Condition / Act ──► Continued Exposure ──► Loss of Control ──► Potential SIF Event
                                  │
                                  ▼
           [ OBSERVED EVIDENCE IN HISTORICAL REPORTS ]
```

> [!IMPORTANT]
> The safety chain above represents a **conceptual safety framework**, not a deterministic or guaranteed sequence. Risk escalation indicators measure the *presence of observed report evidence* matching precursor exposure stages. They do **not** imply that an accident will definitely occur.

---

## 3. The 6 Evidence-Based Escalation Indicators

For any target analytical entity (Equipment, Site, Activity, Department, Location, Refinery Unit, Barrier), `RE_v1` evaluates 6 transparent evidence indicators:

| Indicator Key | Definition & Criterion | Input Data Source |
| :--- | :--- | :--- |
| `REPEATED_REPORTS` | Entity is associated with $\ge 3$ unique safety reports. | `SafetyReport` DTO records |
| `UNRESOLVED_ISSUES` | Entity has $\ge 1$ report requiring corrective action (`action_status != 'CLOSED'`). | `report.action_status` / `status` |
| `REPEATED_BARRIER` | Entity is associated with $\ge 2$ reports exhibiting a recurring barrier concern. | Part 3C Barrier Normalization Engine |
| `INCREASING_RECURRENCE` | Occurrence trend over active time windows is classified as `Increasing`. | Part 3B / 3C Time-Series Trend Engine |
| `SIF_ASSOCIATION` | Entity is associated with $\ge 1$ SIF-Potential precursor report. | `is_sif_hse()` fallback `is_sif_ai()` |
| `PERSISTENT_EXPOSURE` | Barrier concern or precursor condition observed across $\ge 2$ distinct calendar windows. | Report dates & multi-period occurrence matrix |

---

## 4. Overall Escalation Status Classification

Based on the evaluation of the 6 evidence indicators, an entity is assigned an overall escalation status:

| Unique Reports ($n$) | Active Indicators | Overall Escalation Status | Guidance |
| :--- | :--- | :--- | :--- |
| $n < 3$ | Any | `INSUFFICIENT_DATA` | Insufficient report evidence to evaluate escalation. Expose raw counts only. |
| $n \ge 3$ | 0 | `NO_ESCALATION` | Standard background precursor reporting. |
| $n \ge 3$ | 1 to 2 | `POTENTIAL_ESCALATION_INDICATORS_PRESENT` | Specific precursor patterns observed; routine HSE monitoring recommended. |
| $n \ge 3$ | $\ge 3$ | `MULTIPLE_ESCALATION_INDICATORS_PRESENT` | Multiple evidence indicators present; HSE review recommended. |

---

## 5. Sample Sufficiency & Missing Data Handling

1. **Small-Sample Protection**: Single-report ($n=1$) or two-report ($n=2$) entities are strictly protected from false escalation flags. They return `status = "INSUFFICIENT_DATA"`.
2. **Missing Dimension Fields**: If a report lacks equipment ID, location, or department, it is excluded from that specific dimension's escalation calculation without converting missing fields to zero.
3. **Missing Action Status**: If `action_status` is unpopulated, report status (`ACTION_REQUIRED`, `SUBMITTED`, etc.) is used as fallback.
4. **Duplicate Reports**: Reuses Part 3A deduplication clusters; exact duplicates do not artificially inflate repeated report counts.

---

## 6. Auditability & Evidence Payload Schema

Every escalation API response exposes the full underlying evidence package linking to raw database reports:

```json
{
  "entity_type": "equipment",
  "entity_id": "P-101A",
  "entity_name": "P-101A",
  "status": "MULTIPLE_ESCALATION_INDICATORS_PRESENT",
  "period": { "start_date": "2026-01-01", "end_date": "2026-09-17" },
  "sample": {
    "total_reports": 6,
    "analyzed_reports": 6,
    "sif_potential_count": 3
  },
  "indicators": [
    { "type": "REPEATED_REPORTS", "status": "PRESENT", "evidence": "6 unique reports" },
    { "type": "UNRESOLVED_ISSUES", "status": "PRESENT", "evidence": "2 unresolved reports" },
    { "type": "REPEATED_BARRIER", "status": "PRESENT", "evidence": "Energy Isolation in 4 reports" },
    { "type": "INCREASING_RECURRENCE", "status": "PRESENT", "evidence": "Occurrence trend is Increasing" },
    { "type": "SIF_ASSOCIATION", "status": "PRESENT", "evidence": "3 SIF-Potential reports" },
    { "type": "PERSISTENT_EXPOSURE", "status": "PRESENT", "evidence": "Observed across 3 calendar months" }
  ],
  "contributing_report_ids": [101, 102, 103, 108, 114, 122],
  "methodology_version": "RE_v1",
  "limitations": [
    "Escalation indicators describe observed historical precursor patterns, not future accident probabilities.",
    "Indicators depend on reporting thoroughness and corrective action tracking coverage."
  ]
}
```
