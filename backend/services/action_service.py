import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from backend.database.models import (
    Action, ActionComment, ActionStatus, ActionPriority,
    InterventionRecommendation, InterventionStatus, HSEInterventionReview, HSEInterventionDecision,
    SafetyReport, User, UserRole, AuditLog, ActionEvidence, ActionCompletionHistory, ActionImpactAnalysis, utc_now
)

logger = logging.getLogger(__name__)

# Valid Action Lifecycle Transitions Matrix
VALID_STATUS_TRANSITIONS = {
    ActionStatus.APPROVED: [ActionStatus.ASSIGNED, ActionStatus.CANCELLED],
    ActionStatus.ASSIGNED: [ActionStatus.IN_PROGRESS, ActionStatus.ON_HOLD, ActionStatus.CANCELLED],
    ActionStatus.IN_PROGRESS: [ActionStatus.ON_HOLD, ActionStatus.COMPLETED, ActionStatus.CANCELLED],
    ActionStatus.ON_HOLD: [ActionStatus.IN_PROGRESS, ActionStatus.CANCELLED],
    ActionStatus.COMPLETED: [ActionStatus.VERIFICATION_PENDING, ActionStatus.VERIFIED, ActionStatus.REOPENED, ActionStatus.CANCELLED],
    ActionStatus.VERIFICATION_PENDING: [ActionStatus.VERIFIED, ActionStatus.REOPENED, ActionStatus.CANCELLED],
    ActionStatus.VERIFIED: [ActionStatus.REOPENED],
    ActionStatus.REOPENED: [ActionStatus.IN_PROGRESS, ActionStatus.ASSIGNED, ActionStatus.CANCELLED],
    ActionStatus.CANCELLED: [ActionStatus.REOPENED],
}

def generate_action_number(db: Session, intervention: InterventionRecommendation) -> str:
    """Generate human-readable unique Action ID (e.g. ACT-000001 or ACT-R1-ENER-0001)."""
    count = db.query(Action).count() + 1
    report_prefix = f"R{intervention.report_id}" if intervention.report_id else "GEN"
    cat_code = str(intervention.category.value)[:4].upper() if hasattr(intervention.category, 'value') else "ACT"
    return f"ACT-{report_prefix}-{cat_code}-{count:04d}"

def log_audit_event(
    db: Session, 
    user_id: Optional[int], 
    action_name: str, 
    entity_id: str, 
    metadata: Dict[str, Any]
):
    """Utility helper for consistent audit logging across Action events."""
    audit = AuditLog(
        user_id=user_id,
        action=action_name,
        entity_type="ACTION",
        entity_id=entity_id,
        metadata_json=json.dumps(metadata)
    )
    db.add(audit)

