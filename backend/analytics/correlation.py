"""
Cross-Report Correlation Layer (Part 3A)

Calculates transparent, non-causal recurring dimension combinations across
equipment, activity, location, hazards, barriers, and precursor flags.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any, Optional
from collections import Counter

from backend.analytics.config import MISSING_VALUE_PLACEHOLDER
from backend.analytics.data_access import AnalyticsReportDTO


@dataclass
class CorrelationItem:
    """Representation of a specific correlated dimension combination."""
    correlation_type: str  # SINGLE_DIMENSION, PAIRWISE, MULTI_FACTOR, LOCATION_ACTIVITY
    dimensions: Dict[str, str]
    occurrence_count: int
    report_ids: List[int]
    sif_ai_count: int
    sif_hse_count: int


@dataclass
class CorrelationResult:
    """Aggregated correlation findings across all reports."""
    total_reports_analyzed: int
    single_dimension_correlations: List[CorrelationItem]
    pairwise_correlations: List[CorrelationItem]
    multi_factor_correlations: List[CorrelationItem]


def calculate_correlations(
    reports: List[AnalyticsReportDTO],
    min_count: int = 1,
) -> CorrelationResult:
    """
    Computes single, pairwise, and multi-factor recurrences across the dataset.
    Excludes trivial 'UNKNOWN' combinations from multi-factor patterns.
    """
    total_reports = len(reports)
    if total_reports == 0:
        return CorrelationResult(
            total_reports_analyzed=0,
            single_dimension_correlations=[],
            pairwise_correlations=[],
            multi_factor_correlations=[],
        )

    # 1. Single Dimension Frequencies
    single_buckets: Dict[Tuple[str, str], List[AnalyticsReportDTO]] = {}
    
    # 2. Pairwise Frequencies
    pairwise_buckets: Dict[Tuple[Tuple[str, str], Tuple[str, str]], List[AnalyticsReportDTO]] = {}

    # 3. Multi-Factor Frequencies (Equipment + Activity + Barrier/Hazard/Precursor)
    multi_buckets: Dict[Tuple[Tuple[str, str], ...], List[AnalyticsReportDTO]] = {}

    for r in reports:
        norm = r.normalized

        # Extract primary values (skip UNKNOWN for pattern grouping unless meaningful)
        eq = norm.get("equipment_id", MISSING_VALUE_PLACEHOLDER)
        act = norm.get("activity", MISSING_VALUE_PLACEHOLDER)
        loc = norm.get("location", MISSING_VALUE_PLACEHOLDER)
        unit = norm.get("refinery_unit", MISSING_VALUE_PLACEHOLDER)
        dept = norm.get("department", MISSING_VALUE_PLACEHOLDER)
        work = norm.get("work_type", MISSING_VALUE_PLACEHOLDER)
        site = norm.get("site", MISSING_VALUE_PLACEHOLDER)

        effective_barriers = norm.get("barriers", [])
        effective_hazards = norm.get("hazards", [])

        # Single dimension buckets
        for dim_key, dim_val in [
            ("equipment_id", eq),
            ("activity", act),
            ("location", loc),
            ("refinery_unit", unit),
            ("department", dept),
            ("work_type", work),
        ]:
            if dim_val and dim_val != MISSING_VALUE_PLACEHOLDER:
                single_buckets.setdefault((dim_key, dim_val), []).append(r)

        # Pairwise buckets
        pairs = []
        if eq != MISSING_VALUE_PLACEHOLDER and act != MISSING_VALUE_PLACEHOLDER:
            pairs.append((("equipment_id", eq), ("activity", act)))
        if act != MISSING_VALUE_PLACEHOLDER and loc != MISSING_VALUE_PLACEHOLDER:
            pairs.append((("activity", act), ("location", loc)))
        if unit != MISSING_VALUE_PLACEHOLDER and act != MISSING_VALUE_PLACEHOLDER:
            pairs.append((("refinery_unit", unit), ("activity", act)))
        if eq != MISSING_VALUE_PLACEHOLDER and loc != MISSING_VALUE_PLACEHOLDER:
            pairs.append((("equipment_id", eq), ("location", loc)))

        for b in effective_barriers:
            if b and b != MISSING_VALUE_PLACEHOLDER:
                if act != MISSING_VALUE_PLACEHOLDER:
                    pairs.append((("activity", act), ("barrier", b)))
                if eq != MISSING_VALUE_PLACEHOLDER:
                    pairs.append((("equipment_id", eq), ("barrier", b)))

        for p in pairs:
            # Sort pair tuple to prevent order duplication
            sorted_pair = tuple(sorted(p, key=lambda x: x[0]))
            pairwise_buckets.setdefault(sorted_pair, []).append(r)

        # Multi-factor buckets (e.g. Equipment + Activity + Barrier)
        if eq != MISSING_VALUE_PLACEHOLDER and act != MISSING_VALUE_PLACEHOLDER:
            for b in effective_barriers:
                if b and b != MISSING_VALUE_PLACEHOLDER:
                    tup = tuple(sorted([
                        ("equipment_id", eq),
                        ("activity", act),
                        ("barrier", b),
                    ], key=lambda x: x[0]))
                    multi_buckets.setdefault(tup, []).append(r)

            for h in effective_hazards:
                if h and h != MISSING_VALUE_PLACEHOLDER:
                    tup = tuple(sorted([
                        ("equipment_id", eq),
                        ("activity", act),
                        ("hazard", h),
                    ], key=lambda x: x[0]))
                    multi_buckets.setdefault(tup, []).append(r)

            # Precursor multi-factors
            if r.maintenance_delay_or_issue:
                tup = tuple(sorted([
                    ("equipment_id", eq),
                    ("activity", act),
                    ("precursor", "maintenance_delay_or_issue"),
                ], key=lambda x: x[0]))
                multi_buckets.setdefault(tup, []).append(r)

    # Helper function to convert bucket to CorrelationItem
    def _create_item(corr_type: str, dim_tuple: Tuple[Tuple[str, str], ...], bucket: List[AnalyticsReportDTO]) -> CorrelationItem:
        dims = dict(dim_tuple)
        r_ids = [r.report_id for r in bucket]
        sif_ai = sum(1 for r in bucket if r.is_sif_ai())
        sif_hse = sum(1 for r in bucket if r.is_sif_hse() is True)
        return CorrelationItem(
            correlation_type=corr_type,
            dimensions=dims,
            occurrence_count=len(bucket),
            report_ids=r_ids,
            sif_ai_count=sif_ai,
            sif_hse_count=sif_hse,
        )

    single_items = [
        _create_item("SINGLE_DIMENSION", (k,), v)
        for k, v in single_buckets.items()
        if len(v) >= min_count
    ]
    single_items.sort(key=lambda x: x.occurrence_count, reverse=True)

    pairwise_items = [
        _create_item("PAIRWISE", k, v)
        for k, v in pairwise_buckets.items()
        if len(v) >= min_count
    ]
    pairwise_items.sort(key=lambda x: x.occurrence_count, reverse=True)

    multi_items = [
        _create_item("MULTI_FACTOR", k, v)
        for k, v in multi_buckets.items()
        if len(v) >= min_count
    ]
    multi_items.sort(key=lambda x: x.occurrence_count, reverse=True)

    return CorrelationResult(
        total_reports_analyzed=total_reports,
        single_dimension_correlations=single_items,
        pairwise_correlations=pairwise_items,
        multi_factor_correlations=multi_items,
    )
