"""
Part 4A — Intervention Service

Manages persistence, retrieval, idempotency, and audit logging for evidence-based
Intervention Recommendations.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.database.models import (
    SafetyReport, AIAnalysis, InterventionRecommendation, HSEInterventionReview,
    InterventionStatus, InterventionCategory, InterventionPriority,
    HSEInterventionDecision, User, UserRole
)
from backend.services import intervention_recommendation_engine, audit_service

logger = logging.getLogger("backend.services.intervention_service")


def generate_recommendation_for_report(
    db: Session,
    report_id: int,
    current_user: User
) -> InterventionRecommendation:
    """
    Generates and persists an evidence-based Intervention Recommendation for a report.
    Idempotent: prevents duplicate recommendations for the same (report_id, category) pair.
    """
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID #{report_id} not found."
        )

    # Site-level authorization check
    if current_user.site and report.site != current_user.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized access to report from site '{report.site}'."
        )

    # Fetch AI analysis if available
    ai_analysis = db.query(AIAnalysis).filter(AIAnalysis.report_id == report_id).first()

    report_dict = {
        "id": report.id,
        "report_number": report.report_number,
        "description": report.description,
        "site": report.site,
        "refinery_unit": report.refinery_unit,
        "equipment_id": report.equipment_id,
        "work_type": report.work_type,
        "activity": report.activity,
        "department": report.department,
        "date": report.date,
        "action_status": report.action_status,
        "ppe_noncompliance": report.ppe_noncompliance,
        "supervisor_negligence": report.supervisor_negligence,
        "maintenance_delay_or_issue": report.maintenance_delay_or_issue,
        "repeated_issue_ignored": report.repeated_issue_ignored,
    }

    ai_dict = None
    if ai_analysis:
        ai_dict = {
            "id": ai_analysis.id,
            "model_version": ai_analysis.model_version,
            "prediction": ai_analysis.prediction,
            "probability": ai_analysis.probability_or_score,
            "life_saving_rules_json": ai_analysis.life_saving_rules_json,
            "hazards_json": ai_analysis.hazards_json,
            "barrier_concerns_json": ai_analysis.barrier_concerns_json,
        }

    # Generate recommendation structure
    payload = intervention_recommendation_engine.generate_recommendation_payload(
        report_data=report_dict,
        ai_analysis_data=ai_dict,
    )

    cat = payload["category"]

    # Idempotency check: check if recommendation already exists for this report and category
    existing = db.query(InterventionRecommendation).filter(
        InterventionRecommendation.report_id == report_id,
        InterventionRecommendation.category == cat
    ).first()

    if existing:
        logger.info(f"Returning existing recommendation #{existing.id} for report #{report_id} and category {cat.value}")
        return existing

    # Generate unique recommendation number
    rec_number = f"REC-R{report_id}-{cat.value[:4]}-{int(db.query(InterventionRecommendation).count()) + 1:04d}"

    rec = InterventionRecommendation(
        recommendation_number=rec_number,
        report_id=report.id,
        analysis_id=ai_analysis.id if ai_analysis else None,
        barrier_category=payload.get("barrier_category"),
        title=payload["title"],
        category=payload["category"],
        recommendation_text=payload["recommendation_text"],
        rationale=payload["rationale"],
        priority_suggestion=payload["priority_suggestion"],
        evidence_summary=payload["evidence_summary"],
        evidence_json=payload["evidence_json"],
        evidence_count=payload["evidence_count"],
        first_observed=payload["first_observed"],
        latest_observed=payload["latest_observed"],
        sif_classification=payload["sif_classification"],
        hazards_json=payload["hazards_json"],
        life_saving_rules_json=payload["life_saving_rules_json"],
        bdi_score=payload["bdi_score"],
        escalation_indicators_json=payload["escalation_indicators_json"],
        model_version=payload["model_version"],
        analytics_version=payload["analytics_version"],
        methodology_version=payload["methodology_version"],
        status=InterventionStatus.PENDING_HSE_VALIDATION,
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Audit logging
    audit_service.log_audit_event(
        db=db,
        action="INTERVENTION_RECOMMENDATION_GENERATED",
        user_id=current_user.id,
        entity_type="InterventionRecommendation",
        entity_id=str(rec.id),
        metadata={
            "report_id": report_id,
            "category": rec.category.value,
            "priority_suggestion": rec.priority_suggestion.value
        }
    )

    logger.info(f"Generated Intervention Recommendation #{rec.id} ({rec.recommendation_number}) for Report #{report_id}")
    return rec


def get_interventions_for_report(db: Session, report_id: int) -> List[InterventionRecommendation]:
    """Retrieves all persisted intervention recommendations for a report."""
    return db.query(InterventionRecommendation).filter(
        InterventionRecommendation.report_id == report_id
    ).all()


def get_intervention_by_id(db: Session, intervention_id: int) -> Optional[InterventionRecommendation]:
    """Retrieves a specific intervention recommendation by primary ID."""
    return db.query(InterventionRecommendation).filter(
        InterventionRecommendation.id == intervention_id
    ).first()


def get_all_interventions(
    db: Session,
    user: User,
    category: Optional[str] = None,
    priority_suggestion: Optional[str] = None,
    site: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieves a paginated list of intervention recommendations with authorization and filter support.
    """
    query = db.query(InterventionRecommendation).join(
        SafetyReport, InterventionRecommendation.report_id == SafetyReport.id, isouter=True
    )

    # Site-level authorization check
    if user.site:
        query = query.filter(SafetyReport.site == user.site)
    elif site:
        query = query.filter(SafetyReport.site == site)

    if department:
        query = query.filter(SafetyReport.department == department)

    if category:
        try:
            cat_enum = InterventionCategory[category.upper()]
            query = query.filter(InterventionRecommendation.category == cat_enum)
        except KeyError:
            pass

    if priority_suggestion:
        try:
            pri_enum = InterventionPriority[priority_suggestion.upper()]
            query = query.filter(InterventionRecommendation.priority_suggestion == pri_enum)
        except KeyError:
            pass

    total = query.count()
    recommendations = query.order_by(InterventionRecommendation.id.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "recommendations": recommendations,
    }


