import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from backend.database.models import (
    Action, ActionStatus, ActionPriority,
    ActionSLA, ActionReminder, ActionEscalation, SLAConfig,
    SLAStatus, SLACompletionTiming, User, UserRole, AuditLog, utc_now
)

logger = logging.getLogger(__name__)

# Default SLA duration and due-soon thresholds (hours)
DEFAULT_PRIORITY_SLA_CONFIG = {
    "HIGH": {"duration_hours": 48, "due_soon_hours": 24},
    "MEDIUM": {"duration_hours": 72, "due_soon_hours": 24},
    "LOW": {"duration_hours": 168, "due_soon_hours": 48},
    "DEFAULT": {"duration_hours": 72, "due_soon_hours": 24}
}

# Configurable Escalation Overdue Duration Thresholds (hours)
ESCALATION_LEVEL_THRESHOLDS = {
    1: {"name": "Level 1 Escalation — Assignee & Direct Supervisor Notification", "overdue_hours": 24, "target_role": "HSE_USER"},
    2: {"name": "Level 2 Escalation — Department Manager & HSE Officer Alert", "overdue_hours": 48, "target_role": "HSE_MANAGER"},
    3: {"name": "Level 3 Escalation — Senior Refinery Management Alert", "overdue_hours": 72, "target_role": "ADMIN"}
}


