"""
Analytics Data Access Layer (Part 3A)

Extracts and joins SafetyReport, AIAnalysis, and HSEReview records,
enforcing RBAC authorization filtering BEFORE aggregation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database.models import SafetyReport, AIAnalysis, HSEReview, User, UserRole
from backend.analytics.config import MISSING_VALUE_PLACEHOLDER


@dataclass
class AnalyticsReportDTO:
    """Internal DTO representing a safety report for analytical processing."""

    # Core Identifiers
    report_id: int
    report_number: str
    created_by: int
    report_type: str
    date: str
    status: str

    # Categorical & Location Dimensions
    site: str
    refinery_unit: str
    location: str
    equipment_id: str
    work_type: str
    activity: str
    department: str
    description: str

    # Precursor Flags
    ppe_noncompliance: bool
    supervisor_negligence: bool
    maintenance_delay_or_issue: bool
    repeated_issue_ignored: bool
    previous_similar_reports: int
    action_status: Optional[str] = None

    # AI Analysis Information (if available)
    has_ai_analysis: bool = False
    ai_model_version: Optional[str] = None
    ai_prediction: Optional[str] = None
    ai_classification: Optional[int] = None
    ai_probability_or_score: Optional[float] = None
    ai_hazards: List[str] = field(default_factory=list)
    ai_barriers: List[str] = field(default_factory=list)
    ai_lsrs: List[str] = field(default_factory=list)

    # HSE Review Information (if available)
    has_hse_review: bool = False
    hse_decision: Optional[str] = None
    hse_classification: Optional[int] = None
    hse_hazards: List[str] = field(default_factory=list)
    hse_barriers: List[str] = field(default_factory=list)
    hse_lsrs: List[str] = field(default_factory=list)
    reviewer_id: Optional[int] = None

    # Normalized dimension cache (populated by normalization layer)
    normalized: Dict[str, str] = field(default_factory=dict)

    def is_sif_ai(self) -> bool:
        """Returns True if AI predicted SIF-Potential (classification == 1)."""
        return self.ai_classification == 1

    def is_sif_hse(self) -> Optional[bool]:
        """Returns True if HSE validated/modified as SIF (classification == 1), None if no review."""
        if not self.has_hse_review or self.hse_classification is None:
            return None
        return self.hse_classification == 1

    def get_effective_hazards(self) -> List[str]:
        """Returns HSE validated hazards if available, else AI hazards."""
        if self.has_hse_review and self.hse_hazards:
            return self.hse_hazards
        return self.ai_hazards

    def get_effective_barriers(self) -> List[str]:
        """Returns HSE validated barriers if available, else AI barriers."""
        if self.has_hse_review and self.hse_barriers:
            return self.hse_barriers
        return self.ai_barriers

    def get_effective_lsrs(self) -> List[str]:
        """Returns HSE validated LSRs if available, else AI LSRs."""
        if self.has_hse_review and self.hse_lsrs:
            return self.hse_lsrs
        return self.ai_lsrs


def _parse_json_list(raw_json: Optional[str]) -> List[str]:
    """Safely parse a JSON list string or return empty list."""
    if not raw_json:
        return []
    try:
        data = json.loads(raw_json)
        if isinstance(data, list):
            return [str(item) for item in data]
        return []
    except (json.JSONDecodeError, TypeError):
        return []


def get_analytics_reports(
    db: Session,
    user: Optional[User] = None,
    site_filter: Optional[str] = None,
    refinery_unit_filter: Optional[str] = None,
    department_filter: Optional[str] = None,
    report_type_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sif_only: Optional[bool] = None,
) -> List[AnalyticsReportDTO]:
    """
    Fetch safety reports with associated AI Analysis and HSE Review,
    enforcing RBAC authorization prior to aggregation.
    """
    query = select(SafetyReport)

    # 1. Enforce RBAC Site/Department Authorization BEFORE loading records
    if user and user.role == UserRole.HSE_USER:
        if user.site:
            query = query.where(SafetyReport.site == user.site)
        if user.department:
            query = query.where(SafetyReport.department == user.department)

    # 2. Apply optional explicit user filters
    if site_filter:
        query = query.where(SafetyReport.site == site_filter)
    if refinery_unit_filter:
        query = query.where(SafetyReport.refinery_unit == refinery_unit_filter)
    if department_filter:
        query = query.where(SafetyReport.department == department_filter)
    if report_type_filter:
        query = query.where(SafetyReport.report_type == report_type_filter)
    if start_date:
        query = query.where(SafetyReport.date >= start_date)
    if end_date:
        query = query.where(SafetyReport.date <= end_date)

    reports = db.scalars(query).all()
    dto_list: List[AnalyticsReportDTO] = []

    for report in reports:
        # Fetch latest AI analysis
        ai_record = db.scalars(
            select(AIAnalysis)
            .where(AIAnalysis.report_id == report.id)
            .order_by(AIAnalysis.id.desc())
        ).first()

        # Fetch latest HSE review
        hse_record = db.scalars(
            select(HSEReview)
            .where(HSEReview.report_id == report.id)
            .order_by(HSEReview.id.desc())
        ).first()

        has_ai = ai_record is not None
        has_hse = hse_record is not None

        # Filter by SIF if requested
        if sif_only:
            is_sif = False
            if has_hse and hse_record.modified_classification is not None:
                is_sif = (hse_record.modified_classification == 1)
            elif has_ai:
                is_sif = (ai_record.classification == 1)
            if not is_sif:
                continue

        dto = AnalyticsReportDTO(
            report_id=report.id,
            report_number=report.report_number,
            created_by=report.created_by,
            report_type=report.report_type.value if hasattr(report.report_type, "value") else str(report.report_type),
            date=report.date or "",
            status=report.status.value if hasattr(report.status, "value") else str(report.status),
            site=report.site or MISSING_VALUE_PLACEHOLDER,
            refinery_unit=report.refinery_unit or MISSING_VALUE_PLACEHOLDER,
            location=report.location or MISSING_VALUE_PLACEHOLDER,
            equipment_id=report.equipment_id or MISSING_VALUE_PLACEHOLDER,
            work_type=report.work_type or MISSING_VALUE_PLACEHOLDER,
            activity=report.activity or MISSING_VALUE_PLACEHOLDER,
            department=report.department or MISSING_VALUE_PLACEHOLDER,
            description=report.description or "",
            action_status=report.action_status,
            ppe_noncompliance=bool(report.ppe_noncompliance),
            supervisor_negligence=bool(report.supervisor_negligence),
            maintenance_delay_or_issue=bool(report.maintenance_delay_or_issue),
            repeated_issue_ignored=bool(report.repeated_issue_ignored),
            previous_similar_reports=int(report.previous_similar_reports or 0),
            has_ai_analysis=has_ai,
            ai_model_version=ai_record.model_version if has_ai else None,
            ai_prediction=ai_record.prediction if has_ai else None,
            ai_classification=ai_record.classification if has_ai else None,
            ai_probability_or_score=ai_record.probability_or_score if has_ai else None,
            ai_hazards=_parse_json_list(ai_record.hazards_json) if has_ai else [],
            ai_barriers=_parse_json_list(ai_record.barrier_concerns_json) if has_ai else [],
            ai_lsrs=_parse_json_list(ai_record.life_saving_rules_json) if has_ai else [],
            has_hse_review=has_hse,
            hse_decision=hse_record.hse_decision.value if has_hse and hasattr(hse_record.hse_decision, "value") else (str(hse_record.hse_decision) if has_hse else None),
            hse_classification=hse_record.modified_classification if has_hse else None,
            hse_hazards=_parse_json_list(hse_record.modified_hazards_json) if has_hse else [],
            hse_barriers=_parse_json_list(hse_record.modified_barrier_concerns_json) if has_hse else [],
            hse_lsrs=_parse_json_list(hse_record.modified_lsr_json) if has_hse else [],
            reviewer_id=hse_record.reviewer_id if has_hse else None,
        )
        dto_list.append(dto)

    return dto_list
