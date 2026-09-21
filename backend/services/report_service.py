import math
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.database.models import SafetyReport, User, UserRole, ReportStatus, ReportType
from backend.database.schemas import ReportCreate, ReportUpdate
from backend.services.audit_service import log_audit_event

def generate_unique_report_number(db: Session) -> str:
    """Generates a unique, traceable report number format (e.g., OIL-2026-000001)."""
    current_year = datetime.now().year
    prefix = f"OIL-{current_year}-"
    
    last_report = db.query(SafetyReport).filter(
        SafetyReport.report_number.like(f"{prefix}%")
    ).order_by(SafetyReport.id.desc()).first()

    if not last_report:
        next_seq = 1
    else:
        try:
            seq_part = last_report.report_number.split("-")[-1]
            next_seq = int(seq_part) + 1
        except Exception:
            next_seq = db.query(SafetyReport).count() + 1

    return f"{prefix}{next_seq:06d}"

def create_report(db: Session, report_data: ReportCreate, user: User) -> SafetyReport:
    """Creates a new safety observation report for the authenticated user."""
    report_num = generate_unique_report_number(db)

    report = SafetyReport(
        report_number=report_num,
        created_by=user.id,
        report_type=report_data.report_type,
        date=report_data.date,
        site=report_data.site,
        refinery_unit=report_data.refinery_unit,
        location=report_data.location,
        equipment_id=report_data.equipment_id,
        work_type=report_data.work_type,
        activity=report_data.activity,
        department=report_data.department or user.department,
        description=report_data.description.strip(),
        
        ppe_noncompliance=report_data.ppe_noncompliance,
        supervisor_negligence=report_data.supervisor_negligence,
        maintenance_delay_or_issue=report_data.maintenance_delay_or_issue,
        repeated_issue_ignored=report_data.repeated_issue_ignored,
        previous_similar_reports=report_data.previous_similar_reports,

        immediate_cause=report_data.immediate_cause,
        potential_consequence=report_data.potential_consequence,
        risk_level=report_data.risk_level,
        corrective_action=report_data.corrective_action,
        action_status=report_data.action_status,

        status=ReportStatus.SUBMITTED
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    log_audit_event(
        db, action="REPORT_CREATED", user_id=user.id,
        entity_type="SafetyReport", entity_id=report.id,
        metadata={"report_number": report.report_number, "site": report.site, "type": report.report_type.value}
    )

    # Automatically trigger system-calculated similarity, ML prediction, and risk assessment
    try:
        from backend.services.analysis_service import analyze_safety_report
        analyze_safety_report(db, report.id, user)
        db.refresh(report)
    except Exception as e:
        # Non-fatal: Report record created, analysis error logged
        import logging
        logging.getLogger("backend.services.report_service").error(f"Automatic analysis execution failed for report #{report.id}: {e}")

    return report

def get_reports_paginated(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    site: Optional[str] = None,
    report_type: Optional[ReportType] = None,
    status_filter: Optional[ReportStatus] = None,
    department: Optional[str] = None,
    own_only: bool = False
) -> Dict[str, Any]:
    """Retrieves paginated safety reports with filtering and access control."""
    query = db.query(SafetyReport)

    # Access control scoping
    if user.role == UserRole.HSE_USER or own_only:
        query = query.filter(SafetyReport.created_by == user.id)

    if search:
        s_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                SafetyReport.report_number.ilike(s_term),
                SafetyReport.description.ilike(s_term),
                SafetyReport.equipment_id.ilike(s_term),
                SafetyReport.location.ilike(s_term)
            )
        )

    if site:
        query = query.filter(SafetyReport.site == site)

    if report_type:
        query = query.filter(SafetyReport.report_type == report_type)

    if status_filter:
        query = query.filter(SafetyReport.status == status_filter)

    if department:
        query = query.filter(SafetyReport.department == department)

    total = query.count()
    page_size = min(max(1, page_size), 100) # Cap page_size max 100
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    page = min(max(1, page), total_pages)

    offset = (page - 1) * page_size
    reports = query.order_by(SafetyReport.id.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "reports": reports
    }

def get_report_by_id(db: Session, report_id: int, user: User) -> SafetyReport:
    """Retrieves a single report by ID with ownership/role permission checks."""
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safety report not found.")

    # Access control
    if user.role == UserRole.HSE_USER and report.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. You do not have permission to view this report."
        )

    log_audit_event(
        db, action="REPORT_VIEWED", user_id=user.id,
        entity_type="SafetyReport", entity_id=report.id
    )
    return report

def update_report(db: Session, report_id: int, update_data: ReportUpdate, user: User) -> SafetyReport:
    """Updates a safety report."""
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safety report not found.")

    # Only creator or HSE Manager / Admin can update
    if user.role == UserRole.HSE_USER and report.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this report."
        )

    up_dict = update_data.model_dump(exclude_unset=True)
    changes = list(up_dict.keys())

    for key, val in up_dict.items():
        if hasattr(report, key) and val is not None:
            setattr(report, key, val)

    db.commit()
    db.refresh(report)

    log_audit_event(
        db, action="REPORT_UPDATED", user_id=user.id,
        entity_type="SafetyReport", entity_id=report.id,
        metadata={"updated_fields": changes}
    )
    return report
