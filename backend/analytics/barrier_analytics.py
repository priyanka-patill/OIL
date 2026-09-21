"""
Barrier Analytics Engine (Part 3C)

Calculates barrier frequencies, recurrence patterns, cross-dimensional associations,
and detailed barrier profiles from normalized AnalyticsReportDTO records.
"""

from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.barrier_normalization import (
    extract_normalized_barriers_from_dto,
    STANDARD_BARRIER_TAXONOMY,
    BARRIER_UNMAPPED
)
from backend.analytics.config import ANALYTICS_MIN_PATTERN_COUNT, MISSING_VALUE_PLACEHOLDER


def calculate_barrier_frequency(
    reports: List[AnalyticsReportDTO]
) -> List[Dict[str, Any]]:
    """
    Computes barrier frequency metrics across all reports.
    1 occurrence = 1 unique report containing that barrier category.
    """
    # Intermediate data accumulators per category
    data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "occurrences": 0,
        "unique_report_ids": set(),
        "sites": set(),
        "activities": set(),
        "departments": set(),
        "equipment": set(),
        "locations": set(),
        "sif_potential_count": 0,
        "unresolved_count": 0,
        "resolved_count": 0,
        "dates": [],
        "ai_count": 0,
        "hse_count": 0,
        "contributing_reports": []
    })

    for r in reports:
        # Determine SIF status
        is_sif = False
        if r.has_hse_review and r.hse_classification is not None:
            is_sif = (r.hse_classification == 1)
        elif r.has_ai_analysis and r.ai_classification is not None:
            is_sif = (r.ai_classification == 1)

        # Determine Unresolved/Action status
        is_unresolved = False
        if r.action_status:
            is_unresolved = (r.action_status.upper() != "CLOSED")
        elif r.status in ("ACTION_REQUIRED", "SUBMITTED", "AI_ANALYZED", "HSE_REVIEW_PENDING"):
            is_unresolved = True

        observations = extract_normalized_barriers_from_dto(r)
        for obs in observations:
            cat = obs.canonical_category
            acc = data[cat]

            if r.report_id not in acc["unique_report_ids"]:
                acc["unique_report_ids"].add(r.report_id)
                acc["occurrences"] += 1
                acc["contributing_reports"].append(r.report_id)

                if r.site and r.site != MISSING_VALUE_PLACEHOLDER:
                    acc["sites"].add(r.site)
                if r.activity and r.activity != MISSING_VALUE_PLACEHOLDER:
                    acc["activities"].add(r.activity)
                if r.department and r.department != MISSING_VALUE_PLACEHOLDER:
                    acc["departments"].add(r.department)
                if r.equipment_id and r.equipment_id != MISSING_VALUE_PLACEHOLDER:
                    acc["equipment"].add(r.equipment_id)
                if r.location and r.location != MISSING_VALUE_PLACEHOLDER:
                    acc["locations"].add(r.location)

                if is_sif:
                    acc["sif_potential_count"] += 1
                if is_unresolved:
                    acc["unresolved_count"] += 1
                else:
                    acc["resolved_count"] += 1

                if r.date:
                    acc["dates"].append(r.date)

                if obs.source_type == "HSE":
                    acc["hse_count"] += 1
                elif obs.source_type == "AI":
                    acc["ai_count"] += 1

    results: List[Dict[str, Any]] = []
    # Include standard taxonomy categories in deterministic order
    for cat in STANDARD_BARRIER_TAXONOMY:
        if cat in data:
            acc = data[cat]
            dates = sorted(acc["dates"])
            results.append({
                "barrier_category": cat,
                "occurrences": acc["occurrences"],
                "unique_reports": len(acc["unique_report_ids"]),
                "sites_count": len(acc["sites"]),
                "activities_count": len(acc["activities"]),
                "departments_count": len(acc["departments"]),
                "equipment_count": len(acc["equipment"]),
                "locations_count": len(acc["locations"]),
                "sif_potential_association": acc["sif_potential_count"],
                "unresolved_count": acc["unresolved_count"],
                "resolved_count": acc["resolved_count"],
                "first_observed_date": dates[0] if dates else None,
                "latest_observed_date": dates[-1] if dates else None,
                "ai_source_count": acc["ai_count"],
                "hse_source_count": acc["hse_count"],
                "contributing_report_ids": acc["contributing_reports"],
            })

    return results


