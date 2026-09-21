"""
Part 4F — HSE Action Center & Full System Integration API Router

Provides authoritative, RBAC-scoped REST endpoints for the HSE Action Center dashboard:
1. GET /api/action-center/summary - Authoritative KPI summary metrics
2. GET /api/action-center/sections - Paginated operational sections data
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from backend.database.database import get_db
from backend.database.models import (
    User, UserRole, SafetyReport, AIAnalysis,
    InterventionRecommendation, InterventionStatus,
    HSEInterventionReview, Action, ActionStatus, ActionPriority,
    ActionSLA, SLAStatus, SLACompletionTiming,
    ActionImpactAnalysis, ActionCompletionHistory, ActionEvidence, AuditLog,
    utc_now
)
from backend.security.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/action-center", tags=["HSE Action Center & Full System Integration"])


def apply_site_rbac_scoping(query, model, current_user: User):
    """
    Strict site-level RBAC helper:
    If user is not ADMIN and has an assigned site, filter query strictly by model.site.
    Prevents cross-site aggregate data leakage.
    """
    if current_user.role != UserRole.ADMIN and current_user.site:
        if hasattr(model, "site"):
            return query.filter(model.site == current_user.site)
    return query


@router.get("/summary")
def get_action_center_summary(
    site: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Authoritative backend aggregation of HSE Action Center operational KPI summary counts.
    Strictly applies user RBAC and site scoping before counting to prevent aggregate data leakage.
    """
    # Active site filter (user site restriction takes priority if non-admin)
    target_site = current_user.site if (current_user.role != UserRole.ADMIN and current_user.site) else site

    # 1. Pending HSE Reviews Count
    rev_q = db.query(func.count(func.distinct(InterventionRecommendation.id))).filter(
        InterventionRecommendation.status == InterventionStatus.PENDING_HSE_VALIDATION
    )
    if target_site:
        rev_q = rev_q.join(SafetyReport, InterventionRecommendation.report_id == SafetyReport.id).filter(SafetyReport.site == target_site)
    if priority:
        rev_q = rev_q.filter(InterventionRecommendation.priority_suggestion == priority.upper())
    pending_reviews_cnt = rev_q.scalar() or 0

    # 2. Operational Actions Base Query
    act_q = db.query(Action)
    if target_site:
        act_q = act_q.filter(Action.site == target_site)
    if department:
        act_q = act_q.filter(Action.assigned_department == department)
    if priority:
        act_q = act_q.filter(Action.priority == priority.upper())
    if start_date:
        act_q = act_q.filter(func.date(Action.created_at) >= start_date)
    if end_date:
        act_q = act_q.filter(func.date(Action.created_at) <= end_date)

    # Status counts (Distinct Action IDs)
    active_actions_cnt = act_q.filter(
        Action.status.in_([ActionStatus.IN_PROGRESS, ActionStatus.ASSIGNED, ActionStatus.ON_HOLD, ActionStatus.REOPENED])
    ).with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    completed_cnt = act_q.filter(Action.status == ActionStatus.COMPLETED).with_entities(func.count(func.distinct(Action.id))).scalar() or 0
    verification_pending_cnt = act_q.filter(Action.status == ActionStatus.VERIFICATION_PENDING).with_entities(func.count(func.distinct(Action.id))).scalar() or 0
    verified_cnt = act_q.filter(Action.status == ActionStatus.VERIFIED).with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    # 3. SLA Metrics Counts (Distinct Action IDs)
    sla_q = db.query(ActionSLA).join(Action, ActionSLA.action_id == Action.id)
    if target_site:
        sla_q = sla_q.filter(Action.site == target_site)
    if department:
        sla_q = sla_q.filter(Action.assigned_department == department)
    if priority:
        sla_q = sla_q.filter(Action.priority == priority.upper())

    due_soon_cnt = sla_q.filter(
        ActionSLA.sla_status == SLAStatus.DUE_SOON,
        Action.status.in_([ActionStatus.IN_PROGRESS, ActionStatus.ASSIGNED, ActionStatus.ON_HOLD, ActionStatus.REOPENED])
    ).with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    overdue_cnt = sla_q.filter(
        ActionSLA.sla_status == SLAStatus.OVERDUE,
        Action.status.in_([ActionStatus.IN_PROGRESS, ActionStatus.ASSIGNED, ActionStatus.ON_HOLD, ActionStatus.REOPENED])
    ).with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    escalated_actions_cnt = sla_q.filter(
        ActionSLA.current_escalation_level > 0,
        Action.status.in_([ActionStatus.IN_PROGRESS, ActionStatus.ASSIGNED, ActionStatus.ON_HOLD, ActionStatus.REOPENED])
    ).with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    completed_on_time_cnt = sla_q.filter(ActionSLA.completion_timing == SLACompletionTiming.COMPLETED_ON_TIME).with_entities(func.count(func.distinct(Action.id))).scalar() or 0
    completed_late_cnt = sla_q.filter(ActionSLA.completion_timing == SLACompletionTiming.COMPLETED_LATE).with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    # 4. Impact Analysis Counts (Distinct Action IDs)
    imp_q = db.query(ActionImpactAnalysis).join(Action, ActionImpactAnalysis.action_id == Action.id)
    if target_site:
        imp_q = imp_q.filter(Action.site == target_site)
    if department:
        imp_q = imp_q.filter(Action.assigned_department == department)

    impact_available_cnt = imp_q.filter(ActionImpactAnalysis.data_sufficiency_status == "SUFFICIENT").with_entities(func.count(func.distinct(Action.id))).scalar() or 0
    insufficient_data_cnt = imp_q.filter(ActionImpactAnalysis.data_sufficiency_status == "INSUFFICIENT_DATA").with_entities(func.count(func.distinct(Action.id))).scalar() or 0

    return {
        "success": True,
        "data": {
            "summary": {
                "pending_reviews": pending_reviews_cnt,
                "active_actions": active_actions_cnt,
                "due_soon": due_soon_cnt,
                "overdue": overdue_cnt,
                "completed": completed_cnt,
                "verification_pending": verification_pending_cnt,
                "verified": verified_cnt,
                "impact_available": impact_available_cnt,
                "insufficient_data": insufficient_data_cnt,
                "escalated_actions": escalated_actions_cnt,
                "completed_on_time": completed_on_time_cnt,
                "completed_late": completed_late_cnt
            },
            "metadata": {
                "generated_at": utc_now().isoformat(),
                "site_scope": target_site or "ALL_SITES",
                "filters": {
                    "site": target_site,
                    "department": department,
                    "priority": priority,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }
    }


@router.get("/sections")
def get_action_center_sections(
    site: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    sla_status_filter: Optional[str] = Query(None, alias="sla_status"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch consolidated operational section records for the HSE Action Center:
    - Pending Reviews
    - My Actions
    - Overdue Actions & Escalation Outbox
    - Verification Pending
    - Impact Analyses List
    - Recent Activity Stream
    """
    target_site = current_user.site if (current_user.role != UserRole.ADMIN and current_user.site) else site

    # Section 1: Pending HSE Reviews
    rev_q = db.query(InterventionRecommendation).filter(
        InterventionRecommendation.status == InterventionStatus.PENDING_HSE_VALIDATION
    )
    if target_site:
        rev_q = rev_q.join(SafetyReport, InterventionRecommendation.report_id == SafetyReport.id).filter(SafetyReport.site == target_site)
    if priority:
        rev_q = rev_q.filter(InterventionRecommendation.priority_suggestion == priority.upper())

    pending_interventions = rev_q.order_by(InterventionRecommendation.id.desc()).limit(limit).all()

    pending_reviews_list = []
    for intv in pending_interventions:
        rep = intv.report
        pending_reviews_list.append({
            "id": intv.id,
            "recommendation_number": intv.recommendation_number,
            "title": intv.title,
            "category": intv.category.value if hasattr(intv.category, "value") else str(intv.category),
            "barrier_category": intv.barrier_category or "General",
            "priority_suggestion": intv.priority_suggestion.value if hasattr(intv.priority_suggestion, "value") else str(intv.priority_suggestion),
            "report_id": intv.report_id,
            "report_number": rep.report_number if rep else None,
            "site": rep.site if rep else target_site,
            "created_at": intv.created_at.isoformat() if intv.created_at else None
        })

    # Section 2: My Actions (Assigned to current user)
    my_act_q = db.query(Action).filter(Action.assigned_user_id == current_user.id)
    if status_filter:
        my_act_q = my_act_q.filter(Action.status == status_filter.upper())

    my_actions = my_act_q.order_by(Action.id.desc()).limit(limit).all()
    from backend.api.actions import format_action_dict
    my_actions_list = [format_action_dict(a, include_history=False, db=db) for a in my_actions]

    # Section 3: Overdue Actions & Escalations
    overdue_q = db.query(Action).join(ActionSLA, Action.id == ActionSLA.action_id).filter(
        ActionSLA.sla_status == SLAStatus.OVERDUE,
        Action.status.in_([ActionStatus.IN_PROGRESS, ActionStatus.ASSIGNED, ActionStatus.ON_HOLD, ActionStatus.REOPENED])
    )
    if target_site:
        overdue_q = overdue_q.filter(Action.site == target_site)
    if department:
        overdue_q = overdue_q.filter(Action.assigned_department == department)

    overdue_actions = overdue_q.order_by(ActionSLA.due_at.asc()).limit(limit).all()
    overdue_actions_list = []
    now_utc = utc_now()
    for a in overdue_actions:
        sla = a.sla
        days_overdue = 0
        if sla and sla.due_at:
            due_at_utc = sla.due_at if sla.due_at.tzinfo else sla.due_at.replace(tzinfo=timezone.utc)
            delta = now_utc - due_at_utc
            days_overdue = max(1, delta.days)

        latest_esc = sla.escalations[-1] if (sla and sla.escalations) else None

        overdue_actions_list.append({
            "id": a.id,
            "action_number": a.action_number,
            "title": a.title,
            "assigned_user_name": a.assigned_user.name if getattr(a, "assigned_user", None) else f"User #{a.assigned_user_id}",
            "assigned_department": a.assigned_department,
            "site": a.site,
            "priority": a.priority.value if hasattr(a.priority, "value") else str(a.priority),
            "due_date": a.due_date,
            "days_overdue": days_overdue,
            "current_escalation_level": sla.current_escalation_level if sla else 0,
            "latest_escalation": {
                "level": latest_esc.escalation_level,
                "name": latest_esc.escalation_name,
                "triggered_at": latest_esc.triggered_at.isoformat() if latest_esc.triggered_at else None,
                "recipient": latest_esc.recipient_role_or_dept,
                "reason": latest_esc.reason
            } if latest_esc else None
        })

    # Section 4: Verification Pending
    vp_q = db.query(Action).filter(Action.status.in_([ActionStatus.VERIFICATION_PENDING, ActionStatus.COMPLETED]))
    if target_site:
        vp_q = vp_q.filter(Action.site == target_site)
    if department:
        vp_q = vp_q.filter(Action.assigned_department == department)

    vp_actions = vp_q.order_by(Action.updated_at.desc()).limit(limit).all()
    verification_pending_list = [format_action_dict(a, include_history=False, db=db) for a in vp_actions]

    # Section 5: Impact Analyses List
    imp_q = db.query(ActionImpactAnalysis).join(Action, ActionImpactAnalysis.action_id == Action.id)
    if target_site:
        imp_q = imp_q.filter(Action.site == target_site)
    if department:
        imp_q = imp_q.filter(Action.assigned_department == department)

    impact_analyses = imp_q.order_by(ActionImpactAnalysis.id.desc()).limit(limit).all()
    from backend.api.actions import format_impact_analysis_dict
    impact_analyses_list = [format_impact_analysis_dict(imp) for imp in impact_analyses]

    # Section 6: Recent Operational Activity Audit Stream
    audit_q = db.query(AuditLog).filter(AuditLog.entity_type.in_(["ACTION", "INTERVENTION_REVIEW"]))
    audits = audit_q.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    recent_activity_list = []
    for a in audits:
        meta = json.loads(a.metadata_json) if a.metadata_json else {}
        recent_activity_list.append({
            "id": a.id,
            "action_type": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "user_name": a.user.name if getattr(a, "user", None) else (f"User #{a.user_id}" if a.user_id else "System"),
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "metadata": meta
        })

    return {
        "success": True,
        "data": {
            "pending_reviews": pending_reviews_list,
            "my_actions": my_actions_list,
            "overdue_actions": overdue_actions_list,
            "verification_pending": verification_pending_list,
            "impact_analyses": impact_analyses_list,
            "recent_activity": recent_activity_list
        }
    }
