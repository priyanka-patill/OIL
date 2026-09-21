"""
Historical Cross-Report Similarity Engine (SIM_EVAL_v1)

Calculates previous similar reports count and matches using multi-field
structured overlap and TF-IDF text similarity over persisted database records.
Enforces RBAC authorization filtering and self-match exclusion.
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.database.models import SafetyReport, User
from backend.analytics.data_access import get_analytics_reports
from backend.analytics.normalization import normalize_report
from backend.analytics.related_reports import find_related_reports

logger = logging.getLogger("backend.services.similarity_service")

SIMILARITY_METHODOLOGY_VERSION = "SIM_EVAL_v1"


def calculate_report_similarity(
    db: Session,
    report: SafetyReport,
    user: User,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Computes system-calculated historical cross-report similarity for a target SafetyReport.
    
    Rules & Protection:
    - Excludes self (target_report_id).
    - Enforces RBAC user authorization data scope.
    - Uses multi-field structured overlap + TF-IDF description similarity.
    - Excludes source_sheet and dataset tab names.
    - Returns 0 if zero historical reports exist.
    """
    # 1. Fetch authorized persisted safety reports from database
    dto_reports = get_analytics_reports(db, user=user)

    # If target report is newly created or missing from dto_reports, convert target report to DTO
    target_in_dtos = any(r.report_id == report.id for r in dto_reports)
    if not target_in_dtos:
        from backend.analytics.data_access import AnalyticsReportDTO, MISSING_VALUE_PLACEHOLDER
        target_dto = AnalyticsReportDTO(
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
            previous_similar_reports=0
        )
        dto_reports.append(target_dto)

    # 2. Normalize report DTOs
    normalized_dtos = [normalize_report(dto) for dto in dto_reports]

    # 3. Find candidates (excluding self)
    candidates = [r for r in normalized_dtos if r.report_id != report.id]
    if not candidates:
        logger.info(f"No historical reports found for comparison against Report #{report.id}.")
        return {
            "previous_similar_reports_count": 0,
            "similarity_status": "NO_HISTORICAL_REPORTS",
            "similar_reports": [],
            "message": "No historical reports available for comparison.",
            "methodology_version": SIMILARITY_METHODOLOGY_VERSION
        }

    # 4. Run multi-field & TF-IDF similarity calculation
    related = find_related_reports(
        target_report_id=report.id,
        reports=normalized_dtos,
        max_results=max_results
    )

    # Filter out weak or irrelevant matches
    valid_matches: List[Dict[str, Any]] = []
    for rel in related:
        valid_matches.append({
            "report_id": rel.related_report_id,
            "report_number": rel.related_report_number,
            "similarity_score": rel.similarity_score,
            "date": rel.date,
            "site": rel.site,
            "refinery_unit": rel.refinery_unit,
            "equipment_id": rel.equipment_id,
            "activity": rel.activity,
            "description_snippet": rel.description_snippet,
            "evidence_explanation": rel.evidence_explanation
        })

    count = len(valid_matches)
    logger.info(f"Report #{report.id} similarity analysis complete: {count} similar reports matched.")

    return {
        "previous_similar_reports_count": count,
        "similarity_status": "CALCULATED",
        "similar_reports": valid_matches,
        "message": f"{count} similar historical report(s) identified." if count > 0 else "No similar historical reports found.",
        "methodology_version": SIMILARITY_METHODOLOGY_VERSION
    }
