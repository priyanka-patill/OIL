# Intervention Recommendation Generation Methodology
## Oil India Limited (OIL) HSE Safety Intelligence Platform

### 1. Objective
This document details the deterministic, evidence-based methodology used by the OIL HSE Safety Intelligence Platform to convert AI safety findings, precursor flags, Life-Saving Rule (LSR) breaches, and cross-report analytics into structured intervention recommendations.

Recommendations produced by this engine are **suggestions for HSE review** and **do not automatically create operational actions or tasks**.

---

### 2. Data Sources & Integration Framework

The recommendation engine consumes data exclusively from validated upstream platform modules:

1. **Part 1C ML Model**: SIF prediction score, SIF-Potential classification (`SIF-Potential` vs `Non-SIF-Potential`), model version metadata (`sif_model_v1`).
2. **Part 2C AI Safety Analysis**: Identified hazards, Life-Saving Rule mappings, barrier concerns, PPE flags, maintenance flags, supervisor negligence flags.
3. **Part 3A Cross-Report Intelligence**: Recurring pattern detection, pattern occurrence count, related report IDs, first/latest observation dates.
4. **Part 3C Barrier Intelligence**: Primary barrier category, Barrier Degradation Index (BDI_v1) score.
5. **Part 3D Potential Escalation Indicators**: Persistence indicators, barrier recurrence flags, repeated unresolved issue flags.

---

### 3. Target Leakage & Feature Safeguards

The recommendation generation pipeline enforces strict anti-leakage guards:
- **`source_sheet` exclusion**: The `source_sheet` metadata field is completely excluded from decision logic.
- **`12_High_Potential` exclusion**: No special-casing or inference is permitted based on sheet names or target-derived columns.
- **Deterministic Evaluation**: Given identical report content and analytics context, the engine produces identical, reproducible recommendations.

---

### 4. Rule Selection Matrix & Categories

| Secondary Rule / Trigger | Mapped Category | Title Template | Recommended Operational Interventions |
| :--- | :--- | :--- | :--- |
| **LSR / Barrier: Energy Isolation** | `ENERGY_ISOLATION` | Verify Energy Isolation and LOTO Controls | • Field verification of zero energy state before work.<br>• Review LOTO application & isolation tag compliance.<br>• Confirm authorized person sign-off. |
| **LSR / Barrier: Confined Space / Gas** | `CONFINED_SPACE_CONTROL` | Strengthen Confined Space Entry Verification | • Conduct atmospheric gas testing (O2, H2S, LEL).<br>• Verify active entry permit & attendant presence.<br>• Confirm emergency rescue equipment readiness. |
| **LSR / Barrier: Hot Work / Fire** | `HOT_WORK_CONTROL` | Reinforce Hot Work & Fire Prevention Controls | • Verify gas test results prior to hot work ignition.<br>• Clear 35ft radius of flammable materials.<br>• Station dedicated fire watch with extinguisher. |
| **LSR / Barrier: Height / Fall** | `WORKING_AT_HEIGHT_CONTROL` | Enforce Fall Protection & Height Controls | • 100% tie-off verification with double lanyards.<br>• Scaffolding green tag inspection before use.<br>• Guardrail & toe-board integrity check. |
| **LSR / Barrier: Lifting** | `LIFTING_CONTROL` | Audit Lifting Rigging & Exclusion Zones | • Inspect slings, shackles, and crane safety latches.<br>• Verify lifting permit and rigger certification.<br>• Establish barricaded drop zone under suspended loads. |
| **Precursor: PPE Non-Compliance** | `PPE_CONTROL` | Strengthen PPE Compliance Verification | • Inspect site-specific mandatory PPE availability.<br>• Conduct pre-task PPE suitability check.<br>• Supervisor verification before work authorization. |
| **Precursor: Maintenance Delay** | `MAINTENANCE` | Escalate Critical Maintenance & Guarding Audit | • Schedule immediate mechanical/electrical PM.<br>• Inspect protective covers & emergency stops.<br>• Issue safety lockout tag if equipment impaired. |
| **Precursor: Supervisor Negligence** | `SUPERVISION` | Enhance Pre-Job Supervision & Permit Checks | • Mandatory supervisor-led Tool Box Talk (TBT).<br>• On-site PTW requirement audit.<br>• Verify worker competency for high-risk tasks. |

---

### 5. Evidence & Traceability Payload Structure

Every generated recommendation attaches a traceable evidence payload:

```json
{
  "finding": "Recurring Energy Isolation concern across related observations",
  "evidence_summary": "6 related reports | 3 SIF-Potential | BDI: 78.5",
  "related_reports": [101, 114, 127, 131, 144, 152],
  "sif_classification": "SIF-Potential",
  "hazards": ["Electrical", "Energy"],
  "life_saving_rules": ["Energy Isolation"],
  "barrier_category": "Energy Isolation",
  "bdi_score": 78.5,
  "escalation_indicators": ["Repeated observations", "Unresolved issues"],
  "first_observed": "2026-01-15",
  "latest_observed": "2026-03-10",
  "model_version": "sif_model_v1",
  "analytics_version": "safety_intelligence_v1",
  "methodology_version": "intervention_rules_v1"
}
```

---

### 6. Handling Insufficient & Conflicting Data

- **Short / Vague Descriptions (<10 words)**: Categorized under `OTHER` with `INSUFFICIENT_DATA` priority.
- **Missing BDI / Escalation**: Fields set to `null` or empty arrays; priority relies on SIF classification and precursor flags without throwing errors.
- **Conflicting AI vs HSE Classifications**: Both classifications are explicitly preserved in evidence payload; recommendation title and priority transparently reflect AI predictions while flagging HSE status as pending.

---

### 7. Versioning & Governance

- **Recommendation Engine Version**: `intervention_rules_v1`
- **Analytics Pipeline Version**: `safety_intelligence_v1`
- **ML Model Version**: `sif_model_v1`

Any modifications to rule thresholds or categories require incrementing the methodology version string.
