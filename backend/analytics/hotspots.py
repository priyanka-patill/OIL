"""
Hotspot & Concentration Analytics Engine (Part 3B)

Identifies multi-dimensional concentrations of safety reports and SIF precursors
with transparent evidence reasoning, small-sample protection, and non-punitive terminology.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from backend.analytics.config import MISSING_VALUE_PLACEHOLDER
from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.density import calculate_sif_density
from backend.analytics.dimensions import analyze_dimension, DimensionProfile


@dataclass
class HotspotItem:
    """Representation of an observed analytical hotspot/concentration."""

    hotspot_id: str
    dimension: str
    dimension_value: str
    original_value: str
    report_count: int
    eligible_analyzed_reports: int
    ai_sif_count: int
    ai_sif_precursor_density: Optional[float]
    hse_validated_sif_count: int
    data_sufficiency: str
    concentration_score: float
    evidence_reason: str
    common_activities: List[str]
    common_equipment: List[str]
    common_hazards: List[str]
    common_barriers: List[str]
    contributing_report_ids: List[int]


@dataclass
class HotspotResult:
    """Aggregated response containing detected hotspots across dimensions."""

    total_reports_analyzed: int
    hotspots_count: int
    hotspots: List[HotspotItem]
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def detect_hotspots(
    reports: List[AnalyticsReportDTO],
    dimensions_to_scan: Optional[List[str]] = None,
    max_results: int = 10,
) -> HotspotResult:
    """
    Scans organizational dimensions (site, location, equipment_id, activity, department, refinery_unit)
    and identifies analytical hotspots based on volume, SIF precursor density, and recurrence.
    Uses non-punitive, evidence-backed terminology.
    """
    if not reports:
        return HotspotResult(
            total_reports_analyzed=0,
            hotspots_count=0,
            hotspots=[],
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )

    if not dimensions_to_scan:
        dimensions_to_scan = ["equipment_id", "activity", "location", "site", "department", "refinery_unit"]

    candidate_profiles: List[DimensionProfile] = []

    for dim in dimensions_to_scan:
        profiles = analyze_dimension(reports, dim)
        for p in profiles:
            # Exclude UNKNOWN placeholders from hotspot rankings
            if p.dimension_value and p.dimension_value != MISSING_VALUE_PLACEHOLDER:
                candidate_profiles.append(p)

    hotspot_counter = 1
    hotspots: List[HotspotItem] = []

    for p in candidate_profiles:
        # Calculate transparent concentration score:
        # Volume weight (1.0 per report) + SIF Count weight (3.0 per SIF) + Recurrence weight (2.0 per pattern)
        volume_weight = float(p.total_reports) * 1.0
        sif_weight = float(p.ai_sif_count) * 3.0
        pattern_weight = float(p.recurring_pattern_count) * 2.0
        density_weight = (p.ai_sif_density or 0.0) * 10.0

        concentration_score = round(volume_weight + sif_weight + pattern_weight + density_weight, 2)

        # Build human-readable evidence reason
        reasons = [
            f"Observed {p.total_reports} total report(s)",
            f"{p.ai_sif_count} AI SIF-Potential precursor(s)",
        ]
        if p.ai_sif_density is not None:
            reasons.append(f"SIF Precursor Density: {p.ai_sif_density:.1%}")
        if p.recurring_pattern_count > 0:
            reasons.append(f"{p.recurring_pattern_count} recurring pattern(s)")

        evidence = f"Observed Concentration in {p.dimension.replace('_', ' ').title()} '{p.original_value}': " + "; ".join(reasons) + "."

        item = HotspotItem(
            hotspot_id=f"HOT-{hotspot_counter:03d}",
            dimension=p.dimension,
            dimension_value=p.dimension_value,
            original_value=p.original_value,
            report_count=p.total_reports,
            eligible_analyzed_reports=p.eligible_analyzed_reports,
            ai_sif_count=p.ai_sif_count,
            ai_sif_precursor_density=p.ai_sif_density,
            hse_validated_sif_count=p.hse_validated_sif_count,
            data_sufficiency=p.data_sufficiency,
            concentration_score=concentration_score,
            evidence_reason=evidence,
            common_activities=p.common_activities,
            common_equipment=p.common_equipment,
            common_hazards=p.common_hazards,
            common_barriers=p.common_barriers,
            contributing_report_ids=p.contributing_report_ids,
        )

        hotspots.append(item)
        hotspot_counter += 1

    # Sort hotspots by concentration score descending
    hotspots.sort(key=lambda h: h.concentration_score, reverse=True)

    top_hotspots = hotspots[:max_results]

    return HotspotResult(
        total_reports_analyzed=len(reports),
        hotspots_count=len(top_hotspots),
        hotspots=top_hotspots,
        calculated_at=datetime.now(timezone.utc).isoformat(),
    )
