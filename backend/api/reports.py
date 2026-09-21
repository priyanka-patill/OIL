from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, ReportType, ReportStatus
from backend.database.schemas import (
    APIResponse, ReportCreate, ReportUpdate, ReportResponse, 
    ReportListResponse, AIAnalysisResponse, ReportAttachmentResponse
)
from backend.security.dependencies import get_current_active_user
from backend.services import report_service, analysis_service, attachment_service

router = APIRouter(prefix="/reports", tags=["Safety Reports"])

@router.post("", response_model=APIResponse[ReportResponse], status_code=status.HTTP_201_CREATED)
def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submits a new safety observation report for the authenticated user."""
    report = report_service.create_report(db, report_data, current_user)
    resp = ReportResponse.model_validate(report)
    resp.creator_name = current_user.name
    if report.ai_analyses and len(report.ai_analyses) > 0:
        resp.ai_analysis = AIAnalysisResponse.model_validate(report.ai_analyses[-1])
    return APIResponse(
        success=True,
        message="Safety report created successfully.",
        data=resp
    )

@router.get("", response_model=APIResponse[ReportListResponse])
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    site: Optional[str] = Query(None),
    report_type: Optional[ReportType] = Query(None),
    status: Optional[ReportStatus] = Query(None),
    department: Optional[str] = Query(None),
    own_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves paginated safety reports with filtering and access control."""
    result = report_service.get_reports_paginated(
        db, current_user, page=page, page_size=page_size,
        search=search, site=site, report_type=report_type,
        status_filter=status, department=department, own_only=own_only
    )
    
    report_responses = []
    for r in result["reports"]:
        r_resp = ReportResponse.model_validate(r)
        r_resp.creator_name = r.creator.name if r.creator else None
        if r.ai_analyses and len(r.ai_analyses) > 0:
            r_resp.ai_analysis = AIAnalysisResponse.model_validate(r.ai_analyses[-1])
        report_responses.append(r_resp)

    list_resp = ReportListResponse(
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
        reports=report_responses
    )
    return APIResponse(
        success=True,
        message="Safety reports retrieved successfully.",
        data=list_resp
    )

@router.get("/{report_id}", response_model=APIResponse[ReportResponse])
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves a single safety report by ID."""
    report = report_service.get_report_by_id(db, report_id, current_user)
    resp = ReportResponse.model_validate(report)
    resp.creator_name = report.creator.name if report.creator else None
    if report.ai_analyses and len(report.ai_analyses) > 0:
        resp.ai_analysis = AIAnalysisResponse.model_validate(report.ai_analyses[-1])
    if report.attachments:
        resp.attachments = [ReportAttachmentResponse.model_validate(att) for att in report.attachments]
    return APIResponse(
        success=True,
        message="Safety report retrieved successfully.",
        data=resp
    )

@router.put("/{report_id}", response_model=APIResponse[ReportResponse])
def update_report(
    report_id: int,
    update_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Updates a safety report."""
    report = report_service.update_report(db, report_id, update_data, current_user)
    resp = ReportResponse.model_validate(report)
    resp.creator_name = report.creator.name if report.creator else None
    if report.ai_analyses and len(report.ai_analyses) > 0:
        resp.ai_analysis = AIAnalysisResponse.model_validate(report.ai_analyses[-1])
    if report.attachments:
        resp.attachments = [ReportAttachmentResponse.model_validate(att) for att in report.attachments]
    return APIResponse(
        success=True,
        message="Safety report updated successfully.",
        data=resp
    )

@router.post("/{report_id}/attachments", response_model=APIResponse[List[ReportAttachmentResponse]], status_code=status.HTTP_201_CREATED)
def upload_report_attachments(
    report_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Uploads one or more supporting file attachments (photos/permits) for a safety report."""
    uploaded_attachments = []
    for file in files:
        att = attachment_service.save_attachment(db, report_id, file, current_user)
        uploaded_attachments.append(ReportAttachmentResponse.model_validate(att))

    return APIResponse(
        success=True,
        message=f"Successfully attached {len(uploaded_attachments)} file(s) to Report #{report_id}.",
        data=uploaded_attachments
    )

@router.get("/{report_id}/attachments", response_model=APIResponse[List[ReportAttachmentResponse]])
def get_report_attachments(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves all attachments associated with a safety report."""
    attachments = attachment_service.get_report_attachments(db, report_id, current_user)
    resp_list = [ReportAttachmentResponse.model_validate(att) for att in attachments]
    return APIResponse(
        success=True,
        message="Report attachments retrieved successfully.",
        data=resp_list
    )
