"""
SIF Precursor Density Engine (Part 3B)

Calculates descriptive SIF precursor density metrics with strict zero-denominator
handling, small-sample data sufficiency indicators, and calculation timestamps.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.analytics.data_access import AnalyticsReportDTO


@dataclass
class DensityResult:
    """Detailed summary of SIF precursor density calculations."""

    total_reports: int
    eligible_analyzed_reports: int
    un_analyzed_reports: int

    # AI SIF Metrics
    ai_sif_potential_count: int
    ai_non_sif_count: int
    ai_sif_precursor_density: Optional[float]  # Float 0.0 to 1.0 or None if 0 analyzed

    # HSE Validated SIF Metrics
    hse_reviewed_count: int
    hse_sif_validated_count: int
    hse_non_sif_validated_count: int
    hse_sif_precursor_density: Optional[float]  # Float 0.0 to 1.0 or None if 0 reviewed

    # Small-sample Protection & Data Sufficiency Status
    data_sufficiency: str  # SUFFICIENT, LIMITED, INSUFFICIENT, NOT_AVAILABLE
    sufficiency_reason: str

    # Traceability & Audit Metadata
    contributing_report_ids: List[int] = field(default_factory=list)
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def get_data_sufficiency_status(eligible_count: int) -> tuple[str, str]:
    """
    Evaluates small-sample protection status based on eligible analyzed count:
    - >= 10: SUFFICIENT
    - 3 - 9: LIMITED
    - 1 - 2: INSUFFICIENT
    - 0: NOT_AVAILABLE
    """
    if eligible_count >= 10:
        return (
            "SUFFICIENT",
            f"Population size ({eligible_count} analyzed reports) meets standard analytical confidence thresholds.",
        )
    elif eligible_count >= 3:
        return (
            "LIMITED",
            f"Limited population size ({eligible_count} analyzed reports). Interpret density metrics with caution.",
        )
    elif eligible_count >= 1:
        return (
            "INSUFFICIENT",
            f"Very small population size ({eligible_count} analyzed report(s)). Density metric is indicative only.",
        )
    else:
        return (
            "NOT_AVAILABLE",
            "Zero eligible analyzed reports available in the selected sample.",
        )


def calculate_sif_density(reports: List[AnalyticsReportDTO]) -> DensityResult:
    """
    Computes descriptive SIF precursor density metrics across a list of normalized reports.
    Formula: SIF Precursor Density = SIF-Potential Reports / Eligible Analyzed Reports.
    """
    total_count = len(reports)

    # Filter eligible analyzed reports (possessing AI analysis)
    eligible_reports = [r for r in reports if r.has_ai_analysis]
    eligible_count = len(eligible_reports)
    un_analyzed_count = total_count - eligible_count

    # AI SIF Counts
    ai_sif_count = sum(1 for r in eligible_reports if r.is_sif_ai())
    ai_non_sif_count = eligible_count - ai_sif_count

    ai_density: Optional[float] = None
    if eligible_count > 0:
        ai_density = round(ai_sif_count / eligible_count, 4)

    # HSE Validated Counts
    hse_reports = [r for r in reports if r.has_hse_review and r.hse_classification is not None]
    hse_count = len(hse_reports)
    hse_sif_count = sum(1 for r in hse_reports if r.is_sif_hse() is True)
    hse_non_sif_count = hse_count - hse_sif_count

    hse_density: Optional[float] = None
    if hse_count > 0:
        hse_density = round(hse_sif_count / hse_count, 4)

    sufficiency_status, sufficiency_reason = get_data_sufficiency_status(eligible_count)
    report_ids = [r.report_id for r in reports]

    return DensityResult(
        total_reports=total_count,
        eligible_analyzed_reports=eligible_count,
        un_analyzed_reports=un_analyzed_count,
        ai_sif_potential_count=ai_sif_count,
        ai_non_sif_count=ai_non_sif_count,
        ai_sif_precursor_density=ai_density,
        hse_reviewed_count=hse_count,
        hse_sif_validated_count=hse_sif_count,
        hse_non_sif_validated_count=hse_non_sif_count,
        hse_sif_precursor_density=hse_density,
        data_sufficiency=sufficiency_status,
        sufficiency_reason=sufficiency_reason,
        contributing_report_ids=report_ids,
        calculated_at=datetime.now(timezone.utc).isoformat(),
    )
