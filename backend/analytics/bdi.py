"""
Barrier Degradation Index (BDI) Calculation Engine (Part 3C)

Calculates the Barrier Degradation Index (BDI_v1) as an evidence-backed,
descriptive indicator of safety barrier weaknesses.
Enforces strict small-sample protection (n >= 3 unique reports required).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.barrier_normalization import STANDARD_BARRIER_TAXONOMY
from backend.analytics.barrier_analytics import calculate_barrier_frequency, get_barrier_detail_profile
from backend.analytics.barrier_trends import calculate_barrier_trends

# Configuration Thresholds
BDI_MIN_REPORTS = 3
BDI_METHODOLOGY_VERSION = "BDI_v1"

BDI_LIMITATIONS = [
    "BDI is a descriptive indicator of historical reporting patterns, not a predictive safety model.",
    "BDI does not predict future accidents, fatalities, or SIF events.",
    "Barrier observations depend on reporting thoroughness and HSE review coverage."
]


def _compute_trend_direction(trend_series: List[Dict[str, Any]], barrier_category: str) -> str:
    """Calculates linear trend direction across active time windows."""
    if len(trend_series) < 2:
        return "Stable"

    counts = [point["barrier_occurrences"].get(barrier_category, 0) for point in trend_series]
    first_half = counts[:len(counts)//2]
    second_half = counts[len(counts)//2:]

    avg_first = sum(first_half) / max(1, len(first_half))
    avg_second = sum(second_half) / max(1, len(second_half))

    if avg_second > avg_first + 0.5:
        return "Increasing"
    elif avg_second < avg_first - 0.5:
        return "Decreasing"
    return "Stable"


def calculate_bdi_for_barrier(
    barrier_category: str,
    reports: List[AnalyticsReportDTO],
    trend_period: str = "month"
) -> Dict[str, Any]:
    """
    Computes BDI_v1 score and evidence payload for a single barrier category.
    Returns status INSUFFICIENT_DATA and bdi = None if unique_reports < BDI_MIN_REPORTS (3).
    """
    profile = get_barrier_detail_profile(barrier_category, reports)
    n_reports = profile["unique_reports"]

    # Trend calculation
    trends = calculate_barrier_trends(reports, period=trend_period, barrier_category=barrier_category)
    active_windows = len([t for t in trends if t["barrier_occurrences"].get(barrier_category, 0) > 0])
    total_windows = max(1, len(trends))
    trend_dir = _compute_trend_direction(trends, barrier_category)

    # 1. Sample Sufficiency Check
    if n_reports < BDI_MIN_REPORTS:
        return {
            "barrier_category": barrier_category,
            "bdi": None,
            "status": "INSUFFICIENT_DATA",
            "message": f"Insufficient data (minimum {BDI_MIN_REPORTS} unique reports required for BDI score)",
            "methodology_version": BDI_METHODOLOGY_VERSION,
            "evidence": {
                "total_occurrences": profile["occurrences"],
                "unique_reports": n_reports,
                "unique_sites": len(profile["by_site"]),
                "unique_activities": len(profile["by_activity"]),
                "unresolved_count": profile["unresolved_count"],
                "sif_potential_count": profile["sif_potential_association"],
                "persistence_windows": f"{active_windows} of {total_windows} {trend_period}s",
                "trend_direction": trend_dir,
                "contributing_report_ids": profile["contributing_report_ids"]
            },
            "component_scores": None,
            "limitations": BDI_LIMITATIONS,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }

    # Determine status level
    status = "SUFFICIENT_DATA" if n_reports >= 5 else "LIMITED_DATA"

    # 2. Component Scoring (Normalized 0-100)
    # Recurrence Score (R): Scaled relative to 10 reports
    score_R = min(100.0, (n_reports / 10.0) * 100.0)

    # Persistence Score (P): Active windows ratio
    score_P = (active_windows / float(total_windows)) * 100.0

    # Unresolved Status Score (U): Ratio of unresolved reports
    score_U = (profile["unresolved_count"] / float(n_reports)) * 100.0

    # SIF-Potential Association Score (S): Ratio of SIF reports
    score_S = (profile["sif_potential_association"] / float(n_reports)) * 100.0

    # Trend Adjustment (T)
    trend_adj = 0.0
    if trend_dir == "Increasing":
        trend_adj = 10.0
    elif trend_dir == "Decreasing":
        trend_adj = -10.0

    # 3. Composite Formula
    raw_bdi = (0.30 * score_R) + (0.25 * score_P) + (0.25 * score_U) + (0.20 * score_S) + trend_adj
    final_bdi = max(0, min(100, int(round(raw_bdi))))

    return {
        "barrier_category": barrier_category,
        "bdi": final_bdi,
        "status": status,
        "methodology_version": BDI_METHODOLOGY_VERSION,
        "evidence": {
            "total_occurrences": profile["occurrences"],
            "unique_reports": n_reports,
            "unique_sites": len(profile["by_site"]),
            "unique_activities": len(profile["by_activity"]),
            "unresolved_count": profile["unresolved_count"],
            "sif_potential_count": profile["sif_potential_association"],
            "persistence_windows": f"{active_windows} of {total_windows} {trend_period}s",
            "trend_direction": trend_dir,
            "contributing_report_ids": profile["contributing_report_ids"]
        },
        "component_scores": {
            "recurrence_score": round(score_R, 1),
            "persistence_score": round(score_P, 1),
            "unresolved_score": round(score_U, 1),
            "sif_association_score": round(score_S, 1),
            "trend_adjustment": trend_adj
        },
        "limitations": BDI_LIMITATIONS,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }


def calculate_all_bdi(
    reports: List[AnalyticsReportDTO],
    trend_period: str = "month"
) -> List[Dict[str, Any]]:
    """
    Computes BDI_v1 scores across all standard barrier categories.
    """
    bdi_list: List[Dict[str, Any]] = []
    for cat in STANDARD_BARRIER_TAXONOMY:
        item = calculate_bdi_for_barrier(cat, reports, trend_period=trend_period)
        bdi_list.append(item)
    return bdi_list