def create_action_from_intervention(
    db: Session,
    intervention_id: int,
    created_by_user: User,
    assigned_user_id: int,
    assigned_department: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    initial_comment: Optional[str] = None
) -> Action:
    """
    Convert an HSE-approved or HSE-modified intervention recommendation into an operational Action.
    
    STRICT ELIGIBILITY RULES:
    - Only ACCEPTED or MODIFIED interventions can create actions.
    - PENDING_HSE_VALIDATION and REJECTED interventions MUST be rejected by the backend.
    """
    intervention = db.query(InterventionRecommendation).filter(
        InterventionRecommendation.id == intervention_id
    ).first()

    if not intervention:
        raise ValueError(f"Intervention recommendation #{intervention_id} not found.")

    # Rule 5: Action Eligibility Check
    if intervention.status == InterventionStatus.PENDING_HSE_VALIDATION:
        raise ValueError("HSE validation is required before an action can be created. Intervention status is PENDING_HSE_VALIDATION.")
    
    if intervention.status == InterventionStatus.REJECTED:
        raise ValueError("Cannot create action from REJECTED intervention recommendation.")

    if intervention.status not in (InterventionStatus.ACCEPTED, InterventionStatus.MODIFIED):
        raise ValueError(f"Intervention recommendation status '{intervention.status}' is not eligible for action creation.")

    # Rule 15: Validate Assigned User
    assigned_user = db.query(User).filter(User.id == assigned_user_id).first()
    if not assigned_user:
        raise ValueError(f"Assigned user #{assigned_user_id} does not exist.")
    if not assigned_user.is_active:
        raise ValueError(f"Assigned user '{assigned_user.name}' is inactive and cannot receive actions.")

    # Fetch latest HSE Review if available for defaults
    latest_review = (
        db.query(HSEInterventionReview)
        .filter(HSEInterventionReview.intervention_id == intervention_id)
        .order_by(desc(HSEInterventionReview.id))
        .first()
    )

    # Determine Title Default (Rule 13: HSE modified title takes priority over AI original title)
    if not title:
        if latest_review and latest_review.modified_title:
            final_title = latest_review.modified_title
        else:
            final_title = intervention.title
    else:
        final_title = title.strip()

    # Determine Description Default (Rule 14: HSE modified text takes priority)
    if not description:
        if latest_review and latest_review.modified_recommendation_text:
            final_description = latest_review.modified_recommendation_text
        else:
            final_description = intervention.recommendation_text
    else:
        final_description = description.strip()

    # Determine Department Default (Rule 16: HSE proposed department > report department > user department)
    if not assigned_department:
        if latest_review and latest_review.proposed_department:
            final_department = latest_review.proposed_department
        elif intervention.report and intervention.report.department:
            final_department = intervention.report.department
        else:
            final_department = assigned_user.department or "Operations"
    else:
        final_department = assigned_department.strip()

    # Determine Priority Default (Rule 18)
    if not priority:
        if latest_review and latest_review.modified_priority:
            raw_priority = str(latest_review.modified_priority.value if hasattr(latest_review.modified_priority, 'value') else latest_review.modified_priority)
        else:
            raw_priority = str(intervention.priority_suggestion.value if hasattr(intervention.priority_suggestion, 'value') else intervention.priority_suggestion)
        
        try:
            final_priority = ActionPriority(raw_priority.upper())
        except ValueError:
            final_priority = ActionPriority.MEDIUM
    else:
        try:
            final_priority = ActionPriority(priority.upper())
        except ValueError:
            raise ValueError(f"Invalid priority '{priority}'. Allowed: HIGH, MEDIUM, LOW.")

    # Determine Due Date Default (Rule 19)
    if not due_date:
        if latest_review and latest_review.proposed_due_date:
            final_due_date = latest_review.proposed_due_date
        else:
            final_due_date = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d")
    else:
        final_due_date = due_date.strip()

    # Determine Site from Report or User scope
    site = intervention.report.site if intervention.report else (created_by_user.site or "Digboi Refinery")

    action_num = generate_action_number(db, intervention)

    # Immutable evidence snapshot for historical traceability
    evidence_snapshot = {
        "intervention_id": intervention.id,
        "intervention_number": intervention.recommendation_number,
        "original_ai_title": intervention.title,
        "original_ai_recommendation": intervention.recommendation_text,
        "original_ai_priority": str(intervention.priority_suggestion.value if hasattr(intervention.priority_suggestion, 'value') else intervention.priority_suggestion),
        "hse_decision": str(latest_review.decision.value) if latest_review else str(intervention.status.value),
        "evidence_summary": intervention.evidence_summary,
        "sif_classification": intervention.sif_classification,
        "report_number": intervention.report.report_number if intervention.report else None,
    }

    action = Action(
        action_number=action_num,
        intervention_id=intervention.id,
        report_id=intervention.report_id,
        pattern_id=intervention.recurring_pattern_id,
        barrier_id=intervention.barrier_category,
        source_hse_review_id=latest_review.id if latest_review else None,
        title=final_title,
        description=final_description,
        assigned_user_id=assigned_user.id,
        assigned_department=final_department,
        site=site,
        priority=final_priority,
        due_date=final_due_date,
        status=ActionStatus.ASSIGNED,
        created_by=created_by_user.id,
        created_at=utc_now(),
        evidence_snapshot_json=json.dumps(evidence_snapshot)
    )

    db.add(action)
    db.flush()

    if initial_comment and initial_comment.strip():
        comment = ActionComment(
            action_id=action.id,
            user_id=created_by_user.id,
            comment=initial_comment.strip(),
            created_at=utc_now()
        )
        db.add(comment)

    # Rule 32: Audit log creation
    log_audit_event(
        db,
        user_id=created_by_user.id,
        action_name="ACTION_CREATED",
        entity_id=str(action.id),
        metadata={
            "action_number": action.action_number,
            "intervention_id": intervention.id,
            "assigned_user_id": assigned_user.id,
            "assigned_department": final_department,
            "priority": final_priority.value,
            "due_date": final_due_date
        }
    )

    db.commit()
    db.refresh(action)

    # Part 4D: Initialize SLA Clock on Action Assignment
    try:
        from backend.services import sla_service
        sla_service.initialize_sla_for_action(db, action)
    except Exception as e:
        logger.error(f"Failed to initialize SLA for Action #{action.id}: {e}", exc_info=True)

    logger.info(f"Action #{action.id} ({action.action_number}) created for Intervention #{intervention.id} assigned to User #{assigned_user.id}")
    return action