def extract_barrier_recurrence(
    reports: List[AnalyticsReportDTO],
    min_support: int = ANALYTICS_MIN_PATTERN_COUNT
) -> List[Dict[str, Any]]:
    """
    Identifies recurring barrier concerns appearing in at least `min_support` unique reports.
    Returns recurrence patterns with multi-dimensional associations.
    """
    freq_list = calculate_barrier_frequency(reports)
    recurring: List[Dict[str, Any]] = []

    for item in freq_list:
        if item["unique_reports"] >= min_support:
            recurring.append({
                "barrier_category": item["barrier_category"],
                "unique_reports": item["unique_reports"],
                "occurrences": item["occurrences"],
                "sites_count": item["sites_count"],
                "activities_count": item["activities_count"],
                "sif_potential_association": item["sif_potential_association"],
                "unresolved_count": item["unresolved_count"],
                "first_observed_date": item["first_observed_date"],
                "latest_observed_date": item["latest_observed_date"],
                "is_recurring": True,
                "contributing_report_ids": item["contributing_report_ids"]
            })

    return recurring


def get_barrier_detail_profile(
    barrier_category: str,
    reports: List[AnalyticsReportDTO]
) -> Dict[str, Any]:
    """
    Constructs detailed analytical profile for a specific barrier category.
    """
    site_counts: Dict[str, int] = defaultdict(int)
    activity_counts: Dict[str, int] = defaultdict(int)
    dept_counts: Dict[str, int] = defaultdict(int)
    equipment_counts: Dict[str, int] = defaultdict(int)
    location_counts: Dict[str, int] = defaultdict(int)

    contributing_ids: List[int] = []
    sif_count = 0
    unresolved_count = 0
    resolved_count = 0
    dates: List[str] = []
    ai_count = 0
    hse_count = 0

    for r in reports:
        observations = extract_normalized_barriers_from_dto(r)
        matched_obs = [obs for obs in observations if obs.canonical_category == barrier_category]
        if matched_obs:
            contributing_ids.append(r.report_id)

            if r.site and r.site != MISSING_VALUE_PLACEHOLDER:
                site_counts[r.site] += 1
            if r.activity and r.activity != MISSING_VALUE_PLACEHOLDER:
                activity_counts[r.activity] += 1
            if r.department and r.department != MISSING_VALUE_PLACEHOLDER:
                dept_counts[r.department] += 1
            if r.equipment_id and r.equipment_id != MISSING_VALUE_PLACEHOLDER:
                equipment_counts[r.equipment_id] += 1
            if r.location and r.location != MISSING_VALUE_PLACEHOLDER:
                location_counts[r.location] += 1

            is_sif = False
            if r.has_hse_review and r.hse_classification is not None:
                is_sif = (r.hse_classification == 1)
            elif r.has_ai_analysis and r.ai_classification is not None:
                is_sif = (r.ai_classification == 1)
            if is_sif:
                sif_count += 1

            is_unresolved = False
            if r.action_status:
                is_unresolved = (r.action_status.upper() != "CLOSED")
            elif r.status in ("ACTION_REQUIRED", "SUBMITTED", "AI_ANALYZED", "HSE_REVIEW_PENDING"):
                is_unresolved = True
            if is_unresolved:
                unresolved_count += 1
            else:
                resolved_count += 1

            if r.date:
                dates.append(r.date)

            for obs in matched_obs:
                if obs.source_type == "HSE":
                    hse_count += 1
                elif obs.source_type == "AI":
                    ai_count += 1

    sorted_dates = sorted(dates)

    return {
        "barrier_category": barrier_category,
        "occurrences": len(contributing_ids),
        "unique_reports": len(contributing_ids),
        "sif_potential_association": sif_count,
        "unresolved_count": unresolved_count,
        "resolved_count": resolved_count,
        "first_observed_date": sorted_dates[0] if sorted_dates else None,
        "latest_observed_date": sorted_dates[-1] if sorted_dates else None,
        "ai_source_count": ai_count,
        "hse_source_count": hse_count,
        "by_site": dict(site_counts),
        "by_activity": dict(activity_counts),
        "by_department": dict(dept_counts),
        "by_equipment": dict(equipment_counts),
        "by_location": dict(location_counts),
        "contributing_report_ids": contributing_ids
    }
