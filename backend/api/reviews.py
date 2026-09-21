from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, UserRole
from backend.database.schemas import APIResponse, ReviewCreate, ReviewResponse
from backend.security.dependencies import get_current_active_user, require_roles
from backend.services import review_service

router = APIRouter(prefix="/reports", tags=["HSE Reviews"])

@router.post("/{report_id}/review", response_model=APIResponse[ReviewResponse], status_code=status.HTTP_201_CREATED)
def submit_hse_review(
    report_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles([UserRole.HSE_MANAGER, UserRole.ADMIN]))
):
    """
    Submits an HSE review decision for a safety report.
    Only authorized HSE Managers and Admins may access this endpoint.
    """
    review = review_service.create_hse_review(db, report_id, review_data, reviewer)
    resp = ReviewResponse.model_validate(review)
    resp.reviewer_name = reviewer.name
    return APIResponse(
        success=True,
        message="HSE review submitted successfully.",
        data=resp
    )

@router.get("/{report_id}/review", response_model=APIResponse[List[ReviewResponse]])
def get_hse_reviews(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves all HSE review entries for a given report."""
    reviews = review_service.get_hse_reviews_for_report(db, report_id, current_user)
    responses = []
    for r in reviews:
        r_resp = ReviewResponse.model_validate(r)
        r_resp.reviewer_name = r.reviewer.name if r.reviewer else None
        responses.append(r_resp)

    return APIResponse(
        success=True,
        message="HSE reviews retrieved successfully.",
        data=responses
    )
