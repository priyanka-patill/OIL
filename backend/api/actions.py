"""
Part 4C — Action Management & Assignment API Router

Exposes REST endpoints to create operational actions from HSE-approved/modified interventions,
assign actions to users and departments, track action status lifecycles, reassign actions,
modify priorities and due dates, post comments, and query My Actions and Assigned Actions.
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.database import get_db
from backend.database.models import User, UserRole, ActionStatus, ActionPriority, AuditLog
from backend.security.dependencies import get_current_user
from backend.services import action_service

router = APIRouter(prefix="/actions", tags=["Action Management & Assignment"])


class ActionCreateRequest(BaseModel):
    intervention_id: int
    assigned_user_id: int
    assigned_department: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None  # HIGH, MEDIUM, LOW
    due_date: Optional[str] = None  # YYYY-MM-DD
    initial_comment: Optional[str] = None


class ActionStatusUpdateRequest(BaseModel):
    status: str
    comment: Optional[str] = None


class ActionReassignRequest(BaseModel):
    assigned_user_id: int
    assigned_department: Optional[str] = None
    comment: Optional[str] = None


class ActionPriorityUpdateRequest(BaseModel):
    priority: str


class ActionDueDateUpdateRequest(BaseModel):
    due_date: str


class ActionCommentCreateRequest(BaseModel):
    comment: str


class ActionCompleteRequest(BaseModel):
    completion_comment: str
    evidence_file_name: Optional[str] = None
    evidence_file_path: Optional[str] = None
    evidence_description: Optional[str] = None


class ActionVerifyRequest(BaseModel):
    decision: str  # VERIFY or REOPEN
    comment: str


class ActionReopenRequest(BaseModel):
    reopen_reason: str


class ActionEvidenceCreateRequest(BaseModel):
    file_name: str
    file_type: str
    file_path: str
    description: Optional[str] = None


def format_action_comment_dict(comment) -> dict:
    """Helper serializer for ActionComment model."""
    return {
        "id": comment.id,
        "action_id": comment.action_id,
        "user_id": comment.user_id,
        "user_name": comment.user.name if getattr(comment, "user", None) else f"User #{comment.user_id}",
        "comment": comment.comment,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


def format_completion_history_dict(h) -> dict:
    """Helper serializer for ActionCompletionHistory model."""
    return {
        "id": h.id,
        "action_id": h.action_id,
        "cycle_number": h.cycle_number,
        "completed_at": h.completed_at.isoformat() if h.completed_at else None,
        "completed_by": h.completed_by,
        "completed_by_name": h.completer.name if getattr(h, "completer", None) else f"User #{h.completed_by}",
        "completion_comment": h.completion_comment,
        "verification_status": h.verification_status,
        "verified_at": h.verified_at.isoformat() if h.verified_at else None,
        "verified_by": h.verified_by,
        "verified_by_name": h.verifier.name if getattr(h, "verifier", None) else (f"User #{h.verified_by}" if h.verified_by else None),
        "verification_comment": h.verification_comment,
        "reopened_at": h.reopened_at.isoformat() if h.reopened_at else None,
        "reopened_by": h.reopened_by,
        "reopened_by_name": h.reopener.name if getattr(h, "reopener", None) else (f"User #{h.reopened_by}" if h.reopened_by else None),
        "reopen_reason": h.reopen_reason,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


def format_evidence_dict(ev) -> dict:
    """Helper serializer for ActionEvidence model."""
    return {
        "id": ev.id,
        "action_id": ev.action_id,
        "uploaded_by": ev.uploaded_by,
        "uploader_name": ev.uploader.name if getattr(ev, "uploader", None) else f"User #{ev.uploaded_by}",
        "file_name": ev.file_name,
        "file_type": ev.file_type,
        "file_path": ev.file_path,
        "description": ev.description,
        "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
    }


def format_impact_analysis_dict(impact) -> dict:
    """Helper serializer for ActionImpactAnalysis model."""
    if not impact:
        return None
    metrics = json.loads(impact.metrics_json) if impact.metrics_json else {}
    return {
        "id": impact.id,
        "action_id": impact.action_id,
        "intervention_id": impact.intervention_id,
        "report_id": impact.report_id,
        "pattern_id": impact.pattern_id,
        "barrier_id": impact.barrier_id,
        "intervention_date": impact.intervention_date.isoformat() if impact.intervention_date else None,
        "before_period": {
            "start": impact.before_start,
            "end": impact.before_end
        },
        "after_period": {
            "start": impact.after_start,
            "end": impact.after_end
        },
        "metrics": metrics,
        "overall_observed_change": impact.overall_observed_change,
        "data_sufficiency_status": impact.data_sufficiency_status,
        "data_sufficiency_reason": impact.data_sufficiency_reason,
        "methodology_version": impact.methodology_version,
        "calculated_at": impact.calculated_at.isoformat() if impact.calculated_at else None,
    }


def format_action_dict(action, include_history: bool = True, db: Optional[Session] = None) -> dict:
    """Helper serializer for Action model with traceability and history."""
    ev_snapshot = json.loads(action.evidence_snapshot_json) if action.evidence_snapshot_json else {}

    history_events = []
    if include_history and db is not None:
        audits = (
            db.query(AuditLog)
            .filter(AuditLog.entity_type == "ACTION", AuditLog.entity_id == str(action.id))
            .order_by(AuditLog.timestamp.asc())
            .all()
        )
        for a in audits:
            meta = json.loads(a.metadata_json) if a.metadata_json else {}
            history_events.append({
                "id": a.id,
                "action_type": a.action,
                "user_id": a.user_id,
                "user_name": a.user.name if getattr(a, "user", None) else (f"User #{a.user_id}" if a.user_id else "System"),
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "metadata": meta
            })

    sla_info = None
    if getattr(action, "sla", None) and action.sla:
        sla_rec = action.sla
        from backend.services.sla_service import calculate_sla_status_and_times
        sla_res = calculate_sla_status_and_times(sla_rec, action.status)
        sla_info = {
            "id": sla_rec.id,
            "sla_status": sla_res["sla_status"].value if hasattr(sla_res["sla_status"], "value") else str(sla_res["sla_status"]),
            "sla_start_at": sla_rec.sla_start_at.isoformat() if sla_rec.sla_start_at else None,
            "due_at": sla_rec.due_at.isoformat() if sla_rec.due_at else None,
            "sla_duration_minutes": sla_rec.sla_duration_minutes,
            "due_soon_threshold_minutes": sla_rec.due_soon_threshold_minutes,
            "remaining_minutes": sla_res["remaining_minutes"],
            "overdue_minutes": sla_res["overdue_minutes"],
            "is_overdue": sla_res["is_overdue"],
            "completed_at": sla_rec.completed_at.isoformat() if sla_rec.completed_at else None,
            "completion_timing": sla_res["completion_timing"].value if hasattr(sla_res["completion_timing"], "value") else str(sla_res["completion_timing"]),
            "current_escalation_level": sla_rec.current_escalation_level,
            "reminder_count": sla_rec.reminder_count,
            "escalation_count": sla_rec.escalation_count
        }

    # Part 4E Payload Serialization
    comp_history = [format_completion_history_dict(h) for h in action.completion_history] if getattr(action, "completion_history", None) else []
    evidences_list = [format_evidence_dict(ev) for ev in action.evidences] if getattr(action, "evidences", None) else []

    latest_impact = None
    if getattr(action, "impact_analyses", None) and action.impact_analyses:
        latest_impact = format_impact_analysis_dict(action.impact_analyses[0])

    return {
        "id": action.id,
        "action_number": action.action_number,
        "intervention_id": action.intervention_id,
        "report_id": action.report_id,
        "pattern_id": action.pattern_id,
        "barrier_id": action.barrier_id,
        "source_hse_review_id": action.source_hse_review_id,
        "title": action.title,
        "description": action.description,
        "assigned_user_id": action.assigned_user_id,
        "assigned_user_name": action.assigned_user.name if getattr(action, "assigned_user", None) else f"User #{action.assigned_user_id}",
        "assigned_department": action.assigned_department,
        "site": action.site,
        "priority": action.priority.value if hasattr(action.priority, "value") else str(action.priority),
        "due_date": action.due_date,
        "status": action.status.value if hasattr(action.status, "value") else str(action.status),
        "created_by": action.created_by,
        "creator_name": action.creator.name if getattr(action, "creator", None) else f"User #{action.created_by}",
        "created_at": action.created_at.isoformat() if action.created_at else None,
        "updated_at": action.updated_at.isoformat() if action.updated_at else None,
        "start_date": action.start_date.isoformat() if action.start_date else None,
        "completion_date": action.completion_date.isoformat() if action.completion_date else None,
        "verified_at": action.verified_at.isoformat() if action.verified_at else None,
        "reopened_at": action.reopened_at.isoformat() if action.reopened_at else None,
        "cancelled_at": action.cancelled_at.isoformat() if action.cancelled_at else None,
        "evidence_snapshot": ev_snapshot,
        "sla": sla_info,
        "comments": [format_action_comment_dict(c) for c in action.comments] if getattr(action, "comments", None) else [],
        "completion_history": comp_history,
        "evidences": evidences_list,
        "impact_analysis": latest_impact,
        "history": history_events
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_action(
    req: ActionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Convert an HSE-approved or HSE-modified intervention into an operational Action.
    
    Eligibility Enforcement:
    - Only ACCEPTED or MODIFIED interventions can create actions.
    - PENDING_HSE_VALIDATION and REJECTED interventions are rejected with 400 Bad Request.
    """
    try:
        action = action_service.create_action_from_intervention(
            db=db,
            intervention_id=req.intervention_id,
            created_by_user=current_user,
            assigned_user_id=req.assigned_user_id,
            assigned_department=req.assigned_department,
            title=req.title,
            description=req.description,
            priority=req.priority,
            due_date=req.due_date,
            initial_comment=req.initial_comment
        )
        return {
            "success": True,
            "message": f"Action {action.action_number} created successfully.",
            "data": format_action_dict(action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action creation failed: {str(e)}")


@router.get("")
def list_assigned_actions(
    site: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    assigned_user_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List filterable operational actions (Manager / HSE Actions View).
    Supports backend filtering by site, department, status, priority, assignee, and text search.
    """
    actions = action_service.get_all_actions(
        db=db,
        user=current_user,
        site=site,
        department=department,
        status=status_filter,
        priority=priority_filter,
        assigned_user_id=assigned_user_id,
        search=search,
        skip=skip,
        limit=limit
    )
    return {
        "success": True,
        "count": len(actions),
        "data": [format_action_dict(a, include_history=False) for a in actions]
    }


@router.get("/my")
def list_my_actions(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch actions assigned specifically to the current authenticated user (My Actions)."""
    actions = action_service.get_user_actions(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        priority=priority_filter,
        skip=skip,
        limit=limit
    )
    return {
        "success": True,
        "count": len(actions),
        "data": [format_action_dict(a, include_history=False) for a in actions]
    }


@router.get("/{action_id}")
def get_action_detail(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete detail profile of an Action with full source traceability, comments, and audit history."""
    action = action_service.get_action_by_id(db, action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action #{action_id} not found.")

    # Site-level security check
    if current_user.role != UserRole.ADMIN and current_user.site and action.site != current_user.site:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to actions outside your assigned site.")

    return {
        "success": True,
        "data": format_action_dict(action, include_history=True, db=db)
    }


@router.patch("/{action_id}/status")
def update_action_status_endpoint(
    action_id: int,
    req: ActionStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transition Action lifecycle status with strict state validation and timestamp recording."""
    try:
        new_enum = ActionStatus(req.status.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{req.status}'. Allowed statuses: {[s.value for s in ActionStatus]}"
        )

    try:
        updated_action = action_service.update_action_status(
            db=db,
            action_id=action_id,
            new_status=new_enum,
            user=current_user,
            comment_text=req.comment
        )
        return {
            "success": True,
            "message": f"Action status updated to {new_enum.value}.",
            "data": format_action_dict(updated_action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{action_id}/assign")
def reassign_action_endpoint(
    action_id: int,
    req: ActionReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reassign operational action to another user and department."""
    try:
        updated_action = action_service.reassign_action(
            db=db,
            action_id=action_id,
            new_user_id=req.assigned_user_id,
            new_department=req.assigned_department,
            user=current_user,
            comment_text=req.comment
        )
        return {
            "success": True,
            "message": f"Action reassigned to User #{req.assigned_user_id}.",
            "data": format_action_dict(updated_action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{action_id}/priority")
def update_action_priority_endpoint(
    action_id: int,
    req: ActionPriorityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify operational action priority."""
    try:
        new_prio = ActionPriority(req.priority.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid priority '{req.priority}'. Allowed: HIGH, MEDIUM, LOW.")

    try:
        updated_action = action_service.update_action_priority(
            db=db,
            action_id=action_id,
            new_priority=new_prio,
            user=current_user
        )
        return {
            "success": True,
            "message": f"Action priority updated to {new_prio.value}.",
            "data": format_action_dict(updated_action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{action_id}/due-date")
def update_action_due_date_endpoint(
    action_id: int,
    req: ActionDueDateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify operational action due date."""
    try:
        updated_action = action_service.update_action_due_date(
            db=db,
            action_id=action_id,
            new_due_date=req.due_date,
            user=current_user
        )
        return {
            "success": True,
            "message": f"Action due date updated to {req.due_date}.",
            "data": format_action_dict(updated_action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{action_id}/comments")
def add_action_comment_endpoint(
    action_id: int,
    req: ActionCommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a progress or context comment to an action."""
    try:
        comment = action_service.add_action_comment(
            db=db,
            action_id=action_id,
            comment_text=req.comment,
            user=current_user
        )
        return {
            "success": True,
            "message": "Comment added successfully.",
            "data": format_action_comment_dict(comment)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================================================
# PART 4D — SLA MONITORING & ESCALATION ENDPOINTS
# ==================================================

@router.get("/sla/summary")
def get_sla_summary_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Backend aggregation of authoritative SLA summary metrics for Dashboard & Manager View.
    Returns: active, due_soon, overdue, completed_on_time, completed_late.
    """
    from backend.services import sla_service
    summary = sla_service.get_sla_summary(db, current_user)
    return {
        "success": True,
        "data": summary
    }


@router.post("/sla/evaluate")
def evaluate_slas_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manual / Scheduler execution endpoint to re-evaluate SLA state across all active actions.
    Triggers due-soon reminders and multi-level escalations idempotently.
    """
    if current_user.role not in (UserRole.HSE_MANAGER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HSE Managers or Admins can trigger SLA evaluation.")

    from backend.services import sla_service
    result = sla_service.evaluate_all_active_slas(db)
    return {
        "success": True,
        "message": f"SLA evaluation complete. {result['evaluated_count']} actions evaluated.",
        "data": result
    }


@router.get("/{action_id}/sla")
def get_action_sla_detail(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full SLA detail profile for an Action."""
    action = action_service.get_action_by_id(db, action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action #{action_id} not found.")

    if current_user.role != UserRole.ADMIN and current_user.site and action.site != current_user.site:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    from backend.services import sla_service
    # Ensure fresh SLA evaluation
    if action.sla:
        sla_service.evaluate_action_sla(db, action)

    formatted = format_action_dict(action, include_history=False, db=db)
    return {
        "success": True,
        "data": formatted.get("sla")
    }


@router.get("/{action_id}/sla/history")
def get_action_sla_history(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch complete SLA reminder and escalation event history for an Action."""
    action = action_service.get_action_by_id(db, action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action #{action_id} not found.")

    if current_user.role != UserRole.ADMIN and current_user.site and action.site != current_user.site:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    sla = action.sla
    if not sla:
        return {"success": True, "data": {"reminders": [], "escalations": []}}

    reminders = [
        {
            "id": r.id,
            "reminder_type": r.reminder_type,
            "scheduled_for": r.scheduled_for.isoformat() if r.scheduled_for else None,
            "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
            "recipient_user_id": r.recipient_user_id,
            "status": r.status,
            "message": r.message
        }
        for r in sla.reminders
    ]

    escalations = [
        {
            "id": e.id,
            "escalation_level": e.escalation_level,
            "escalation_name": e.escalation_name,
            "overdue_minutes_at_trigger": e.overdue_minutes_at_trigger,
            "triggered_at": e.triggered_at.isoformat() if e.triggered_at else None,
            "recipient_role_or_dept": e.recipient_role_or_dept,
            "status": e.status,
            "reason": e.reason
        }
        for r_esc in sla.escalations
        for e in [r_esc]
    ]

    return {
        "success": True,
        "data": {
            "sla_status": sla.sla_status.value if hasattr(sla.sla_status, "value") else str(sla.sla_status),
            "current_escalation_level": sla.current_escalation_level,
            "reminders": reminders,
            "escalations": escalations
        }
    }


# =========================================================================
# PART 4E — COMPLETION, VERIFICATION & IMPACT TRACKING ENDPOINTS
# =========================================================================

@router.post("/{action_id}/complete")
def complete_action_endpoint(
    action_id: int,
    req: ActionCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete operational action (Assignee workflow).
    - Enforces mandatory completion comment.
    - Records server UTC completion_date.
    - Optional completion evidence attachments.
    - Transitions action to COMPLETED then VERIFICATION_PENDING.
    """
    try:
        action = action_service.complete_action_with_verification_pending(
            db=db,
            action_id=action_id,
            user=current_user,
            completion_comment=req.completion_comment,
            evidence_file_name=req.evidence_file_name,
            evidence_file_path=req.evidence_file_path,
            evidence_description=req.evidence_description
        )
        return {
            "success": True,
            "message": f"Action {action.action_number} marked completed and submitted for HSE verification.",
            "data": format_action_dict(action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action completion failed: {str(e)}")


@router.post("/{action_id}/verify")
def verify_action_endpoint(
    action_id: int,
    req: ActionVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    HSE Verification / Reopen endpoint.
    - Authorized HSE user verifies or reopens completed action.
    - VERIFY: transitions to VERIFIED, sets verified_at, triggers Part 4E Impact Analysis.
    - REOPEN: requires reopen reason, transitions to REOPENED, preserves completion history.
    """
    if current_user.role not in (UserRole.HSE_USER, UserRole.HSE_MANAGER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized HSE reviewers can verify or reopen actions.")

    try:
        action = action_service.verify_action_by_hse(
            db=db,
            action_id=action_id,
            hse_user=current_user,
            decision=req.decision,
            comment_text=req.comment
        )
        return {
            "success": True,
            "message": f"Action {action.action_number} status updated to {action.status.value}.",
            "data": format_action_dict(action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action verification failed: {str(e)}")


@router.post("/{action_id}/reopen")
def reopen_action_endpoint(
    action_id: int,
    req: ActionReopenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Explicit Reopen action endpoint requiring reopen reason."""
    if current_user.role not in (UserRole.HSE_USER, UserRole.HSE_MANAGER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized HSE reviewers can reopen actions.")

    try:
        action = action_service.verify_action_by_hse(
            db=db,
            action_id=action_id,
            hse_user=current_user,
            decision="REOPEN",
            comment_text=req.reopen_reason
        )
        return {
            "success": True,
            "message": f"Action {action.action_number} reopened for further work.",
            "data": format_action_dict(action, include_history=True, db=db)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Reopen failed: {str(e)}")


@router.post("/{action_id}/evidence")
def add_evidence_endpoint(
    action_id: int,
    req: ActionEvidenceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Store evidence attachment for an action."""
    try:
        ev = action_service.add_action_evidence(
            db=db,
            action_id=action_id,
            user=current_user,
            file_name=req.file_name,
            file_type=req.file_type,
            file_path=req.file_path,
            description=req.description
        )
        return {
            "success": True,
            "message": f"Evidence '{ev.file_name}' attached to Action #{action_id}.",
            "data": format_evidence_dict(ev)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{action_id}/completion-history")
def get_completion_history_endpoint(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get multi-cycle completion and verification history audit log."""
    history = action_service.get_action_completion_history(db, action_id)
    return {
        "success": True,
        "data": [format_completion_history_dict(h) for h in history]
    }


@router.get("/{action_id}/impact")
def get_impact_analysis_endpoint(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get latest observational Before/After Impact Analysis profile for an action."""
    from backend.database.models import Action
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action #{action_id} not found.")

    from backend.services import impact_service
    impact = impact_service.get_latest_impact_analysis(db, action_id)

    if not impact and action.status in (ActionStatus.VERIFIED, ActionStatus.COMPLETED, ActionStatus.VERIFICATION_PENDING):
        try:
            impact = impact_service.calculate_and_store_impact(db, action)
        except Exception as e:
            logger.error(f"Failed on-the-fly impact calculation for Action #{action_id}: {e}", exc_info=True)

    return {
        "success": True,
        "data": format_impact_analysis_dict(impact)
    }


@router.post("/{action_id}/impact/recalculate")
def recalculate_impact_endpoint(
    action_id: int,
    before_days: int = Query(90, ge=7, le=365),
    after_days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force recalculation of observational Impact Analysis snapshot."""
    from backend.database.models import Action
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action #{action_id} not found.")

    try:
        from backend.services import impact_service
        impact = impact_service.calculate_and_store_impact(db, action, before_days=before_days, after_days=after_days)
        return {
            "success": True,
            "message": "Impact Analysis recalculated successfully.",
            "data": format_impact_analysis_dict(impact)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Recalculation failed: {str(e)}")


