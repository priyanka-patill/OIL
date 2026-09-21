# Part 4B — HSE Review & Approval Workflow
## OIL HSE SIF-Precursor Safety Intelligence Platform

### 1. Objective & Scope
Part 4B implements a human-in-the-loop **HSE Review & Approval Workflow** for AI/system-suggested intervention recommendations generated in Part 4A.

The primary objective is to allow authorized HSE reviewers to evaluate system recommendations and record an explicit, auditable human validation decision (`ACCEPT`, `MODIFY`, or `REJECT`).

#### Strict Boundary Enforcement:
- **NO Operational Action Creation** (belongs to Part 4C)
- **NO Action Assignment / User Task Allocation** (belongs to Part 4C)
- **NO SLA Monitoring / Timers / Overdue Escalation** (belongs to Part 4D)
- **NO Action Completion / Verification Workflows** (belongs to Part 4E)
- **NO Impact Measurement / Effectiveness Analytics** (belongs to Part 4E)
- **NO ML Model Retraining / Modification** (Part 1C model remains untouched)

---

### 2. Core Workflow Architecture

```
                 AI Recommendation (Part 4A)
                             │
                             ▼
                   PENDING_HSE_VALIDATION
                             │
                             ▼
                     Human HSE Review
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
          ACCEPT          MODIFY          REJECT
             │               │               │
             ▼               ▼               ▼
         ACCEPTED        MODIFIED        REJECTED
       Recommendation  Recommendation  Recommendation
             │               │               │
             └───────┬───────┘               ▼
                     ▼               Audit Log Only
              Future Part 4C          (Immutably Preserved)
```

---

### 3. Immutability Principle & AI/HSE Separation

1. **Original AI Recommendation Immutability**:
   The original fields on `InterventionRecommendation` (`title`, `recommendation_text`, `category`, `priority_suggestion`, `evidence_json`, `model_version`, `methodology_version`, `created_at`) are **NEVER overwritten or altered** when a review decision is recorded.

2. **Separate Review Entity (`HSEInterventionReview`)**:
   HSE review decisions, modified fields, rejection reasons, reviewer identity, and server-side timestamps are stored in a distinct table (`hse_intervention_reviews`), referencing the original intervention.

3. **Visual Distinction in UI**:
   The user interface clearly presents three distinct components:
   - **Original AI Recommendation** (Labeled "Original AI — Preserved")
   - **HSE Review Decision & Audit Details** (Reviewer Name, Review Timestamp, Review Comment)
   - **HSE Modified Recommendation** (if decision = `MODIFY`) or **Mandatory Rejection Justification** (if decision = `REJECT`)

---

### 4. Controlled Decision Workflows

#### A. ACCEPT Workflow
- **Validation**: Verifies reviewer authorization and site-level scope permissions.
- **Action**: Sets recommendation status to `ACCEPTED`.
- **Persistence**: Creates `HSEInterventionReview` record with `decision = ACCEPT`.
- **Audit**: Emits `INTERVENTION_REVIEW_ACCEPTED` audit log event.
- **Boundary**: Does NOT create an operational action or start SLA timers.

#### B. MODIFY Workflow
- **Validation**: Requires non-empty modified recommendation text or title.
- **Action**: Sets recommendation status to `MODIFIED`.
- **Persistence**: Stores `modified_title`, `modified_recommendation_text`, `modified_category`, `modified_priority`, `proposed_department`, and `proposed_due_date` in `HSEInterventionReview`.
- **Audit**: Emits `INTERVENTION_REVIEW_MODIFIED` audit log event.
- **Boundary**: Proposed department and due date are recorded as **HSE planning metadata**, NOT active operational SLA clocks or task assignments.

#### C. REJECT Workflow
- **Validation**: Requires a **mandatory, non-empty rejection reason**. Submissions with empty or whitespace-only reasons are rejected with HTTP 400 Bad Request.
- **Action**: Sets recommendation status to `REJECTED`.
- **Persistence**: Stores `rejection_reason` in `HSEInterventionReview`.
- **Audit**: Emits `INTERVENTION_REVIEW_REJECTED` audit log event.
- **Boundary**: Recommendation remains auditable in the database and audit trail; it is never deleted.

