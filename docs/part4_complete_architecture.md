# Part 4 — Complete Architecture & End-to-End System Specifications

## 1. Complete Architecture Summary

Part 4 of the Oil India Limited (OIL) HSE Safety Intelligence Platform provides an end-to-end, human-in-the-loop operational workflow that converts analytical findings from Parts 1–3 into real organizational actions, time-aware SLA management, HSE verification, and observational impact tracking.

```
+---------------------------------------------------------------------------------------------------+
|                                  COMPLETE PART 4 ARCHITECTURE                                     |
+---------------------------------------------------------------------------------------------------+
|  4A — INTERVENTION RECOMMENDATION FOUNDATION                                                       |
|  Consumes Part 3 findings (Patterns, Barriers/BDI, Escalation) -> Suggests evidence-based rules.  |
|                                                                                                   |
|  4B — HSE REVIEW & APPROVAL WORKFLOW                                                              |
|  Human-in-the-Loop review screen -> HSE Reviewer decides (ACCEPT / MODIFY / REJECT).              |
|                                                                                                   |
|  4C — ACTION MANAGEMENT & ASSIGNMENT                                                              |
|  Converts approved interventions into operational Actions assigned to users & departments.        |
|                                                                                                   |
|  4D — SLA MONITORING & ESCALATION                                                                 |
|  Time-aware tracking -> SLA status (ACTIVE, DUE_SOON, OVERDUE), reminders, multi-level escalations|
|                                                                                                   |
|  4E — COMPLETION, VERIFICATION & IMPACT TRACKING                                                  |
|  Assignee completion -> Server timestamps -> HSE verification -> Reopen cycles -> Impact (v1).   |
|                                                                                                   |
|  4F — HSE ACTION CENTER                                                                           |
|  Unified operational dashboard -> Real-time KPIs, section lists, RBAC security, navigation.       |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Stage Breakdown

### Part 4A — Intervention Recommendation Foundation
- **Input**: Safety Intelligence findings (Recurring Patterns, Barrier Degradation Index, Risk Escalation).
- **Process**: Automated rule-based engine mapping precursor categories to evidence-based interventions.
- **Output**: `InterventionRecommendation` records in `PENDING_HSE_VALIDATION` state.

### Part 4B — HSE Review & Approval Workflow
- **Input**: `InterventionRecommendation`.
- **Process**: Human-in-the-loop review interface allowing authorized HSE users to inspect evidence, modify recommendations, or state rejection reasons.
- **Output**: `HSEInterventionReview` audit log (`ACCEPT`, `MODIFY`, `REJECT`).

### Part 4C — Action Management & Assignment
- **Input**: Accepted or Modified Interventions.
- **Process**: Operational action creation, priority setting, department assignment, due date assignment.
- **Output**: `Action` records with full lifecycle tracking (`ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `CANCELLED`).

### Part 4D — SLA Monitoring & Escalation
- **Input**: `Action` records.
- **Process**: Time-aware SLA monitoring service (`sla_service.py`), background evaluation, due-soon reminders, multi-level escalations outbox.
- **Output**: `ActionSLA` state (`ACTIVE`, `DUE_SOON`, `OVERDUE`), `SLAReminderOutbox`, `SLAEscalationOutbox`, and completion timing (`COMPLETED_ON_TIME`, `COMPLETED_LATE`).

### Part 4E — Completion, Verification & Impact Tracking
- **Input**: Completed Actions.
- **Process**: Assignee completion submission $\rightarrow$ HSE verification or reopen decision $\rightarrow$ Observational Before/After Impact Engine (`impact_service.py`).
- **Output**: `ActionCompletionHistory` multi-cycle audit log, `ActionEvidence` attachments, and `ActionImpactAnalysis` snapshots (5 Safety Indicators, `SUFFICIENT` vs `INSUFFICIENT_DATA`, non-causal framing).

### Part 4F — HSE Action Center & Full System Integration
- **Input**: All outputs from Parts 3A–3E and Parts 4A–4E.
- **Process**: Unified operational dashboard (`/action-center`), authoritative backend KPI aggregation (`action_center.py`), site-scoped RBAC security, global filtering, cross-system navigation.
- **Output**: Enterprise HSE operational control center.

---

## 3. System Integrity & Compliance Rules

1. **Authoritative Backend**: All statuses, counts, and metrics are computed in backend services. No client-side date arithmetic or state fabrication.
2. **Strict Site RBAC**: Scoping is applied prior to counting to prevent aggregate data leakage.
3. **Non-Causal Language**: Zero positive causal assertions (*"caused"*, *"prevented"*, *"eliminated"*). All comparisons are descriptive (*"Observed count changed from X to Y"*).
4. **Data Sufficiency**: Small samples ($< 2$ reports) preserve `INSUFFICIENT_DATA` status.
5. **Anti-Leakage**: `source_sheet` and `"12_High_Potential"` metadata have zero influence on logic or metrics.