def update_action_status(
    db: Session,
    action_id: int,
    new_status: ActionStatus,
    user: User,
    comment_text: Optional[str] = None
) -> Action:
    """
    Transition action status across lifecycle with strict state transition validation and server-side timestamps.
    """
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    curr_status = action.status
    if curr_status == new_status:
        return action

    allowed_next = VALID_STATUS_TRANSITIONS.get(curr_status, [])
    if new_status not in allowed_next:
        raise ValueError(f"Invalid status transition from {curr_status.value} to {new_status.value}. Allowed next states: {[s.value for s in allowed_next]}.")

    # Update Server-Side Timestamps (Rules 24, 25, 70)
    now = utc_now()
    if new_status == ActionStatus.IN_PROGRESS and not action.start_date:
        action.start_date = now
    elif new_status == ActionStatus.COMPLETED:
        action.completion_date = now
    elif new_status == ActionStatus.VERIFIED:
        action.verified_at = now
    elif new_status == ActionStatus.REOPENED:
        action.reopened_at = now
    elif new_status == ActionStatus.CANCELLED:
        action.cancelled_at = now

    action.status = new_status
    action.updated_at = now

    if comment_text and comment_text.strip():
        comment = ActionComment(
            action_id=action.id,
            user_id=user.id,
            comment=comment_text.strip(),
            created_at=now
        )
        db.add(comment)

    log_audit_event(
        db,
        user_id=user.id,
        action_name="ACTION_STATUS_CHANGED",
        entity_id=str(action.id),
        metadata={
            "action_number": action.action_number,
            "old_status": curr_status.value,
            "new_status": new_status.value,
            "comment": comment_text
        }
    )

    db.commit()
    db.refresh(action)

    # Part 4D: Re-evaluate Action SLA upon status transition
    try:
        from backend.services import sla_service
        sla_service.evaluate_action_sla(db, action, now=now)
    except Exception as e:
        logger.error(f"SLA evaluation on status update failed for Action #{action.id}: {e}", exc_info=True)

    return action

