"""
Part 4A & 4B — Intervention Recommendations & HSE Review API Router

Exposes REST endpoints to generate, list, inspect, and perform human-in-the-loop HSE Review
(ACCEPT, MODIFY, REJECT) for evidence-based intervention recommendations.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.database import get_db
from backend.database.models import User, UserRole
from backend.security.dependencies import get_current_user
from backend.services import intervention_service

router = APIRouter(prefix="/interventions", tags=["Intervention Recommendation Foundation & HSE Review"])


class InterventionGenerateRequest(BaseModel):
    report_id: int


class InterventionReviewSubmitRequest(BaseModel):
    decision: str  # ACCEPT, MODIFY, REJECT
    rejection_reason: Optional[str] = None
    review_comment: Optional[str] = None
    modified_title: Optional[str] = None
    modified_recommendation_text: Optional[str] = None
    modified_category: Optional[str] = None
    modified_priority: Optional[str] = None
    proposed_owner_id: Optional[int] = None
    proposed_department: Optional[str] = None
    proposed_due_date: Optional[str] = None


def format_review_dict(rev) -> Optional[dict]:
    """Helper serializer for HSEInterventionReview ORM model."""
    if not rev:
        return None
    return {
        "id": rev.id,
        "intervention_id": rev.intervention_id,
        "reviewer_id": rev.reviewer_id,
        "reviewer_name": rev.reviewer.name if getattr(rev, "reviewer", None) else f"User #{rev.reviewer_id}",
        "decision": rev.decision.value if hasattr(rev.decision, "value") else str(rev.decision),
        "rejection_reason": rev.rejection_reason,
        "review_comment": rev.review_comment,
        "modified_title": rev.modified_title,
        "modified_recommendation_text": rev.modified_recommendation_text,
        "modified_category": rev.modified_category.value if hasattr(rev.modified_category, "value") else (str(rev.modified_category) if rev.modified_category else None),
        "modified_priority": rev.modified_priority.value if hasattr(rev.modified_priority, "value") else (str(rev.modified_priority) if rev.modified_priority else None),
        "proposed_owner_id": rev.proposed_owner_id,
        "proposed_owner_name": rev.proposed_owner.name if getattr(rev, "proposed_owner", None) else (f"User #{rev.proposed_owner_id}" if rev.proposed_owner_id else None),
        "proposed_department": rev.proposed_department,
        "proposed_due_date": rev.proposed_due_date,
        "reviewed_at": rev.reviewed_at.isoformat() if rev.reviewed_at else None,
    }


def format_intervention_dict(rec) -> dict:
    """Helper serializer for InterventionRecommendation ORM model."""
    import json
    latest_rev = rec.reviews[0] if getattr(rec, "reviews", None) and len(rec.reviews) > 0 else None
    
    return {
        "id": rec.id,
        "recommendation_number": rec.recommendation_number,
        "report_id": rec.report_id,
        "analysis_id": rec.analysis_id,
        "recurring_pattern_id": rec.recurring_pattern_id,
        "barrier_category": rec.barrier_category,
        "title": rec.title,
        "category": rec.category.value if hasattr(rec.category, "value") else str(rec.category),
        "recommendation_text": rec.recommendation_text,
        "rationale": rec.rationale,
        "priority_suggestion": rec.priority_suggestion.value if hasattr(rec.priority_suggestion, "value") else str(rec.priority_suggestion),
        "evidence_summary": rec.evidence_summary,
        "evidence_payload": json.loads(rec.evidence_json) if rec.evidence_json else {},
        "evidence_count": rec.evidence_count,
        "first_observed": rec.first_observed,
        "latest_observed": rec.latest_observed,
        "sif_classification": rec.sif_classification,
        "hazards": json.loads(rec.hazards_json) if rec.hazards_json else [],
        "life_saving_rules": json.loads(rec.life_saving_rules_json) if rec.life_saving_rules_json else [],
        "bdi_score": rec.bdi_score,
        "escalation_indicators": json.loads(rec.escalation_indicators_json) if rec.escalation_indicators_json else [],
        "model_version": rec.model_version,
        "analytics_version": rec.analytics_version,
        "methodology_version": rec.methodology_version,
        "status": rec.status.value if hasattr(rec.status, "value") else str(rec.status),
        "validation_notice": "AI-Suggested Intervention — HSE Validation Required",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        "latest_review": format_review_dict(latest_rev),
        "review_count": len(rec.reviews) if getattr(rec, "reviews", None) else 0,
    }


@router.post("/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_intervention(
    body: InterventionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates an evidence-based Intervention Recommendation for a report."""
    rec = intervention_service.generate_recommendation_for_report(
        db=db,
        report_id=body.report_id,
        current_user=current_user,
    )
    return {
        "success": True,
        "message": "AI-Suggested Intervention Recommendation generated successfully.",
        "data": format_intervention_dict(rec),
    }


