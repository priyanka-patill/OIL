# Part 4F — HSE Action Center & Full System Integration Documentation

## 1. Architectural Overview & Executive Summary

Part 4F is the final integration, presentation, navigation, and operational workflow layer of Part 4 for the Oil India Limited (OIL) HSE Safety Intelligence Platform.

It brings together Parts 3A–3E (Safety Intelligence, Hotspots, Barriers/BDI, Escalation) and Parts 4A–4E (Intervention Recommendations, HSE Review, Action Management, SLA Monitoring, Completion/Verification & Impact Tracking) into a unified **HSE Action Center** (`/action-center`).

```
+-----------------------------------------------------------------------------------+
|                         COMPLETE END-TO-END WORKFLOW                              |
+-----------------------------------------------------------------------------------+
|  PART 3E: Safety Intelligence Dashboard (Hotspots, Barriers/BDI, Escalations)    |
|        |                                                                          |
|        v                                                                          |
|  PART 4A: Evidence-Based Intervention Recommendation Foundation                   |
|        |                                                                          |
|        v                                                                          |
|  PART 4B: Human-in-the-Loop HSE Review & Decision (ACCEPT / MODIFY / REJECT)      |
|        |                                                                          |
|        v                                                                          |
|  PART 4C: Operational Action Creation, Department Scoping & Assignment            |
|        |                                                                          |
|        v                                                                          |
|  PART 4D: SLA Monitoring, Due-Soon Notifications & Multi-Level Escalation Outbox  |
|        |                                                                          |
|        v                                                                          |
|  PART 4E: Completion, HSE Verification, Reopen Cycles & Impact Analysis           |
|        |                                                                          |
|        v                                                                          |
|  PART 4F: HSE ACTION CENTER (Unified Operational Dashboard & Navigation)          |
+-----------------------------------------------------------------------------------+
```

---

## 2. HSE Action Center Core Capabilities & Features

### 2.1 8 Primary Operational KPI Summary Cards
All KPI metrics are aggregated authoritatively from backend database records. Hardcoded or client-side date arithmetic KPI counts are strictly prohibited.
1. **Pending Reviews**: Count of intervention recommendations awaiting HSE review (`PENDING_HSE_VALIDATION`).
2. **Active Actions**: Count of active operational actions (`IN_PROGRESS`, `ASSIGNED`, `ON_HOLD`, `REOPENED`).
3. **Due Soon**: Count of active actions with Part 4D SLA status `DUE_SOON`.
4. **Overdue**: Count of active actions with Part 4D SLA status `OVERDUE`.
5. **Completed**: Count of actions in `COMPLETED` status.
6. **Verification Pending**: Count of actions in `VERIFICATION_PENDING` status awaiting HSE verification.
7. **Impact Available**: Count of actions with Part 4E observational impact data marked `SUFFICIENT`.
8. **Insufficient Data**: Count of actions with Part 4E impact data marked `INSUFFICIENT_DATA`.

### 2.2 Operational Sections
- **Pending HSE Reviews**: Displays pending interventions with priority suggestions, barrier categories, report origins, and quick links to review screens.
- **My Actions & Active Actions**: Displays actions assigned to the authenticated user with SLA countdown badges, department scoping, and direct links to action detail records.
- **Overdue Actions & Escalation Outbox**: Exposes SLA days overdue, current escalation level ($1, 2, 3$), trigger timestamps, escalation reasons, and recipient roles.
- **Verification Pending**: Displays completed work reports from assignees, attached evidence indicators, and direct links to the HSE verification workflow.
- **Intervention Impact & Insufficient Data**: Displays Before/After report counts, observed trend badges, sample size evaluations, sufficiency rationales, and methodology disclaimers.
- **Recent Operational Activity Stream**: Real-time audit trail feed tracking action assignments, status transitions, review decisions, and SLA events.

---

## 3. Security, RBAC & Aggregate Data Leakage Safeguards

- **Strict Site-Level Scoping**: Non-admin users restricted to specific sites (e.g., `Digboi Refinery` or `Duliajan Field`) only receive aggregate KPI summary counts and section lists scoped strictly to their authorized site.
- **No Aggregate Leakage**: Summary counts are calculated **AFTER** RBAC authorization scoping is applied. The system never computes global totals and filters them client-side.
- **URL State Persistence**: Filter selections (Site, Department, Priority, Status, SLA Status) are persisted in URL query parameters (`/action-center?site=Digboi%20Refinery&sla_status=OVERDUE`), enabling authorized deep-linking and bookmarking.

---

## 4. Methodology & Non-Causal Safeguards

- **Strict Descriptive Terminology**: All impact results rendered in the Action Center use non-causal language (*"Observed count changed from X to Y"*).
- **Forbidden Terms**: Words such as *"caused"*, *"prevented"*, *"eliminated"*, *"proven reduction"*, or *"reduced fatality risk"* are strictly prohibited.
- **Insufficient Data Preservation**: Impact records marked `INSUFFICIENT_DATA` are explicitly highlighted with explanation banners rather than displaying misleading 100% improvement percentages.
- **Anti-Leakage**: Metadata fields `source_sheet` and `"12_High_Potential"` have zero influence on Action Center metrics, counts, or section lists.

---

## 5. API Endpoints Specification

| Endpoint | Method | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/action-center/summary` | `GET` | Authenticated | Returns authoritative, RBAC-scoped summary counts for all 8 KPI cards. |
| `/api/action-center/sections` | `GET` | Authenticated | Returns structured operational lists for Pending Reviews, My Actions, Overdue Actions, Verification Pending, Impact Analyses, and Activity Audit Stream. |

---

## 6. End-to-End Operational Validation

The system has been validated through full end-to-end integration tests:
1. SIF Precursor Report logged in Part 3.
2. AI/System generates Evidence-Based Intervention in Part 4A.
3. HSE Reviewer accepts/modifies intervention in Part 4B.
4. Operational Action created and assigned in Part 4C.
5. Time-aware SLA monitoring tracks due-soon and overdue states with automated escalations in Part 4D.
6. Assignee completes work; HSE Reviewer verifies and triggers Before/After Impact Analysis in Part 4E.
7. HSE Action Center reflects real-time status across all 12 stages in Part 4F.