def reassign_action(
    db: Session,
    action_id: int,
    new_user_id: int,
    new_department: Optional[str],
    user: User,
    comment_text: Optional[str] = None
) -> Action:
    """Reassign operational action to another active user and department."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    new_user = db.query(User).filter(User.id == new_user_id).first()
    if not new_user:
        raise ValueError(f"User #{new_user_id} does not exist.")
    if not new_user.is_active:
        raise ValueError(f"User '{new_user.name}' is inactive and cannot receive actions.")

    old_user_id = action.assigned_user_id
    old_department = action.assigned_department

    action.assigned_user_id = new_user.id
    if new_department:
        action.assigned_department = new_department.strip()

    action.updated_at = utc_now()

    if comment_text and comment_text.strip():
        comment = ActionComment(
            action_id=action.id,
            user_id=user.id,
            comment=comment_text.strip(),
            created_at=utc_now()
        )
        db.add(comment)

    log_audit_event(
        db,
        user_id=user.id,
        action_name="ACTION_REASSIGNED",
        entity_id=str(action.id),
        metadata={
            "action_number": action.action_number,
            "old_user_id": old_user_id,
            "new_user_id": new_user.id,
            "old_department": old_department,
            "new_department": action.assigned_department
        }
    )

    db.commit()
    db.refresh(action)
    return action

def update_action_priority(
    db: Session,
    action_id: int,
    new_priority: ActionPriority,
    user: User
) -> Action:
    """Modify operational action priority while preserving historical AI/HSE priorities."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    old_priority = action.priority
    action.priority = new_priority
    action.updated_at = utc_now()

    log_audit_event(
        db,
        user_id=user.id,
        action_name="ACTION_PRIORITY_CHANGED",
        entity_id=str(action.id),
        metadata={
            "action_number": action.action_number,
            "old_priority": old_priority.value,
            "new_priority": new_priority.value
        }
    )

    db.commit()
    db.refresh(action)
    return action

def update_action_due_date(
    db: Session,
    action_id: int,
    new_due_date: str,
    user: User
) -> Action:
    """Modify operational action due date."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    old_due_date = action.due_date
    action.due_date = new_due_date.strip()
    action.updated_at = utc_now()

    log_audit_event(
        db,
        user_id=user.id,
        action_name="ACTION_DUE_DATE_CHANGED",
        entity_id=str(action.id),
        metadata={
            "action_number": action.action_number,
            "old_due_date": old_due_date,
            "new_due_date": action.due_date
        }
    )

    db.commit()
    db.refresh(action)

    # Part 4D: Update ActionSLA due_at if SLA record exists
    if action.sla:
        try:
            from backend.services import sla_service
            action.sla.due_at = sla_service.parse_due_date_to_utc(action.due_date)
            sla_service.evaluate_action_sla(db, action)
        except Exception as e:
            logger.error(f"Failed to update ActionSLA due_at for Action #{action.id}: {e}", exc_info=True)

    return action

def add_action_comment(
    db: Session,
    action_id: int,
    comment_text: str,
    user: User
) -> ActionComment:
    """Add a new comment thread item to an action."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    if not comment_text or not comment_text.strip():
        raise ValueError("Comment text cannot be empty.")

    comment = ActionComment(
        action_id=action.id,
        user_id=user.id,
        comment=comment_text.strip(),
        created_at=utc_now()
    )
    db.add(comment)

    log_audit_event(
        db,
        user_id=user.id,
        action_name="ACTION_COMMENT_ADDED",
        entity_id=str(action.id),
        metadata={"action_number": action.action_number, "comment_id": comment.id}
    )

    db.commit()
    db.refresh(comment)
    return comment

def get_action_by_id(db: Session, action_id: int) -> Optional[Action]:
    """Retrieve full detail profile of an Action by ID."""
    return db.query(Action).filter(Action.id == action_id).first()

def get_user_actions(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Action]:
    """Fetch actions assigned specifically to the authenticated user (My Actions)."""
    query = db.query(Action).filter(Action.assigned_user_id == user_id)

    if status:
        query = query.filter(Action.status == status)
    if priority:
        query = query.filter(Action.priority == priority)

    return query.order_by(desc(Action.id)).offset(skip).limit(limit).all()

def get_all_actions(
    db: Session,
    user: User,
    site: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_user_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Action]:
    """
    Fetch filterable actions list based on user scope & authorization (Assigned/Manager Actions).
    """
    query = db.query(Action)

    # Site-level RBAC scoping: Non-admin HSE_USER or HSE_MANAGER only sees their authorized site if restricted
    if user.role != UserRole.ADMIN and user.site:
        query = query.filter(Action.site == user.site)

    if site:
        query = query.filter(Action.site == site)
    if department:
        query = query.filter(Action.assigned_department == department)
    if status:
        query = query.filter(Action.status == status)
    if priority:
        query = query.filter(Action.priority == priority)
    if assigned_user_id:
        query = query.filter(Action.assigned_user_id == assigned_user_id)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Action.action_number.ilike(pattern),
                Action.title.ilike(pattern),
                Action.description.ilike(pattern)
            )
        )

    return query.order_by(desc(Action.id)).offset(skip).limit(limit).all()


