"""
Organizational Dimension Analytics Engine (Part 3B)

Calculates profile analytics across Sites, Activities, Equipment,
Locations, Departments, and Refinery Units.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from collections import Counter
from datetime import datetime, timezone

from backend.analytics.config import MISSING_VALUE_PLACEHOLDER
from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.density import calculate_sif_density, get_data_sufficiency_status
from backend.analytics.patterns import detect_recurring_patterns


@dataclass
class DimensionProfile:
    """Detailed profile metrics for a specific dimension value."""

    dimension: str
    dimension_value: str
    original_value: str
    total_reports: int
    eligible_analyzed_reports: int
    ai_sif_count: int
    ai_sif_density: Optional[float]
    hse_validated_sif_count: int
    hse_validated_sif_density: Optional[float]
    data_sufficiency: str
    recurring_pattern_count: int
    common_activities: List[str]
    common_equipment: List[str]
    common_hazards: List[str]
    common_barriers: List[str]
    contributing_report_ids: List[int]
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def analyze_dimension(
    reports: List[AnalyticsReportDTO],
    dimension_name: str,
) -> List[DimensionProfile]:
    """
    Groups reports by a specified dimension (e.g., 'site', 'activity', 'equipment_id', 'location', 'department', 'refinery_unit')
    and returns analytical profiles sorted by total reports descending.
    """
    profiles: List[DimensionProfile] = []
    if not reports:
        return profiles

    # Group reports by normalized dimension value
    grouped: Dict[str, List[AnalyticsReportDTO]] = {}
    original_value_map: Dict[str, str] = {}

    for r in reports:
        norm_val = r.normalized.get(dimension_name, MISSING_VALUE_PLACEHOLDER)
        raw_val = getattr(r, dimension_name, MISSING_VALUE_PLACEHOLDER) or MISSING_VALUE_PLACEHOLDER
        
        grouped.setdefault(norm_val, []).append(r)
        if norm_val not in original_value_map or (original_value_map[norm_val] == MISSING_VALUE_PLACEHOLDER and raw_val != MISSING_VALUE_PLACEHOLDER):
            original_value_map[norm_val] = str(raw_val).strip()

    # Pre-detect recurring patterns for co-occurrence linking
    patterns = detect_recurring_patterns(reports, min_support=2)
    calc_now = datetime.now(timezone.utc).isoformat()

    for norm_val, bucket in grouped.items():
        density_res = calculate_sif_density(bucket)

        # Collect top co-occurring activities, equipment, hazards, barriers
        act_counts = Counter()
        eq_counts = Counter()
        hazard_counts = Counter()
        barrier_counts = Counter()

        for r in bucket:
            if r.activity and r.activity != MISSING_VALUE_PLACEHOLDER:
                act_counts[r.activity.strip()] += 1
            if r.equipment_id and r.equipment_id != MISSING_VALUE_PLACEHOLDER:
                eq_counts[r.equipment_id.strip()] += 1
            for h in r.get_effective_hazards():
                if h:
                    hazard_counts[h] += 1
            for b in r.get_effective_barriers():
                if b:
                    barrier_counts[b] += 1

        top_acts = [a for a, _ in act_counts.most_common(3)]
        top_eqs = [e for e, _ in eq_counts.most_common(3)]
        top_hazards = [h for h, _ in hazard_counts.most_common(3)]
        top_barriers = [b for b, _ in barrier_counts.most_common(3)]

        # Count patterns matching this dimension value
        bucket_report_ids = set(r.report_id for r in bucket)
        matched_patterns = [
            p for p in patterns 
            if any(rid in bucket_report_ids for rid in p.report_ids)
        ]

        prof = DimensionProfile(
            dimension=dimension_name,
            dimension_value=norm_val,
            original_value=original_value_map.get(norm_val, norm_val),
            total_reports=density_res.total_reports,
            eligible_analyzed_reports=density_res.eligible_analyzed_reports,
            ai_sif_count=density_res.ai_sif_potential_count,
            ai_sif_density=density_res.ai_sif_precursor_density,
            hse_validated_sif_count=density_res.hse_sif_validated_count,
            hse_validated_sif_density=density_res.hse_sif_precursor_density,
            data_sufficiency=density_res.data_sufficiency,
            recurring_pattern_count=len(matched_patterns),
            common_activities=top_acts,
            common_equipment=top_eqs,
            common_hazards=top_hazards,
            common_barriers=top_barriers,
            contributing_report_ids=sorted(list(bucket_report_ids)),
            calculated_at=calc_now,
        )

        profiles.append(prof)

    # Sort profiles by total reports descending
    profiles.sort(key=lambda p: (p.total_reports, p.ai_sif_count), reverse=True)
    return profiles
