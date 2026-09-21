# PART 4C — ACTION MANAGEMENT & ASSIGNMENT DOCUMENTATION

## 1. OBJECTIVE

Part 4C converts HSE-approved and HSE-modified intervention recommendations into actual organizational actions within the Oil India Limited (OIL) HSE Safety Intelligence platform.

The workflow path is:
```
HSE Approved Intervention
          ↓
     Create Action
          ↓
      Assign To
          ↓
     Department
          ↓
       Priority
          ↓
       Due Date
          ↓
    Action Lifecycle
```

Primary Goal: Execute and track operational safety actions resulting from HSE-validated interventions, preserving full traceability to the originating AI recommendations, HSE review decisions, evidence snapshots, and safety precursor reports.

---

## 2. ARCHITECTURE & IMMUTABILITY PRINCIPLE

Part 4C strictly preserves the immutability of upstream data layers:
1. **Original AI Recommendation**: AI recommendation text, priority, hazards, and evidence are preserved on `InterventionRecommendation`.
2. **HSE Review Decision**: Human-in-the-loop review decision (`ACCEPT`, `MODIFY`, `REJECT`), modified text, and proposed metadata are preserved on `HSEInterventionReview`.
3. **Operational Action**: Downstream organizational entity (`Action`) created only from ACCEPTED or MODIFIED interventions.

```
AI Evidence → AI Recommendation → HSE Review → Approved/Modified Intervention → Operational ACTION → (Future Part 4D SLA / Part 4E Impact)
```

---

## 3. ACTION DATABASE MODEL

Defined in `backend/database/models.py`:

- `Action`:
  - `id`: Integer primary key.
  - `action_number`: Unique human-readable identifier (e.g. `ACT-R1-ENER-0001`).
  - `intervention_id`: Foreign key to `intervention_recommendations.id` (mandatory link).
  - `report_id`: Foreign key to `safety_reports.id` (traceability to originating report).
  - `pattern_id`: String (Part 3 recurring pattern ID, if applicable).
  - `barrier_id`: String (Part 3 barrier category, if applicable).
  - `source_hse_review_id`: Foreign key to `hse_intervention_reviews.id`.
  - `title`: Operational title (pre-fills from HSE modified title or original AI title).
  - `description`: Operational description (pre-fills from HSE modified text or original AI text).
  - `assigned_user_id`: Foreign key to `users.id` (validated active user).
  - `assigned_department`: Department string (pre-fills from HSE proposal or report department).
  - `site`: Site scope (e.g. "Digboi Refinery").
  - `priority`: Controlled enum (`ActionPriority`: `HIGH`, `MEDIUM`, `LOW`).
  - `due_date`: Operational due date (`YYYY-MM-DD`).
  - `status`: Controlled enum (`ActionStatus`: `APPROVED`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`, `VERIFICATION_PENDING`, `VERIFIED`, `REOPENED`, `CANCELLED`).
  - `created_by`: Foreign key to creating user.
  - `created_at`, `updated_at`: Server-side UTC timestamps.
  - `start_date`, `completion_date`, `verified_at`, `reopened_at`, `cancelled_at`: Server-managed lifecycle timestamps.
  - `evidence_snapshot_json`: Immutable JSON snapshot of evidence payload at creation time.

- `ActionComment`:
  - Threaded user comments on an action for progress updates and context notes.

---

## 4. ACTION ELIGIBILITY & APPROVAL REQUIREMENT

Strict backend enforcement ensures:
- **ACCEPTED** interventions → Eligible for Action creation.
- **MODIFIED** interventions → Eligible for Action creation (pre-fills defaults from HSE modifications).
- **PENDING_HSE_VALIDATION** interventions → Rejected (HTTP 400 Bad Request: "HSE validation is required...").
- **REJECTED** interventions → Rejected (HTTP 400 Bad Request: "Cannot create action from REJECTED...").

---

## 5. STATUS LIFECYCLE & VALID TRANSITIONS

Valid state transitions matrix (`action_service.py`):
```
APPROVED → ASSIGNED, CANCELLED
ASSIGNED → IN_PROGRESS, ON_HOLD, CANCELLED
IN_PROGRESS → ON_HOLD, COMPLETED, CANCELLED
ON_HOLD → IN_PROGRESS, CANCELLED
COMPLETED → VERIFICATION_PENDING, VERIFIED, REOPENED, CANCELLED
VERIFICATION_PENDING → VERIFIED, REOPENED, CANCELLED
VERIFIED → REOPENED
REOPENED → IN_PROGRESS, ASSIGNED, CANCELLED
CANCELLED → REOPENED
```

Arbitrary status jumps (e.g., `ASSIGNED` → `VERIFIED` directly) are rejected by backend transition validation.

---

## 6. API SPECIFICATION

Endpoints exposed in `backend/api/actions.py`:

- `POST /api/actions`: Create operational action from intervention.
- `GET /api/actions`: List assigned actions with site/department/status/priority/search backend filters (Manager View).
- `GET /api/actions/my`: List actions assigned to current authenticated user (My Actions View).
- `GET /api/actions/{id}`: Get full action profile with source traceability, comments, and audit history.
- `PATCH /api/actions/{id}/status`: Transition status with comment and server timestamp recording.
- `PATCH /api/actions/{id}/assign`: Reassign action to active user & department.
- `PATCH /api/actions/{id}/priority`: Modify action priority.
- `PATCH /api/actions/{id}/due-date`: Modify operational due date.
- `POST /api/actions/{id}/comments`: Add comment to action thread.

---

## 7. AUTHORIZATION & SITE SECURITY

- `HSE_USER`: Can view and update assigned actions within their authorized site.
- `HSE_MANAGER` / `ADMIN`: Can create actions, reassign, modify priority/due date, and oversee actions across authorized scopes.
- IDOR Protection: Site scope is validated on detail access and list queries.

---

## 8. ANTI-LEAKAGE AUDIT

- `source_sheet` and `"12_High_Potential"` have ZERO influence on action creation, priority assignment, due date selection, or status lifecycle.

---

## 9. SCOPE BOUNDARIES

- **Part 4C Scope**: Operational action creation, assignment, lifecycle status management, due date storage, comments, audit logging, and UI detail views.
- **DO NOT INCLUDE IN PART 4C**:
  - SLA engine, SLA countdown, overdue alerts, automatic reminders, escalation schedulers (Part 4D).
  - Intervention effectiveness scoring, SIF recurrence comparison, before/after metrics (Part 4E).

---

## 10. FUTURE INTEGRATION CONTRACTS

### Part 4D Integration Contract (SLA Monitoring & Escalation)
Part 4D will consume:
- `Action.id`
- `Action.status`
- `Action.due_date`
- `Action.created_at`
- `Action.priority`
- `Action.assigned_user_id`
- `Action.assigned_department`
- `Action.site`

Part 4D will calculate:
- SLA countdown duration
- Due soon / overdue flags
- Escalation levels and automated reminder schedules

### Part 4E Integration Contract (Verification & Impact Analytics)
Part 4E will consume:
- `Action.id`
- `Action.completion_date`
- `Action.verified_at`
- `Action.intervention_id`
- `Action.report_id`
- `Action.barrier_id`

Part 4E will perform:
- Formal completion verification audit
- Pre vs Post intervention barrier degradation index (BDI) comparison
- SIF recurrence reduction scoring and intervention effectiveness tracking
