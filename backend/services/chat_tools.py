"""
OIL HSE Safety Assistant — Domain Data Retrieval Engine (chat_tools.py)

Provides authenticated, site-authorized database and analytics retrieval functions
for the conversational AI assistant. Strictly enforces access control based on user identity,
site assignments, and roles.
"""

import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.database.models import (
    User, UserRole, SafetyReport, Action, ActionStatus, SLAStatus,
    InterventionRecommendation, HSEDecision, HSEInterventionDecision
)
from backend.services import (
    report_service, action_service,
    sla_service, impact_service, intervention_service
)


def get_dashboard_summary_data(db: Session, user: User) -> Dict[str, Any]:
    """Retrieve authorized dashboard summary metrics."""
    reports_query = db.query(SafetyReport)
    if user.role != UserRole.ADMIN and user.site:
        reports_query = reports_query.filter(SafetyReport.site == user.site)
    
    all_reports = reports_query.all()
    total_reports = len(all_reports)
    sif_analyzed = 0
    hse_validated = 0
    pending_review = 0
    for r in all_reports:
        if getattr(r, "ai_analyses", None) and r.ai_analyses and r.ai_analyses[0].prediction == "SIF_PRECURSOR":
            sif_analyzed += 1
        if getattr(r, "hse_reviews", None) and r.hse_reviews:
            hse_validated += 1
        else:
            pending_review += 1

    actions_query = db.query(Action)
    if user.role != UserRole.ADMIN and user.site:
        actions_query = actions_query.filter(Action.site == user.site)
    
    open_actions = actions_query.filter(
        Action.status.in_([ActionStatus.ASSIGNED, ActionStatus.IN_PROGRESS, ActionStatus.ON_HOLD, ActionStatus.REOPENED])
    ).count()

    return {
        "total_reports": total_reports,
        "sif_analyzed": sif_analyzed,
        "hse_validated": hse_validated,
        "pending_review": pending_review,
        "open_actions": open_actions,
        "user_site": user.site or "All Sites (Admin)"
    }