@router.get("", response_model=dict)
def list_interventions(
    category: Optional[str] = Query(None, description="Filter by intervention category"),
    priority_suggestion: Optional[str] = Query(None, description="Filter by suggested priority (HIGH, MEDIUM, LOW, INSUFFICIENT_DATA)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (PENDING_HSE_VALIDATION, ACCEPTED, MODIFIED, REJECTED)"),
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves paginated list of intervention recommendations."""
    res = intervention_service.get_all_interventions(
        db=db,
        user=current_user,
        category=category,
        priority_suggestion=priority_suggestion,
        site=site,
        department=department,
        limit=limit,
        offset=offset,
    )
    formatted = [format_intervention_dict(r) for r in res["recommendations"]]
    return {
        "success": True,
        "message": "Intervention recommendations retrieved successfully.",
        "data": {
            "total": res["total"],
            "limit": res["limit"],
            "offset": res["offset"],
            "recommendations": formatted,
        },
    }


@router.get("/{intervention_id}", response_model=dict)
def get_intervention_detail(
    intervention_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves detailed profile for a specific intervention recommendation by ID."""
    rec = intervention_service.get_intervention_by_id(db=db, intervention_id=intervention_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention recommendation #{intervention_id} not found."
        )

    # Site-level authorization check
    if current_user.site and rec.report and rec.report.site != current_user.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to intervention recommendation."
        )

    return {
        "success": True,
        "message": "Intervention recommendation retrieved successfully.",
        "data": format_intervention_dict(rec),
    }


@router.get("/report/{report_id}", response_model=dict)
def get_interventions_by_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all intervention recommendations associated with a specific report."""
    recs = intervention_service.get_interventions_for_report(db=db, report_id=report_id)
    formatted = [format_intervention_dict(r) for r in recs]
    return {
        "success": True,
        "message": f"Intervention recommendations for Report #{report_id} retrieved successfully.",
        "data": formatted,
    }


@router.post("/{intervention_id}/review", response_model=dict, status_code=status.HTTP_200_OK)
def submit_intervention_review(
    intervention_id: int,
    body: InterventionReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a human-in-the-loop HSE Review decision (ACCEPT, MODIFY, REJECT) for an intervention recommendation.
    Enforces authorization and server-side reviewer identity.
    """
    review = intervention_service.submit_intervention_review(
        db=db,
        intervention_id=intervention_id,
        current_user=current_user,
        review_payload=body.model_dump(),
    )
    rec = intervention_service.get_intervention_by_id(db=db, intervention_id=intervention_id)
    return {
        "success": True,
        "message": f"HSE Review decision '{review.decision.value}' recorded successfully.",
        "data": {
            "intervention": format_intervention_dict(rec),
            "review": format_review_dict(review),
        },
    }


@router.get("/{intervention_id}/review/history", response_model=dict)
def get_intervention_review_history(
    intervention_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves full HSE review audit history records for an intervention recommendation."""
    rec = intervention_service.get_intervention_by_id(db=db, intervention_id=intervention_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention recommendation #{intervention_id} not found."
        )

    if current_user.site and rec.report and rec.report.site != current_user.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to intervention review history."
        )

    reviews = intervention_service.get_intervention_reviews(db=db, intervention_id=intervention_id)
    formatted = [format_review_dict(r) for r in reviews]
    return {
        "success": True,
        "message": f"HSE review history for Intervention #{intervention_id} retrieved successfully.",
        "data": formatted,
    }
