import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.database.models import SafetyReport, HSEReview, User, UserRole, HSEDecision, ReportStatus
from backend.database.schemas import ReviewCreate
from backend.services.audit_service import log_audit_event

def create_hse_review(db: Session, report_id: int, review_data: ReviewCreate, reviewer: User) -> HSEReview:
    """
    Submits an HSE review decision for a safety report.
    Only HSE_MANAGER and ADMIN roles are authorized.
    """
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safety report not found.")

    if review_data.hse_decision == HSEDecision.REJECTED and (not review_data.review_comment or not review_data.review_comment.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection decision requires a mandatory review comment."
        )

    review = HSEReview(
        report_id=report.id,
        reviewer_id=reviewer.id,
        ai_prediction_accepted=review_data.ai_prediction_accepted,
        hse_decision=review_data.hse_decision,
        modified_classification=review_data.modified_classification,
        modified_lsr_json=json.dumps(review_data.modified_lsr) if review_data.modified_lsr else None,
        modified_hazards_json=json.dumps(review_data.modified_hazards) if review_data.modified_hazards else None,
        modified_barrier_concerns_json=json.dumps(review_data.modified_barrier_concerns) if review_data.modified_barrier_concerns else None,
        review_comment=review_data.review_comment
    )

    db.add(review)

    # Update report status
    if review_data.hse_decision == HSEDecision.ACCEPTED:
        report.status = ReportStatus.HSE_VALIDATED
    elif review_data.hse_decision == HSEDecision.MODIFIED:
        report.status = ReportStatus.ACTION_REQUIRED
    elif review_data.hse_decision == HSEDecision.REJECTED:
        report.status = ReportStatus.CLOSED

    db.commit()
    db.refresh(review)
    db.refresh(report)

    log_audit_event(
        db, action="HSE_REVIEW_CREATED", user_id=reviewer.id,
        entity_type="HSEReview", entity_id=review.id,
        metadata={
            "report_id": report.id,
            "report_number": report.report_number,
            "decision": review.hse_decision.value
        }
    )
    return review

def get_hse_reviews_for_report(db: Session, report_id: int, user: User) -> List[HSEReview]:
    """Retrieves all HSE review entries for a given report."""
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safety report not found.")

    if user.role == UserRole.HSE_USER and report.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view reviews for this report."
        )

    reviews = db.query(HSEReview).filter(HSEReview.report_id == report_id).order_by(HSEReview.id.desc()).all()
    return reviews