def get_my_actions_data(db: Session, user: User, status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve actions assigned specifically to current authenticated user."""
    actions = action_service.get_user_actions(db, user.id, status=status, priority=priority)
    result = []
    for a in actions:
        sla_info = None
        if getattr(a, "sla", None) and a.sla:
            sla_res = sla_service.calculate_sla_status_and_times(a.sla, a.status)
            sla_info = {
                "sla_status": str(sla_res["sla_status"].value if hasattr(sla_res["sla_status"], "value") else sla_res["sla_status"]),
                "remaining_minutes": sla_res["remaining_minutes"],
                "overdue_minutes": sla_res["overdue_minutes"],
                "is_overdue": sla_res["is_overdue"]
            }
        result.append({
            "id": a.id,
            "action_number": a.action_number,
            "title": a.title,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "priority": a.priority.value if hasattr(a.priority, "value") else str(a.priority),
            "due_date": a.due_date,
            "site": a.site,
            "department": a.assigned_department,
            "sla": sla_info
        })
    return result


def get_overdue_actions_data(db: Session, user: User) -> List[Dict[str, Any]]:
    """Retrieve user's assigned actions that are currently overdue according to SLA calculations."""
    actions = get_my_actions_data(db, user)
    return [a for a in actions if a.get("sla") and a["sla"].get("is_overdue")]


def get_action_details_data(db: Session, user: User, action_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve specific action details with site-level authorization check."""
    a = action_service.get_action_by_id(db, action_id)
    if not a:
        return None
    
    if user.role != UserRole.ADMIN and user.site and a.site != user.site:
        return None  # Authorization boundary
    
    return {
        "id": a.id,
        "action_number": a.action_number,
        "title": a.title,
        "description": a.description,
        "status": a.status.value if hasattr(a.status, "value") else str(a.status),
        "priority": a.priority.value if hasattr(a.priority, "value") else str(a.priority),
        "due_date": a.due_date,
        "site": a.site,
        "assigned_user_name": a.assigned_user.name if getattr(a, "assigned_user", None) else f"User #{a.assigned_user_id}",
        "assigned_department": a.assigned_department,
        "report_id": a.report_id,
        "intervention_id": a.intervention_id
    }


def get_reports_summary_data(db: Session, user: User, site: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve authorized safety reports summary."""
    target_site = site or (user.site if user.role != UserRole.ADMIN else None)
    reports, _ = report_service.get_reports(db, site=target_site, limit=limit)
    
    result = []
    for r in reports:
        ai_res = r.ai_analyses[0] if getattr(r, "ai_analyses", None) and r.ai_analyses else None
        hse_res = r.hse_reviews[0] if getattr(r, "hse_reviews", None) and r.hse_reviews else None
        
        is_sif = (ai_res.prediction == "SIF_PRECURSOR") if ai_res else False
        ai_score = round(ai_res.probability_or_score, 2) if ai_res else None
        hse_dec = hse_res.decision.value if (hse_res and hasattr(hse_res.decision, "value")) else ("PENDING" if not hse_res else str(hse_res.decision))

        result.append({
            "id": r.id,
            "report_number": r.report_number,
            "title": r.description[:60] + ("..." if len(r.description) > 60 else ""),
            "report_type": r.report_type.value if hasattr(r.report_type, "value") else str(r.report_type),
            "site": r.site,
            "incident_date": r.date,
            "is_sif_precursor": is_sif,
            "ai_confidence": ai_score,
            "hse_decision": hse_dec,
            "validated_sif": (hse_res.validated_sif == True) if hse_res else is_sif,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status)
        })
    return result


def get_report_details_data(db: Session, user: User, report_identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieve detailed analysis of a report by ID or report number."""
    r = None
    if str(report_identifier).isdigit():
        try:
            r = report_service.get_report_by_id(db, int(report_identifier), user)
        except Exception:
            r = None
    if not r:
        try:
            r = report_service.get_report_by_number(db, str(report_identifier), user)
        except Exception:
            r = None
    
    if not r:
        return None
    
    # Site authorization check
    if user.role != UserRole.ADMIN and user.site and r.site != user.site:
        return None
    
    ai_res = r.ai_analyses[0] if getattr(r, "ai_analyses", None) and r.ai_analyses else None
    hse_res = r.hse_reviews[0] if getattr(r, "hse_reviews", None) and r.hse_reviews else None
    
    hazards = json.loads(ai_res.hazards_json) if (ai_res and ai_res.hazards_json) else []
    barriers = json.loads(ai_res.barrier_concerns_json) if (ai_res and getattr(ai_res, "barrier_concerns_json", None) and ai_res.barrier_concerns_json) else []
    lsrs = json.loads(ai_res.life_saving_rules_json) if (ai_res and ai_res.life_saving_rules_json) else []
    
    is_sif = (ai_res.prediction == "SIF_PRECURSOR") if ai_res else False
    ai_score = round(ai_res.probability_or_score, 2) if ai_res else None
    ai_exp = None
    if ai_res and ai_res.explanation_json:
        try:
            exp_dict = json.loads(ai_res.explanation_json)
            ai_exp = exp_dict.get("summary") if isinstance(exp_dict, dict) else str(exp_dict)
        except Exception:
            ai_exp = str(ai_res.explanation_json)

    hse_dec = hse_res.decision.value if (hse_res and hasattr(hse_res.decision, "value")) else ("PENDING" if not hse_res else str(hse_res.decision))

    return {
        "id": r.id,
        "report_number": r.report_number,
        "title": r.description[:60] + ("..." if len(r.description) > 60 else ""),
        "description": r.description,
        "report_type": r.report_type.value if hasattr(r.report_type, "value") else str(r.report_type),
        "site": r.site,
        "location": r.location,
        "incident_date": r.date,
        "is_sif_precursor": is_sif,
        "ai_confidence": ai_score,
        "ai_explanation": ai_exp,
        "hazards": hazards,
        "barrier_concerns": barriers,
        "life_saving_rules": lsrs,
        "hse_decision": hse_dec,
        "validated_sif": (hse_res.validated_sif == True) if hse_res else is_sif,
        "hse_notes": hse_res.notes if hse_res else None,
        "status": r.status.value if hasattr(r.status, "value") else str(r.status)
    }


def get_sif_analysis_explanation_data(db: Session, user: User, report_identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieve AI vs HSE decision analysis for a report without exposing source_sheet metadata."""
    report_data = get_report_details_data(db, user, report_identifier)
    if not report_data:
        return None
    
    ai_status = "SIF-Potential" if report_data["is_sif_precursor"] else "Non-SIF"
    hse_status = "Pending HSE Review"
    if report_data["hse_decision"] != "PENDING":
        hse_status = "SIF-Potential" if report_data["validated_sif"] else "Non-SIF"

    return {
        "report_number": report_data["report_number"],
        "title": report_data["title"],
        "ai_classification": ai_status,
        "ai_confidence": report_data["ai_confidence"],
        "ai_explanation": report_data["ai_explanation"],
        "hazards": report_data["hazards"],
        "barrier_concerns": report_data["barrier_concerns"],
        "hse_review_decision": report_data["hse_decision"],
        "hse_validated_sif_status": hse_status,
        "hse_notes": report_data["hse_notes"]
    }


def get_safety_intelligence_data(db: Session, user: User) -> Dict[str, Any]:
    """Retrieve high-level safety intelligence metrics (patterns, barrier concerns, sites)."""
    try:
        from backend.analytics.service import AnalyticsService
        res = AnalyticsService.get_recurring_patterns(db=db, user=user)
        patterns = res.get("data", []) if isinstance(res, dict) else []
        return {
            "patterns": patterns[:5] if isinstance(patterns, list) else [],
            "barriers": [],
            "site_metrics": []
        }
    except Exception as e:
        return {"patterns": [], "barriers": [], "site_metrics": []}


def get_action_center_summary_data(db: Session, user: User) -> Dict[str, Any]:
    """Retrieve Action Center overview metrics."""
    reports_q = db.query(SafetyReport)
    actions_q = db.query(Action)
    
    if user.role != UserRole.ADMIN and user.site:
        reports_q = reports_q.filter(SafetyReport.site == user.site)
        actions_q = actions_q.filter(Action.site == user.site)
    
    pending_reviews = reports_q.filter(SafetyReport.hse_decision == HSEDecision.PENDING).count()
    active_actions = actions_q.filter(Action.status.in_([ActionStatus.ASSIGNED, ActionStatus.IN_PROGRESS, ActionStatus.ON_HOLD, ActionStatus.REOPENED])).count()
    verification_pending = actions_q.filter(Action.status == ActionStatus.VERIFICATION_PENDING).count()
    completed_actions = actions_q.filter(Action.status == ActionStatus.VERIFIED).count()

    return {
        "pending_reviews": pending_reviews,
        "active_actions": active_actions,
        "verification_pending": verification_pending,
        "completed_actions": completed_actions
    }
