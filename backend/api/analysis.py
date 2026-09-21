from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.database.schemas import APIResponse, AIAnalysisResponse
from backend.security.dependencies import get_current_active_user
from backend.services import analysis_service

router = APIRouter(prefix="/reports", tags=["AI Safety Analysis"])

@router.post("/{report_id}/analyze", response_model=APIResponse[AIAnalysisResponse], status_code=status.HTTP_200_OK)
def trigger_analysis(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Triggers or re-runs Part 1C AI safety analysis for a report."""
    analysis = analysis_service.analyze_safety_report(db, report_id, current_user)
    resp = AIAnalysisResponse.model_validate(analysis)
    return APIResponse(
        success=True,
        message="AI Safety Analysis executed and persisted successfully.",
        data=resp
    )

@router.get("/{report_id}/analysis", response_model=APIResponse[AIAnalysisResponse])
def get_analysis(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves persisted AI safety analysis for a report."""
    analysis = analysis_service.get_analysis_for_report(db, report_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI analysis found for report #{report_id}."
        )
    resp = AIAnalysisResponse.model_validate(analysis)
    return APIResponse(
        success=True,
        message="AI Safety Analysis retrieved successfully.",
        data=resp
    )