---

### 5. Database Schema

#### `HSEInterventionReview` Model (`backend/database/models.py`)

- **Table**: `hse_intervention_reviews`
- **Fields**:
  - `id`: Integer Primary Key
  - `intervention_id`: Foreign Key (`intervention_recommendations.id`, nullable=False, index=True)
  - `reviewer_id`: Foreign Key (`users.id`, nullable=False, index=True)
  - `decision`: Enum `HSEInterventionDecision` (`ACCEPT`, `MODIFY`, `REJECT`)
  - `rejection_reason`: Text (nullable=True, mandatory for `REJECT`)
  - `review_comment`: Text (nullable=True)
  - `modified_title`: String(255) (nullable=True)
  - `modified_recommendation_text`: Text (nullable=True)
  - `modified_category`: Enum `InterventionCategory` (nullable=True)
  - `modified_priority`: Enum `InterventionPriority` (nullable=True)
  - `proposed_owner_id`: Foreign Key (`users.id`, nullable=True)
  - `proposed_department`: String(100) (nullable=True)
  - `proposed_due_date`: String(20) (nullable=True)
  - `reviewed_at`: DateTime (server-side UTC timestamp)
  - `created_at`: DateTime (server-side UTC timestamp)

---

### 6. REST API Endpoints

#### `POST /api/interventions/{id}/review`
- **Description**: Submits an HSE review decision for an intervention.
- **Payload**:
  ```json
  {
    "decision": "ACCEPT | MODIFY | REJECT",
    "rejection_reason": "Mandatory if REJECT",
    "review_comment": "Optional audit comment",
    "modified_title": "Modified Title (if MODIFY)",
    "modified_recommendation_text": "Modified Text (if MODIFY)",
    "modified_category": "ENERGY_ISOLATION",
    "modified_priority": "HIGH",
    "proposed_department": "Operations",
    "proposed_due_date": "2026-10-15"
  }
  ```
- **Response**: Updated intervention object including `latest_review` payload.

#### `GET /api/interventions/{id}/review/history`
- **Description**: Retrieves complete review audit history for an intervention recommendation.

---

### 7. Authorization & Security

- **Server-Side Identity**: `reviewer_id` is extracted strictly from the verified JWT access token (`current_user.id`). Client payload attempts to tamper with reviewer identity are ignored.
- **Role-Based Access Control (RBAC)**: Review submission requires authorized HSE roles (`HSE_MANAGER`, `ADMIN`, `HSE_USER`).
- **Site-Level Authorization**: Users restricted to a specific site (e.g. `Duliajan Complex`) are blocked with HTTP 403 Forbidden from reviewing recommendations originating from another site (e.g. `Digboi Refinery`).

---

### 8. Target Leakage Safeguards

- **`source_sheet` and `"12_High_Potential"` Exclusion**: Neither column is evaluated during review processing, rejection validation, or priority modification.

---

### 9. Part 4C Integration Contract

Part 4B produces validated recommendation state for Part 4C (Action Management & Assignment):

1. **For `ACCEPTED` Recommendations**:
   - `intervention_id`: Integer
   - `original_recommendation`: Immutable AI Title, Text, Category, Priority, Evidence
   - `review_decision`: `ACCEPT`
   - `reviewer_id` & `reviewed_at`: Validated reviewer details

2. **For `MODIFIED` Recommendations**:
   - `intervention_id`: Integer
   - `original_recommendation`: Immutable AI Title, Text, Category, Priority, Evidence
   - `review_decision`: `MODIFY`
   - `approved_recommendation`: Modified Title, Text, Category, Priority
   - `proposed_department` & `proposed_due_date`: Planning metadata ready for action assignment

3. **For `REJECTED` Recommendations**:
   - `intervention_id`: Integer
   - `review_decision`: `REJECT`
   - `rejection_reason`: Immutable audit justification (Excluded from action creation)