def submit_intervention_review(
    db: Session,
    intervention_id: int,
    current_user: User,
    review_payload: Dict[str, Any]
) -> HSEInterventionReview:
    """
    Submits a human-in-the-loop HSE Review (ACCEPT, MODIFY, REJECT) for an Intervention Recommendation.
    Immutability Principle: Preserves original AI recommendation fields untouched.
    Does NOT create operational actions or start SLA clocks.
    """
    rec = db.query(InterventionRecommendation).filter(InterventionRecommendation.id == intervention_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention recommendation #{intervention_id} not found."
        )

    # Site-level authorization check
    if current_user.site and rec.report and rec.report.site != current_user.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to intervention recommendation for review."
        )

    # Validate decision string
    raw_decision = review_payload.get("decision", "").upper()
    try:
        decision_enum = HSEInterventionDecision[raw_decision]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid HSE decision '{raw_decision}'. Must be one of ACCEPT, MODIFY, REJECT."
        )

    rejection_reason = review_payload.get("rejection_reason")
    review_comment = review_payload.get("review_comment")

    # Reject workflow validation: Rejection reason is mandatory!
    if decision_enum == HSEInterventionDecision.REJECT:
        if not rejection_reason or not str(rejection_reason).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid rejection reason is mandatory when rejecting an intervention recommendation."
            )

    # Modify workflow validation & processing
    modified_title = None
    modified_text = None
    modified_category = None
    modified_priority = None
    proposed_owner_id = review_payload.get("proposed_owner_id")
    proposed_dept = review_payload.get("proposed_department")
    proposed_due_date = review_payload.get("proposed_due_date")

    if decision_enum == HSEInterventionDecision.MODIFY:
        raw_m_title = review_payload.get("modified_title")
        modified_title = raw_m_title.strip() if (raw_m_title and isinstance(raw_m_title, str) and raw_m_title.strip()) else rec.title

        raw_m_text = review_payload.get("modified_recommendation_text")
        if raw_m_text is not None and not str(raw_m_text).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modified recommendation text cannot be empty when decision is MODIFY."
            )
        modified_text = raw_m_text.strip() if (raw_m_text and isinstance(raw_m_text, str) and raw_m_text.strip()) else rec.recommendation_text
        
        raw_cat = review_payload.get("modified_category")
        if raw_cat:
            try:
                modified_category = InterventionCategory[raw_cat.upper()]
            except KeyError:
                modified_category = rec.category
        else:
            modified_category = rec.category

        raw_pri = review_payload.get("modified_priority")
        if raw_pri:
            try:
                modified_priority = InterventionPriority[raw_pri.upper()]
            except KeyError:
                modified_priority = rec.priority_suggestion
        else:
            modified_priority = rec.priority_suggestion

        if not modified_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modified recommendation text cannot be empty."
            )

    # Proposed due date validation (basic format validation)
    if proposed_due_date:
        proposed_due_date = str(proposed_due_date).strip()
        if len(proposed_due_date) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid proposed due date format. Expected YYYY-MM-DD."
            )

    # Proposed owner validation
    if proposed_owner_id:
        owner_user = db.query(User).filter(User.id == proposed_owner_id).first()
        if not owner_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposed owner User #{proposed_owner_id} does not exist."
            )

    # Update recommendation status (Immutability check: AI fields remain unchanged!)
    if decision_enum == HSEInterventionDecision.ACCEPT:
        rec.status = InterventionStatus.ACCEPTED
    elif decision_enum == HSEInterventionDecision.MODIFY:
        rec.status = InterventionStatus.MODIFIED
    elif decision_enum == HSEInterventionDecision.REJECT:
        rec.status = InterventionStatus.REJECTED

    # Build Review Record
    review = HSEInterventionReview(
        intervention_id=rec.id,
        reviewer_id=current_user.id,
        decision=decision_enum,
        rejection_reason=rejection_reason.strip() if rejection_reason else None,
        review_comment=review_comment.strip() if review_comment else None,
        modified_title=modified_title,
        modified_recommendation_text=modified_text,
        modified_category=modified_category,
        modified_priority=modified_priority,
        proposed_owner_id=proposed_owner_id,
        proposed_department=proposed_dept.strip() if proposed_dept else None,
        proposed_due_date=proposed_due_date,
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    db.refresh(rec)

    # Audit logging
    audit_service.log_audit_event(
        db=db,
        action=f"INTERVENTION_REVIEW_{decision_enum.value}",
        user_id=current_user.id,
        entity_type="HSEInterventionReview",
        entity_id=str(review.id),
        metadata={
            "intervention_id": intervention_id,
            "decision": decision_enum.value,
            "recommendation_number": rec.recommendation_number,
            "status": rec.status.value,
        }
    )

    logger.info(f"HSE Review #{review.id} ({decision_enum.value}) submitted for Intervention Recommendation #{rec.id} by User #{current_user.id}")
    return review


def get_intervention_reviews(db: Session, intervention_id: int) -> List[HSEInterventionReview]:
    """Retrieves all HSE review decision history records for a given intervention recommendation."""
    return db.query(HSEInterventionReview).filter(
        HSEInterventionReview.intervention_id == intervention_id
    ).order_by(HSEInterventionReview.id.desc()).all()