def log_sla_audit_event(
    db: Session,
    user_id: Optional[int],
    action_name: str,
    action_id: int,
    metadata: Dict[str, Any]
):
    """Helper for logging consistent SLA audit events."""
    audit = AuditLog(
        user_id=user_id,
        action=action_name,
        entity_type="ACTION_SLA",
        entity_id=str(action_id),
        metadata_json=json.dumps(metadata)
    )
    db.add(audit)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime object is timezone-aware UTC."""
    if not dt:
        return None
    if not dt.tzinfo:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_due_date_to_utc(due_date_str: str) -> datetime:
    """Parse YYYY-MM-DD date string into UTC datetime at end of day (23:59:59 UTC)."""
    try:
        dt = datetime.strptime(due_date_str.strip(), "%Y-%m-%d")
        return datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc) + timedelta(days=3)


def get_priority_sla_config(db: Session, priority: str) -> dict:
    """Fetch SLA configuration for a priority level with configurable database overrides."""
    p_upper = priority.upper() if priority else "MEDIUM"
    cfg = db.query(SLAConfig).filter(SLAConfig.priority == p_upper).first()
    if cfg:
        return {
            "duration_hours": cfg.default_duration_hours,
            "due_soon_hours": cfg.due_soon_threshold_hours,
            "escalation_l1_hours": cfg.escalation_l1_overdue_hours,
            "escalation_l2_hours": cfg.escalation_l2_overdue_hours,
            "escalation_l3_hours": cfg.escalation_l3_overdue_hours,
        }
    defaults = DEFAULT_PRIORITY_SLA_CONFIG.get(p_upper, DEFAULT_PRIORITY_SLA_CONFIG["DEFAULT"])
    return {
        "duration_hours": defaults["duration_hours"],
        "due_soon_hours": defaults["due_soon_hours"],
        "escalation_l1_hours": 24,
        "escalation_l2_hours": 48,
        "escalation_l3_hours": 72,
    }


def initialize_sla_for_action(
    db: Session,
    action: Action,
    now: Optional[datetime] = None
) -> ActionSLA:
    """
    Initialize SLA record when action is assigned.
    SLA Clock starts at sla_start_at (server-side UTC timestamp).
    """
    if action.sla:
        return action.sla

    start_time = ensure_utc(now or utc_now())

    prio_str = action.priority.value if hasattr(action.priority, 'value') else str(action.priority)
    prio_cfg = get_priority_sla_config(db, prio_str)

    duration_minutes = prio_cfg["duration_hours"] * 60
    due_soon_minutes = prio_cfg["due_soon_hours"] * 60

    # Determine authoritative SLA Due Date from operational due date or duration
    if action.due_date:
        due_at_dt = parse_due_date_to_utc(action.due_date)
    else:
        due_at_dt = start_time + timedelta(minutes=duration_minutes)

    sla = ActionSLA(
        action_id=action.id,
        sla_status=SLAStatus.ACTIVE,
        sla_start_at=start_time,
        due_at=due_at_dt,
        sla_duration_minutes=duration_minutes,
        due_soon_threshold_minutes=due_soon_minutes,
        completion_timing=SLACompletionTiming.NOT_COMPLETED,
        current_escalation_level=0,
        reminder_count=0,
        escalation_count=0,
        created_at=start_time
    )

    db.add(sla)
    db.flush()

    log_sla_audit_event(
        db,
        user_id=action.created_by,
        action_name="ACTION_SLA_STARTED",
        action_id=action.id,
        metadata={
            "action_number": action.action_number,
            "sla_start_at": start_time.isoformat(),
            "due_at": due_at_dt.isoformat(),
            "duration_minutes": duration_minutes,
            "due_soon_threshold_minutes": due_soon_minutes
        }
    )

    db.commit()
    db.refresh(sla)
    logger.info(f"SLA initialized for Action #{action.id} ({action.action_number}) starting at {start_time.isoformat()} due at {due_at_dt.isoformat()}")
    return sla


def calculate_sla_status_and_times(
    sla: ActionSLA,
    action_status: ActionStatus,
    now: Optional[datetime] = None
) -> dict:
    """
    Pure backend calculation of authoritative SLA status, remaining time, and overdue duration.
    """
    current_time = ensure_utc(now or utc_now())
    due_dt = ensure_utc(sla.due_at)

    # 1. Cancelled Action State
    if action_status == ActionStatus.CANCELLED:
        return {
            "sla_status": SLAStatus.CANCELLED,
            "completion_timing": SLACompletionTiming.NOT_COMPLETED,
            "remaining_minutes": 0,
            "overdue_minutes": 0,
            "is_overdue": False
        }

    # 2. Completed Action State
    if action_status in (ActionStatus.COMPLETED, ActionStatus.VERIFICATION_PENDING, ActionStatus.VERIFIED):
        completed_time = ensure_utc(sla.completed_at or current_time)
        timing = SLACompletionTiming.COMPLETED_ON_TIME if completed_time <= due_dt else SLACompletionTiming.COMPLETED_LATE
        return {
            "sla_status": SLAStatus.COMPLETED,
            "completion_timing": timing,
            "remaining_minutes": 0,
            "overdue_minutes": max(0, int((completed_time - due_dt).total_seconds() / 60)) if timing == SLACompletionTiming.COMPLETED_LATE else 0,
            "is_overdue": timing == SLACompletionTiming.COMPLETED_LATE
        }

    # 3. Active / In-Progress / On-Hold Action State
    if current_time >= due_dt:
        overdue_mins = int((current_time - due_dt).total_seconds() / 60)
        return {
            "sla_status": SLAStatus.OVERDUE,
            "completion_timing": SLACompletionTiming.NOT_COMPLETED,
            "remaining_minutes": 0,
            "overdue_minutes": overdue_mins,
            "is_overdue": True
        }

    remaining_mins = int((due_dt - current_time).total_seconds() / 60)
    if remaining_mins <= sla.due_soon_threshold_minutes:
        return {
            "sla_status": SLAStatus.DUE_SOON,
            "completion_timing": SLACompletionTiming.NOT_COMPLETED,
            "remaining_minutes": remaining_mins,
            "overdue_minutes": 0,
            "is_overdue": False
        }

    return {
        "sla_status": SLAStatus.ACTIVE,
        "completion_timing": SLACompletionTiming.NOT_COMPLETED,
        "remaining_minutes": remaining_mins,
        "overdue_minutes": 0,
        "is_overdue": False
    }


def evaluate_action_sla(
    db: Session,
    action: Action,
    now: Optional[datetime] = None
) -> ActionSLA:
    """
    Authoritative SLA evaluation for a single action.
    Updates SLA status, completion timing, triggers reminders and multi-level escalations idempotently.
    """
    current_time = ensure_utc(now or utc_now())

    sla = action.sla
    if not sla:
        if action.status not in (ActionStatus.APPROVED, ActionStatus.CANCELLED):
            sla = initialize_sla_for_action(db, action, now=current_time)
        else:
            return None

    calc_res = calculate_sla_status_and_times(sla, action.status, now=current_time)
    new_sla_status = calc_res["sla_status"]
    new_completion_timing = calc_res["completion_timing"]

    old_sla_status = sla.sla_status
    sla.sla_status = new_sla_status
    sla.completion_timing = new_completion_timing
    sla.updated_at = current_time

    # Handle Completion Evaluation
    if action.status in (ActionStatus.COMPLETED, ActionStatus.VERIFICATION_PENDING, ActionStatus.VERIFIED):
        if not sla.completed_at:
            sla.completed_at = ensure_utc(action.completion_date or action.verified_at or current_time)
            due_dt = ensure_utc(sla.due_at)
            sla.completion_timing = SLACompletionTiming.COMPLETED_ON_TIME if sla.completed_at <= due_dt else SLACompletionTiming.COMPLETED_LATE

            log_sla_audit_event(
                db,
                user_id=action.assigned_user_id,
                action_name="ACTION_SLA_COMPLETED",
                action_id=action.id,
                metadata={
                    "action_number": action.action_number,
                    "completed_at": sla.completed_at.isoformat(),
                    "completion_timing": sla.completion_timing.value
                }
            )

    # Handle Active Due-Soon Reminder Evaluation (Idempotent)
    elif new_sla_status == SLAStatus.DUE_SOON and sla.reminder_count == 0:
        reminder = ActionReminder(
            action_id=action.id,
            sla_id=sla.id,
            reminder_type="DUE_SOON_REMINDER",
            scheduled_for=sla.due_at - timedelta(minutes=sla.due_soon_threshold_minutes),
            triggered_at=current_time,
            recipient_user_id=action.assigned_user_id,
            status="SENT_AUDIT",
            message=f"Due Soon Alert: Action {action.action_number} ('{action.title}') is due on {action.due_date} ({calc_res['remaining_minutes']} mins remaining)."
        )
        db.add(reminder)
        sla.reminder_count += 1
        sla.last_reminder_at = current_time

        log_sla_audit_event(
            db,
            user_id=None,
            action_name="ACTION_SLA_DUE_SOON",
            action_id=action.id,
            metadata={
                "action_number": action.action_number,
                "remaining_minutes": calc_res["remaining_minutes"],
                "due_at": sla.due_at.isoformat()
            }
        )

    # Handle Overdue & Idempotent Multi-Level Escalation Evaluation
    elif new_sla_status == SLAStatus.OVERDUE:
        if old_sla_status != SLAStatus.OVERDUE:
            log_sla_audit_event(
                db,
                user_id=None,
                action_name="ACTION_SLA_OVERDUE",
                action_id=action.id,
                metadata={
                    "action_number": action.action_number,
                    "overdue_minutes": calc_res["overdue_minutes"],
                    "due_at": sla.due_at.isoformat()
                }
            )

        overdue_hours = calc_res["overdue_minutes"] / 60.0
        prio_str = action.priority.value if hasattr(action.priority, 'value') else str(action.priority)
        prio_cfg = get_priority_sla_config(db, prio_str)

        l1_hrs = prio_cfg["escalation_l1_hours"]
        l2_hrs = prio_cfg["escalation_l2_hours"]
        l3_hrs = prio_cfg["escalation_l3_hours"]

        # Level 1 Escalation Check (Idempotent: triggers if overdue_hours >= l1_hrs and current_escalation_level < 1)
        if overdue_hours >= l1_hrs and sla.current_escalation_level < 1:
            esc_l1 = ActionEscalation(
                action_id=action.id,
                sla_id=sla.id,
                escalation_level=1,
                escalation_name=ESCALATION_LEVEL_THRESHOLDS[1]["name"],
                overdue_minutes_at_trigger=calc_res["overdue_minutes"],
                triggered_at=current_time,
                recipient_role_or_dept=f"Assignee ({action.assigned_user.name if action.assigned_user else action.assigned_user_id}) & Supervisor",
                status="TRIGGERED",
                reason=f"Action overdue by {int(overdue_hours)} hours (threshold: {l1_hrs}h)."
            )
            db.add(esc_l1)
            sla.current_escalation_level = 1
            sla.escalation_count += 1
            sla.last_escalation_at = current_time

            log_sla_audit_event(
                db,
                user_id=None,
                action_name="ACTION_ESCALATED_L1",
                action_id=action.id,
                metadata={"action_number": action.action_number, "level": 1, "overdue_hours": overdue_hours}
            )

        # Level 2 Escalation Check (Idempotent)
        if overdue_hours >= l2_hrs and sla.current_escalation_level < 2:
            esc_l2 = ActionEscalation(
                action_id=action.id,
                sla_id=sla.id,
                escalation_level=2,
                escalation_name=ESCALATION_LEVEL_THRESHOLDS[2]["name"],
                overdue_minutes_at_trigger=calc_res["overdue_minutes"],
                triggered_at=current_time,
                recipient_role_or_dept=f"Department Manager ({action.assigned_department}) & HSE Officer",
                status="TRIGGERED",
                reason=f"Action overdue by {int(overdue_hours)} hours (threshold: {l2_hrs}h)."
            )
            db.add(esc_l2)
            sla.current_escalation_level = 2
            sla.escalation_count += 1
            sla.last_escalation_at = current_time

            log_sla_audit_event(
                db,
                user_id=None,
                action_name="ACTION_ESCALATED_L2",
                action_id=action.id,
                metadata={"action_number": action.action_number, "level": 2, "overdue_hours": overdue_hours}
            )

        # Level 3 Escalation Check (Idempotent)
        if overdue_hours >= l3_hrs and sla.current_escalation_level < 3:
            esc_l3 = ActionEscalation(
                action_id=action.id,
                sla_id=sla.id,
                escalation_level=3,
                escalation_name=ESCALATION_LEVEL_THRESHOLDS[3]["name"],
                overdue_minutes_at_trigger=calc_res["overdue_minutes"],
                triggered_at=current_time,
                recipient_role_or_dept=f"Senior Refinery Management ({action.site})",
                status="TRIGGERED",
                reason=f"Action overdue by {int(overdue_hours)} hours (threshold: {l3_hrs}h)."
            )
            db.add(esc_l3)
            sla.current_escalation_level = 3
            sla.escalation_count += 1
            sla.last_escalation_at = current_time

            log_sla_audit_event(
                db,
                user_id=None,
                action_name="ACTION_ESCALATED_L3",
                action_id=action.id,
                metadata={"action_number": action.action_number, "level": 3, "overdue_hours": overdue_hours}
            )

    db.commit()
    db.refresh(sla)
    return sla


def evaluate_all_active_slas(db: Session, now: Optional[datetime] = None) -> dict:
    """
    Batch evaluate SLA state for all active non-completed actions safely.
    Handles multiple crossed thresholds and isolated error handling per action.
    """
    current_time = now or utc_now()
    active_actions = (
        db.query(Action)
        .filter(Action.status.notin_([ActionStatus.COMPLETED, ActionStatus.VERIFIED, ActionStatus.CANCELLED]))
        .all()
    )

    evaluated = 0
    updated = 0
    due_soon_cnt = 0
    overdue_cnt = 0
    escalated_cnt = 0

    for act in active_actions:
        try:
            sla = evaluate_action_sla(db, act, now=current_time)
            if sla:
                evaluated += 1
                if sla.sla_status == SLAStatus.DUE_SOON:
                    due_soon_cnt += 1
                elif sla.sla_status == SLAStatus.OVERDUE:
                    overdue_cnt += 1
                if sla.current_escalation_level > 0:
                    escalated_cnt += 1
        except Exception as e:
            logger.error(f"Error evaluating SLA for Action #{act.id}: {e}", exc_info=True)

    return {
        "success": True,
        "evaluated_count": evaluated,
        "due_soon_count": due_soon_cnt,
        "overdue_count": overdue_cnt,
        "escalated_count": escalated_cnt,
        "evaluated_at": current_time.isoformat()
    }


def get_sla_summary(db: Session, user: User) -> dict:
    """
    Backend aggregation of authoritative SLA summary metrics for Dashboard and Manager view.
    """
    query = db.query(ActionSLA).join(Action, ActionSLA.action_id == Action.id)

    # Site-level security scoping
    if user.role != UserRole.ADMIN and user.site:
        query = query.filter(Action.site == user.site)

    all_slas = query.all()

    active_cnt = 0
    due_soon_cnt = 0
    overdue_cnt = 0
    completed_on_time_cnt = 0
    completed_late_cnt = 0

    now = utc_now()
    for sla in all_slas:
        res = calculate_sla_status_and_times(sla, sla.action.status, now=now)
        st = res["sla_status"]
        tm = res["completion_timing"]

        if st == SLAStatus.ACTIVE:
            active_cnt += 1
        elif st == SLAStatus.DUE_SOON:
            due_soon_cnt += 1
        elif st == SLAStatus.OVERDUE:
            overdue_cnt += 1
        elif st == SLAStatus.COMPLETED:
            if tm == SLACompletionTiming.COMPLETED_ON_TIME:
                completed_on_time_cnt += 1
            else:
                completed_late_cnt += 1

    return {
        "active": active_cnt,
        "due_soon": due_soon_cnt,
        "overdue": overdue_cnt,
        "completed_on_time": completed_on_time_cnt,
        "completed_late": completed_late_cnt,
        "total_managed": len(all_slas)
    }