# =========================================================================
# PART 4E — COMPLETION, HSE VERIFICATION & REOPEN WORKFLOW SERVICES
# =========================================================================

def complete_action_with_verification_pending(
    db: Session,
    action_id: int,
    user: User,
    completion_comment: str,
    evidence_file_name: Optional[str] = None,
    evidence_file_path: Optional[str] = None,
    evidence_description: Optional[str] = None
) -> Action:
    """
    Complete an operational action (Assignee workflow).
    - Enforces mandatory completion comment.
    - Records server-side completion_date timestamp.
    - Optional evidence attachment.
    - Transitions action to COMPLETED then VERIFICATION_PENDING.
    - Preserves SLA completion timing.
    - Records ActionCompletionHistory cycle audit log.
    """
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    if not completion_comment or not completion_comment.strip():
        raise ValueError("Completion comment is mandatory and cannot be empty.")

    now = utc_now()
    action.completion_date = now

    # Determine current completion cycle number
    existing_cycles = db.query(ActionCompletionHistory).filter(
        ActionCompletionHistory.action_id == action_id
    ).count()
    current_cycle = existing_cycles + 1

    # Attach optional evidence if provided
    if evidence_file_name and evidence_file_path:
        ev = ActionEvidence(
            action_id=action.id,
            uploaded_by=user.id,
            file_name=evidence_file_name.strip(),
            file_type="application/octet-stream",
            file_path=evidence_file_path.strip(),
            description=evidence_description.strip() if evidence_description else None,
            uploaded_at=now
        )
        db.add(ev)

    # Record ActionCompletionHistory audit entry
    history_rec = ActionCompletionHistory(
        action_id=action.id,
        cycle_number=current_cycle,
        completed_at=now,
        completed_by=user.id,
        completion_comment=completion_comment.strip(),
        verification_status="PENDING",
        created_at=now
    )
    db.add(history_rec)

    # Transition to COMPLETED and then VERIFICATION_PENDING
    action.status = ActionStatus.VERIFICATION_PENDING
    action.updated_at = now

    # Add threaded comment
    comment = ActionComment(
        action_id=action.id,
        user_id=user.id,
        comment=f"Action marked COMPLETED (Cycle #{current_cycle}). Operational note: {completion_comment.strip()}",
        created_at=now
    )
    db.add(comment)

    log_audit_event(
        db,
        user_id=user.id,
        action_name="ACTION_COMPLETED_PENDING_VERIFICATION",
        entity_id=str(action.id),
        metadata={
            "action_number": action.action_number,
            "cycle_number": current_cycle,
            "completion_comment": completion_comment,
            "evidence_attached": bool(evidence_file_name)
        }
    )

    db.commit()
    db.refresh(action)

    # Part 4D: Re-evaluate SLA to capture completed_on_time vs completed_late
    try:
        from backend.services import sla_service
        sla_service.evaluate_action_sla(db, action, now=now)
    except Exception as e:
        logger.error(f"Failed to re-evaluate SLA upon completion for Action #{action.id}: {e}", exc_info=True)

    logger.info(f"Action #{action.id} ({action.action_number}) completed by User #{user.id} (Cycle #{current_cycle}). Pending HSE Verification.")
    return action


