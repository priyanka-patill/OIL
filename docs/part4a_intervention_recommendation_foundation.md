# Part 4A — Intervention Recommendation Foundation
## OIL HSE SIF-Precursor Safety Intelligence Platform

### 1. Objective & Scope
Part 4A establishes a deterministic, evidence-based **Intervention Recommendation Layer** bridging Parts 2 and 3 Safety Intelligence findings with future HSE review processes.

The primary objective is to convert actual findings—such as SIF predictions, Life-Saving Rule (LSR) breaches, hazard profiles, recurring patterns, Barrier Degradation Index (BDI) scores, and potential escalation indicators—into structured, traceable, AI/system-suggested interventions requiring HSE validation.

#### Boundary Enforcement (Strict Exclusions):
- **NO Action Creation / Tasks** (belongs to Part 4C)
- **NO Action Assignment / User Allocation** (belongs to Part 4C)
- **NO Status Lifecycles (IN_PROGRESS, COMPLETED, OVERDUE)** (belongs to Part 4C/4E)
- **NO Due Dates / SLA Reminders / Escalations** (belongs to Part 4D)
- **NO Verification / Completion Workflows** (belongs to Part 4E)
- **NO Impact Measurement / Effectiveness Scoring** (belongs to Part 4E)
- **NO ML Model Modification / Retraining** (Part 1C model remains untouched)

---

### 2. Architectural Blueprint

```
                      PART 2C
                   AI Analysis
                       │
                       │
                       ▼
                ┌───────────────┐
                │ Safety Report │
                └───────┬───────┘
                        │
                        ▼
                  PART 3A–3D
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   Recurring Pattern  Barrier      Escalation
          │             │             │
          └─────────────┼─────────────┘
                        ▼
               Intervention Engine
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
         Category    Evidence    Priority
            │           │           │
            └───────────┼───────────┘
                        ▼
            Intervention Recommendation
                        │
                        ▼
         "HSE Validation Required"
                        │
                        ▼
                  STOP PART 4A
```

---

### 3. Database Schema & Data Models

#### `InterventionRecommendation` Model (`backend/database/models.py`)

- **Table**: `intervention_recommendations`
- **Fields**:
  - `id`: Integer Primary Key
  - `recommendation_number`: Unique business key (e.g. `REC-2026-00042`)
  - `report_id`: Foreign Key (`safety_reports.id`)
  - `analysis_id`: Foreign Key (`ai_analyses.id`, optional)
  - `recurring_pattern_id`: Foreign Key (`recurring_patterns.id`, optional)
  - `barrier_category`: String (optional)
  - `title`: String (e.g. "Verify Energy Isolation and LOTO Controls")
  - `category`: Enum `InterventionCategory`
  - `recommendation_text`: Text (Operational guidance)
  - `rationale`: Text (Analytical rationale & evidence basis)
  - `priority_suggestion`: Enum `InterventionPriority` (`HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT_DATA`)
  - `evidence_summary`: String
  - `evidence_json`: Text (JSON string containing full evidence payload)
  - `evidence_count`: Integer
  - `first_observed`: String / ISO Date
  - `latest_observed`: String / ISO Date
  - `sif_classification`: String (`SIF-Potential`, `Non-SIF-Potential`)
  - `hazards_json`: Text (JSON array of hazards)
  - `life_saving_rules_json`: Text (JSON array of LSRs)
  - `bdi_score`: Float (optional BDI score snapshot)
  - `escalation_indicators_json`: Text (JSON array of escalation indicators)
  - `model_version`: String (`sif_model_v1`)
  - `analytics_version`: String (`safety_intelligence_v1`)
  - `methodology_version`: String (`intervention_rules_v1`)
  - `status`: Enum `InterventionStatus` (`GENERATED`, `PENDING_HSE_VALIDATION`)
  - `created_at` / `updated_at`: DateTime ISO Timestamps

---

### 4. Controlled Intervention Categories

1. `ENERGY_ISOLATION` — Lockout/Tagout (LOTO), electrical/mechanical zero energy verification.
2. `CONFINED_SPACE_CONTROL` — Gas testing, atmospheric monitoring, entry permits, emergency rescue.
3. `GAS_TESTING` — Atmospheric testing, continuous gas monitoring, hot work gas checks.
4. `WORKING_AT_HEIGHT_CONTROL` — Full body harness, anchor points, scaffolding inspections, edge protection.
5. `HOT_WORK_CONTROL` — Hot work permit, fire watch, combustible clearing, spark containment.
6. `LIFTING_CONTROL` — Rigging inspection, crane load chart compliance, exclusion zones.
7. `PPE_CONTROL` — Specific PPE suitability, availability, and supervisor pre-job verification.
8. `PERMIT_CONTROL` — Permit to Work (PTW) issuance, risk assessment alignment, shift handover.
9. `MAINTENANCE` — Preventive maintenance scheduling, pressure testing, valve/flange checks.
10. `EQUIPMENT_GUARDING` — Rotating machinery guards, interlocks, barrier installation.
11. `SUPERVISION` — Pre-job safety toolbox talks, field supervision frequency, oversight.
12. `PROCEDURE_REVIEW` — Standard Operating Procedure (SOP) updates, management of change (MOC).
13. `OTHER` — General safety controls, housekeeping, traffic management.

---

### 5. Recommendation Engine & Rules Methodology

The recommendation engine (`backend/services/intervention_recommendation_engine.py`) operates deterministically without external generative AI APIs or target leakage:

- **Inputs**: Report description, AI analysis (SIF probability/classification, hazards, LSRs), Part 3 cross-report intelligence (recurring patterns, BDI, escalation indicators).
- **Leakage Protection**: Strictly ignores `source_sheet` and `"12_High_Potential"` features.
- **Rule Selection Matrix**: Matches primary barrier concern and LSR to specific operational templates (e.g. Energy Isolation → LOTO verification; Confined Space → Gas testing & entry permit verification).

---

### 6. Priority Suggestion Methodology

Priority is an analytical suggestion (`HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT_DATA`), NOT an action priority or SLA urgency:
- **`HIGH`**: SIF-Potential + (Recurring Pattern OR BDI ≥ 75.0 OR Escalation Indicators ≥ 2 OR Repeated Issue Ignored).
- **`MEDIUM`**: SIF-Potential without high recurrence OR Non-SIF with recurring pattern / BDI ≥ 50.0.
- **`LOW`**: Non-SIF single observation with standard control requirements.
- **`INSUFFICIENT_DATA`**: Report description < 10 words or missing critical classification context.

---

### 7. REST API Endpoints

- `POST /api/interventions/generate`: Generates recommendation for report ID.
- `GET /api/interventions`: List recommendations with category, priority, site, department filtering.
- `GET /api/interventions/{id}`: Fetch detailed recommendation profile.
- `GET /api/interventions/report/{report_id}`: Fetch all recommendations for a specific report.

---

### 8. Frontend Integration

- **Component**: `InterventionCard.jsx`
- **Banner**: **"AI-Suggested Intervention — HSE Validation Required"** prominently displayed on all cards.
- **Disclaimer**: *"This recommendation is generated from available safety intelligence evidence. It is a suggestion only and requires HSE review before any operational action is created."*
- **Panel**: `InterventionPanel.jsx` embedded directly into `ReportDetailPage.jsx`.

---

### 9. Verification & Validation

- Unit tests (`tests/test_part4a_interventions.py`) verify:
  1. ORM Model persistence
  2. Recommendation generation engine
  3. Evidence payload traceability
  4. Priority calculation rules
  5. Anti-leakage audit (zero `source_sheet` / `"12_High_Potential"` influence)
  6. Deduplication / Idempotency
  7. Site-level security authorization
  8. Real database record processing
