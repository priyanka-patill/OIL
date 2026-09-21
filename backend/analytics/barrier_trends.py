"""
Barrier Trend Engine (Part 3C)

Calculates time-series trends for barrier occurrences and BDI scores
across Weekly, Monthly, and Quarterly time windows.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.barrier_normalization import (
    extract_normalized_barriers_from_dto,
    STANDARD_BARRIER_TAXONOMY
)


def _get_time_period_key(date_str: str, period: str) -> str:
    """Helper to convert YYYY-MM-DD date into period key."""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        if period == "week":
            year, week, _ = dt.isocalendar()
            return f"{year}-W{week:02d}"
        elif period == "quarter":
            quarter = (dt.month - 1) // 3 + 1
            return f"{dt.year}-Q{quarter}"
        else:  # month (default)
            return dt.strftime("%Y-%m")
    except ValueError:
        return "Unknown"


def calculate_barrier_trends(
    reports: List[AnalyticsReportDTO],
    period: str = "month",
    barrier_category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Computes time-series trend of barrier occurrences grouped by time period.
    """
    period = (period or "month").lower()
    if period not in ("week", "month", "quarter"):
        period = "month"

    # Aggregator: period_key -> { barrier_category -> occurrence_count, total_reports }
    period_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "period": "",
        "total_reports": 0,
        "barriers": defaultdict(int),
        "sif_reports": 0,
        "unresolved_reports": 0,
        "report_ids": set()
    })

    for r in reports:
        p_key = _get_time_period_key(r.date, period)
        if p_key == "Unknown":
            continue

        p_entry = period_data[p_key]
        p_entry["period"] = p_key

        if r.report_id not in p_entry["report_ids"]:
            p_entry["report_ids"].add(r.report_id)
            p_entry["total_reports"] += 1

            is_sif = False
            if r.has_hse_review and r.hse_classification is not None:
                is_sif = (r.hse_classification == 1)
            elif r.has_ai_analysis and r.ai_classification is not None:
                is_sif = (r.ai_classification == 1)
            if is_sif:
                p_entry["sif_reports"] += 1

            is_unresolved = False
            if r.action_status:
                is_unresolved = (r.action_status.upper() != "CLOSED")
            elif r.status in ("ACTION_REQUIRED", "SUBMITTED", "AI_ANALYZED", "HSE_REVIEW_PENDING"):
                is_unresolved = True
            if is_unresolved:
                p_entry["unresolved_reports"] += 1

        observations = extract_normalized_barriers_from_dto(r)
        for obs in observations:
            cat = obs.canonical_category
            if barrier_category is None or cat == barrier_category:
                p_entry["barriers"][cat] += 1

    sorted_periods = sorted(period_data.keys())
    trend_series: List[Dict[str, Any]] = []

    for p_key in sorted_periods:
        p_entry = period_data[p_key]
        barriers_dict = dict(p_entry["barriers"])
        
        trend_series.append({
            "period": p_key,
            "total_reports": p_entry["total_reports"],
            "sif_reports": p_entry["sif_reports"],
            "unresolved_reports": p_entry["unresolved_reports"],
            "barrier_occurrences": barriers_dict,
            "total_barrier_occurrences": sum(barriers_dict.values()),
        })

    return trend_series