def verify_action_by_hse(
    db: Session,
    action_id: int,
    hse_user: User,
    decision: str,  # VERIFY or REOPEN
    comment_text: str
) -> Action:
    """
    Human-in-the-loop HSE Verification / Reopen workflow.
    - Authorized HSE user verifies or reopens completed action.
    - VERIFY: Sets verified_at, updates status to VERIFIED, triggers impact_service calculation.
    - REOPEN: Validates mandatory reopen_reason, sets reopened_at, transitions to REOPENED/IN_PROGRESS.
    - Preserves historical completion and verification records across multiple cycles.
    """
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    decision_clean = decision.strip().upper()
    if decision_clean not in ("VERIFY", "REOPEN"):
        raise ValueError("Decision must be either 'VERIFY' or 'REOPEN'.")

    if not comment_text or not comment_text.strip():
        raise ValueError("Verification/Reopen comment is mandatory.")

    now = utc_now()

    # Retrieve latest completion history cycle record
    history_rec = (
        db.query(ActionCompletionHistory)
        .filter(ActionCompletionHistory.action_id == action_id)
        .order_by(desc(ActionCompletionHistory.id))
        .first()
    )

    if decision_clean == "VERIFY":
        action.verified_at = now
        action.status = ActionStatus.VERIFIED
        action.updated_at = now

        if history_rec:
            history_rec.verification_status = "VERIFIED"
            history_rec.verified_at = now
            history_rec.verified_by = hse_user.id
            history_rec.verification_comment = comment_text.strip()

        log_audit_event(
            db,
            user_id=hse_user.id,
            action_name="ACTION_HSE_VERIFIED",
            entity_id=str(action.id),
            metadata={
                "action_number": action.action_number,
                "verifier_id": hse_user.id,
                "verification_comment": comment_text
            }
        )

        comment = ActionComment(
            action_id=action.id,
            user_id=hse_user.id,
            comment=f"HSE VERIFIED: {comment_text.strip()}",
            created_at=now
        )
        db.add(comment)

        db.commit()
        db.refresh(action)

        # Trigger Part 4E Impact Analysis Calculation
        try:
            from backend.services import impact_service
            impact_service.calculate_and_store_impact(db, action)
        except Exception as e:
            logger.error(f"Failed to calculate Part 4E Impact Analysis for Action #{action.id}: {e}", exc_info=True)

        logger.info(f"Action #{action.id} ({action.action_number}) successfully HSE VERIFIED by User #{hse_user.id}")
        return action

    else:  # REOPEN
        action.reopened_at = now
        action.status = ActionStatus.REOPENED
        action.updated_at = now

        if history_rec:
            history_rec.verification_status = "REOPENED"
            history_rec.reopened_at = now
            history_rec.reopened_by = hse_user.id
            history_rec.reopen_reason = comment_text.strip()

        log_audit_event(
            db,
            user_id=hse_user.id,
            action_name="ACTION_REOPENED_BY_HSE",
            entity_id=str(action.id),
            metadata={
                "action_number": action.action_number,
                "reopener_id": hse_user.id,
                "reopen_reason": comment_text
            }
        )

        comment = ActionComment(
            action_id=action.id,
            user_id=hse_user.id,
            comment=f"HSE REOPENED ACTION: {comment_text.strip()}",
            created_at=now
        )
        db.add(comment)

        db.commit()
        db.refresh(action)

        logger.info(f"Action #{action.id} ({action.action_number}) REOPENED by HSE User #{hse_user.id}")
        return action


def get_action_completion_history(db: Session, action_id: int) -> List[ActionCompletionHistory]:
    """Fetch complete multi-cycle completion and verification history for an action."""
    return (
        db.query(ActionCompletionHistory)
        .filter(ActionCompletionHistory.action_id == action_id)
        .order_by(ActionCompletionHistory.cycle_number.asc())
        .all()
    )


def add_action_evidence(
    db: Session,
    action_id: int,
    user: User,
    file_name: str,
    file_type: str,
    file_path: str,
    description: Optional[str] = None
) -> ActionEvidence:
    """Store evidence attachment for an action."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ValueError(f"Action #{action_id} not found.")

    ev = ActionEvidence(
        action_id=action.id,
        uploaded_by=user.id,
        file_name=file_name.strip(),
        file_type=file_type.strip(),
        file_path=file_path.strip(),
        description=description.strip() if description else None,
        uploaded_at=utc_now()
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev

