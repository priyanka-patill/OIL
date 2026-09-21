# PART 4D — SLA MONITORING & ESCALATION ARCHITECTURE & SPECIFICATION

## 1. Executive Overview

Part 4D introduces a time-aware SLA Monitoring & Automated Escalation Engine to the Oil India Limited (OIL) HSE Safety Intelligence Platform. Building upon the Part 4C Action Lifecycle, Part 4D tracks assigned action progress against operational due dates, calculates backend SLA statuses (`ACTIVE`, `DUE_SOON`, `OVERDUE`, `COMPLETED`, `CANCELLED`), classifies completion timing (`COMPLETED_ON_TIME` vs. `COMPLETED_LATE`), and triggers idempotent reminder and multi-level escalation events.

---

## 2. SLA Architecture & Data Models

### 2.1 Database Entities (`backend/database/models.py`)

1. **`ActionSLA`**: 1-to-1 relationship with `Action`.
   - `sla_start_at`: UTC timestamp set when action is assigned.
   - `due_at`: UTC target completion deadline.
   - `sla_status`: `SLAStatus` Enum (`NOT_STARTED`, `ACTIVE`, `DUE_SOON`, `OVERDUE`, `COMPLETED`, `CANCELLED`).
   - `due_soon_threshold_hours`: Window (default 24h) before deadline to enter `DUE_SOON` status.
   - `current_escalation_level`: Escalation level counter (0, 1, 2, 3).
   - `last_evaluated_at`: Last evaluation timestamp.
   - `completion_timing`: `SLACompletionTiming` Enum (`NOT_COMPLETED`, `COMPLETED_ON_TIME`, `COMPLETED_LATE`).
   - `completed_at`: Completion timestamp.
   - `reminder_count`: Idempotent count of due-soon reminder events emitted.

2. **`ActionReminder`**: Outbox audit log for due-soon reminders.
   - `action_id`, `action_sla_id`, `sent_at`, `recipient_user_id`, `recipient_role`, `message`, `channel`.

3. **`ActionEscalation`**: Outbox audit log for multi-level escalations.
   - `action_id`, `action_sla_id`, `escalation_level` (1, 2, or 3), `escalation_reason`, `triggered_at`, `target_role`, `target_user_id`, `message`.

4. **`SLAConfig`**: Operational SLA configuration matrix by priority level.

---

## 3. SLA Rules & Threshold Logic

### 3.1 SLA Clock & Due Date Resolution
- When an action transitions to `ASSIGNED`, `sla_start_at` is set to UTC server `datetime.now(timezone.utc)`.
- Operational `due_date` (YYYY-MM-DD) is converted to end-of-day UTC deadline (`23:59:59 UTC`).
- If no explicit `due_date` is provided, default priority duration (HIGH: 3 days, MEDIUM: 7 days, LOW: 14 days) is added to `sla_start_at`.

### 3.2 Backend Status Evaluation (`backend/services/sla_service.py`)
- **`ACTIVE`**: Current UTC time is before `due_at - due_soon_threshold_hours`.
- **`DUE_SOON`**: Remaining hours $\le$ `due_soon_threshold_hours` (default 24 hours) and status is not completed/cancelled.
- **`OVERDUE`**: Current UTC time $> `due_at` and action is not completed/cancelled.
- **`COMPLETED`**: Action transitioned to `COMPLETED` or `VERIFIED`.
  - **`COMPLETED_ON_TIME`**: `completed_at <= due_at`.
  - **`COMPLETED_LATE`**: `completed_at > due_at`.

### 3.3 Multi-Level Escalation Rules
When an action becomes `OVERDUE`, escalations fire idempotently based on overdue duration:
- **Level 1 Escalation**: Overdue $\ge 24$ hours ($\ge 1$ day). Targets Assigned User & Department Lead.
- **Level 2 Escalation**: Overdue $\ge 48$ hours ($\ge 2$ days). Targets Department Manager & HSE Officer.
- **Level 3 Escalation**: Overdue $\ge 72$ hours ($\ge 3$ days). Targets HSE Director & Executive Oversight.

### 3.4 Idempotency & Delayed Scheduler Recovery
- SLA status evaluation is fully idempotent. If evaluated multiple times within the same state, duplicate reminder or escalation outbox entries are prevented.
- If a background evaluator runs after a multi-day delay, missing lower-level escalations (e.g. L1 and L2) are emitted sequentially up to the current overdue duration.

---

## 4. Anti-Leakage Enforcement
- SLA calculations and escalation levels rely strictly on time deltas, operational priority, and due dates.
- Data features `source_sheet` and `"12_High_Potential"` are strictly prohibited from influencing SLA statuses or escalation levels.

---

## 5. API Endpoints (`backend/api/actions.py`)

- `GET /api/actions/sla/summary`: Aggregated SLA dashboard summary metrics (`active`, `due_soon`, `overdue`, `completed_on_time`, `completed_late`).
- `POST /api/actions/sla/evaluate`: Evaluates all active SLAs or a specific action ID.
- `GET /api/actions/{id}/sla`: Detailed SLA status, countdown timer, and metrics for a specific action.
- `GET /api/actions/{id}/sla/history`: Outbox timeline of reminder and escalation events.

---

## 6. Verification & Readiness

- All unit, integration, idempotency, delayed scheduler recovery, and anti-leakage tests pass 100% green (`tests/test_part4d_sla_monitoring.py`).
- Platform status: **`READY FOR PART 4E`**.
