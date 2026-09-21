# Analytical Prioritization Methodology Specification (`PRI_v1`)

**Project**: Oil India Limited (OIL) HSE Safety Intelligence Platform  
**Version**: `PRI_v1`  
**Date**: September 17, 2026  
**Status**: Active Methodology Specification

---

## 1. Purpose & Analytical Scope

The **Analytical Prioritization Framework (`PRI_v1`)** provides a transparent, evidence-backed priority indicator to help HSE managers and safety engineers identify analytical entities (Equipment, Site, Activity, Department, Location) that warrant further review.

### Core Objectives:
1. **Descriptive Prioritization**: Analytical Priority is a descriptive evidence indicator intended to organize HSE review workflows. It is **NOT** a risk score, accident probability, or fatality forecast.
2. **Double-Counting Prevention**: Reuses SIF precursor density (Part 3B), Barrier Degradation Index (Part 3C), and Potential Escalation Indicators (Part 3D) without double-counting identical evidence components.
3. **Transparent Ordinal Tiers**: Uses 4 clear, evidence-based priority tiers rather than arbitrary percentage scores:
   - `HIGH_PRIORITY`: Multiple escalation indicators present AND high SIF density or degraded barrier.
   - `MEDIUM_PRIORITY`: At least 1 escalation indicator present OR moderate SIF density.
   - `LOW_PRIORITY`: Standard precursor reporting with zero active escalation indicators.
   - `INSUFFICIENT_DATA`: Fewer than 3 unique reports ($n < 3$).

---

## 2. Priority Tier Assignment Matrix

| Unique Reports ($n$) | Active Escalation Indicators | SIF Precursor Density | BDI Status / Score | Priority Tier (`PRI_v1`) |
| :--- | :--- | :--- | :--- | :--- |
| $n < 3$ | Any | Any | Any | `INSUFFICIENT_DATA` |
| $n \ge 3$ | $\ge 3$ indicators | $> 20.0\%$ OR BDI $\ge 60$ | High Concern | `HIGH_PRIORITY` |
| $n \ge 3$ | 1 to 2 indicators | $> 10.0\%$ OR BDI $\ge 40$ | Moderate Concern | `MEDIUM_PRIORITY` |
| $n \ge 3$ | 0 indicators | $\le 10.0\%$ AND BDI $< 40$ | Low Concern | `LOW_PRIORITY` |

---

## 3. Double-Counting Prevention Strategy

To ensure mathematical and methodological rigor:
1. **SIF Density (Part 3B)**: Provides the baseline proportion of SIF-Potential precursor reports ($\frac{\text{SIF Reports}}{\text{Analyzed Reports}}$).
2. **BDI (Part 3C)**: Incorporates barrier-specific persistence and unresolved status at the barrier level.
3. **Escalation Indicators (Part 3D)**: Evaluates entity-level cross-report recurrence, persistent exposure, and trend direction.
4. **Integration Rule**: Priority tiers map entity-level escalation indicators alongside Part 3B density and Part 3C BDI without summing or multiplying raw overlapping counts.

---

## 4. Zero Data Leakage & Security

- **Zero Leakage**: `source_sheet` and `"12_High_Potential"` are 100% excluded from priority assignments.
- **RBAC Enforcement**: Prioritization calculations strictly observe site and department access boundaries established by user roles (`HSE_USER` vs `ADMIN`).

---

## 5. Auditability Payload Schema

Every Analytical Priority API response exposes the complete supporting evidence payload:

```json
{
  "entity_type": "equipment",
  "entity_id": "P-101A",
  "entity_name": "P-101A",
  "priority_tier": "HIGH_PRIORITY",
  "sample": {
    "total_reports": 6,
    "analyzed_reports": 6,
    "sif_potential_count": 3,
    "sif_density": 0.50
  },
  "escalation_summary": {
    "status": "MULTIPLE_ESCALATION_INDICATORS_PRESENT",
    "active_indicators_count": 4,
    "active_indicators": ["REPEATED_REPORTS", "UNRESOLVED_ISSUES", "REPEATED_BARRIER", "SIF_ASSOCIATION"]
  },
  "barrier_summary": {
    "top_barrier": "Energy Isolation",
    "bdi_score": 68
  },
  "contributing_report_ids": [101, 102, 103, 108, 114, 122],
  "methodology_version": "PRI_v1",
  "limitations": [
    "Analytical Priority is a descriptive evidence indicator intended to support HSE review.",
    "It is not a probability score for SIF, accident, or fatality events."
  ]
}
```
