"""
Recurring Pattern Detection Layer (Part 3A)

Aggregates correlated combinations, enforcing minimum pattern support thresholds
and building traceable RecurringPattern objects.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from collections import Counter

from backend.analytics.config import ANALYTICS_MIN_PATTERN_COUNT, ANALYTICS_VERSION, MISSING_VALUE_PLACEHOLDER
from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.correlation import calculate_correlations, CorrelationItem


@dataclass
class RecurringPattern:
    """Detailed representation of a detected recurring safety pattern."""

    pattern_id: str
    pattern_label: str
    dimensions: Dict[str, str]
    occurrence_count: int
    first_occurrence: str
    latest_occurrence: str
    report_ids: List[int]
    report_numbers: List[str]

    # AI SIF Counts
    ai_sif_count: int
    ai_non_sif_count: int

    # HSE Validated SIF Counts
    hse_validated_sif_count: int
    hse_validated_non_sif_count: int

    # Associated AI/HSE Safety Context
    common_hazards: List[str]
    common_barriers: List[str]
    common_lsrs: List[str]

    # Geographic & Operational Scope
    affected_sites: List[str]
    affected_activities: List[str]

    analytics_version: str = ANALYTICS_VERSION


def detect_recurring_patterns(
    reports: List[AnalyticsReportDTO],
    min_support: int = ANALYTICS_MIN_PATTERN_COUNT,
) -> List[RecurringPattern]:
    """
    Scans normalized AnalyticsReportDTO objects and returns recurring patterns meeting or exceeding `min_support`.
    Combinations with count < min_support are explicitly filtered out.
    """
    patterns: List[RecurringPattern] = []
    if not reports:
        return patterns

    # Calculate correlations
    corr_results = calculate_correlations(reports, min_count=min_support)

    # Combine pairwise and multi-factor correlations meeting threshold
    candidate_items: List[CorrelationItem] = (
        corr_results.multi_factor_correlations + corr_results.pairwise_correlations
    )

    # Also check high-frequency single dimension recurrences (e.g. equipment with >= min_support)
    for s in corr_results.single_dimension_correlations:
        if s.occurrence_count >= min_support:
            candidate_items.append(s)

    # Map report_id -> AnalyticsReportDTO for fast lookup
    report_map = {r.report_id: r for r in reports}
    pattern_counter = 1

    seen_pattern_keys: Set[str] = set()

    for item in candidate_items:
        # Generate a unique key for deduplicating overlapping pattern items
        key_parts = sorted([f"{k}={v}" for k, v in item.dimensions.items()])
        pattern_key = "||".join(key_parts)
        if pattern_key in seen_pattern_keys:
            continue
        seen_pattern_keys.add(pattern_key)

        # Retrieve contributing reports
        contributing_reports = [report_map[rid] for rid in item.report_ids if rid in report_map]
        if not contributing_reports:
            continue

        # Collect dates
        dates = [r.date for r in contributing_reports if r.date]
        dates.sort()
        first_occ = dates[0] if dates else MISSING_VALUE_PLACEHOLDER
        latest_occ = dates[-1] if dates else MISSING_VALUE_PLACEHOLDER

        # Collect report numbers
        report_nums = [r.report_number for r in contributing_reports]

        # SIF Counts (Separate AI vs HSE)
        ai_sif = sum(1 for r in contributing_reports if r.is_sif_ai())
        ai_non_sif = sum(1 for r in contributing_reports if r.has_ai_analysis and not r.is_sif_ai())

        hse_sif = sum(1 for r in contributing_reports if r.is_sif_hse() is True)
        hse_non_sif = sum(1 for r in contributing_reports if r.is_sif_hse() is False)

        # Aggregate common hazards, barriers, LSRs, sites, and activities
        hazard_counts = Counter()
        barrier_counts = Counter()
        lsr_counts = Counter()
        sites_set = set()
        activities_set = set()

        for r in contributing_reports:
            if r.site and r.site != MISSING_VALUE_PLACEHOLDER:
                sites_set.add(r.site)
            if r.activity and r.activity != MISSING_VALUE_PLACEHOLDER:
                activities_set.add(r.activity)

            for h in r.get_effective_hazards():
                if h:
                    hazard_counts[h] += 1
            for b in r.get_effective_barriers():
                if b:
                    barrier_counts[b] += 1
            for l in r.get_effective_lsrs():
                if l:
                    lsr_counts[l] += 1

        top_hazards = [h for h, _ in hazard_counts.most_common(3)]
        top_barriers = [b for b, _ in barrier_counts.most_common(3)]
        top_lsrs = [l for l, _ in lsr_counts.most_common(3)]

        # Generate human-readable label
        label_parts = [f"{v.title()}" for k, v in item.dimensions.items()]
        pattern_label = " + ".join(label_parts)

        p = RecurringPattern(
            pattern_id=f"PAT-{pattern_counter:03d}",
            pattern_label=pattern_label,
            dimensions=item.dimensions,
            occurrence_count=len(contributing_reports),
            first_occurrence=first_occ,
            latest_occurrence=latest_occ,
            report_ids=item.report_ids,
            report_numbers=report_nums,
            ai_sif_count=ai_sif,
            ai_non_sif_count=ai_non_sif,
            hse_validated_sif_count=hse_sif,
            hse_validated_non_sif_count=hse_non_sif,
            common_hazards=top_hazards,
            common_barriers=top_barriers,
            common_lsrs=top_lsrs,
            affected_sites=sorted(list(sites_set)),
            affected_activities=sorted(list(activities_set)),
            analytics_version=ANALYTICS_VERSION,
        )

        patterns.append(p)
        pattern_counter += 1

    return patterns
