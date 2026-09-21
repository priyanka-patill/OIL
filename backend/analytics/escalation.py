"""
Risk Escalation Engine (Part 3D)

Evaluates 6 evidence-based risk escalation indicators across organizational entities
(Equipment, Site, Activity, Department, Location, Barrier).
Enforces strict small-sample protection (n >= 3 unique reports required).
"""

from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from datetime import datetime, timezone

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.barrier_normalization import extract_normalized_barriers_from_dto
from backend.analytics.barrier_trends import _get_time_period_key
from backend.analytics.config import MISSING_VALUE_PLACEHOLDER

ESCALATION_MIN_REPORTS = 3
ESCALATION_METHODOLOGY_VERSION = "RE_v1"

ESCALATION_LIMITATIONS = [
    "Escalation indicators describe observed historical precursor patterns, not future accident probabilities.",
    "Indicators depend on reporting thoroughness and corrective action tracking coverage."
]


def evaluate_entity_risk_escalation(
    entity_type: str,
    entity_id: str,
    reports: List[AnalyticsReportDTO]
) -> Dict[str, Any]:
    """
    Evaluates 6 risk escalation evidence indicators for a specific entity.
    Returns status INSUFFICIENT_DATA if unique reports < ESCALATION_MIN_REPORTS (3).
    """
    entity_type_lower = entity_type.lower().strip()
    entity_id_lower = entity_id.lower().strip()

    # Filter reports associated with target entity
    matching_reports: List[AnalyticsReportDTO] = []
    for r in reports:
        val = ""
        if entity_type_lower == "equipment_id" or entity_type_lower == "equipment":
            val = r.normalized.get("equipment_id", r.equipment_id or "")
        elif entity_type_lower == "site":
            val = r.normalized.get("site", r.site or "")
        elif entity_type_lower == "activity":
            val = r.normalized.get("activity", r.activity or "")
        elif entity_type_lower == "department":
            val = r.normalized.get("department", r.department or "")
        elif entity_type_lower == "location":
            val = r.normalized.get("location", r.location or "")
        elif entity_type_lower == "refinery_unit":
            val = r.normalized.get("refinery_unit", r.refinery_unit or "")
        elif entity_type_lower == "barrier":
            observations = extract_normalized_barriers_from_dto(r)
            if any(o.canonical_category.lower() == entity_id_lower for o in observations):
                matching_reports.append(r)
            continue

        if val and val.lower().strip() == entity_id_lower and val != MISSING_VALUE_PLACEHOLDER:
            matching_reports.append(r)

    n_reports = len(matching_reports)
    contributing_ids = [r.report_id for r in matching_reports]

    # 1. Sample Sufficiency Check
    if n_reports < ESCALATION_MIN_REPORTS:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "INSUFFICIENT_DATA",
            "message": f"Insufficient data (minimum {ESCALATION_MIN_REPORTS} unique reports required for escalation evaluation)",
            "methodology_version": ESCALATION_METHODOLOGY_VERSION,
            "sample": {
                "total_reports": n_reports,
                "analyzed_reports": len([r for r in matching_reports if r.has_ai_analysis or r.has_hse_review]),
                "sif_potential_count": 0
            },
            "indicators": [],
            "contributing_report_ids": contributing_ids,
            "limitations": ESCALATION_LIMITATIONS,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }

    # 2. Evaluate Indicators
    sif_count = 0
    unresolved_count = 0
    barrier_counts: Dict[str, int] = defaultdict(int)
    period_months: Set[str] = set()

    for r in matching_reports:
        # SIF check
        is_sif = False
        if r.has_hse_review and r.hse_classification is not None:
            is_sif = (r.hse_classification == 1)
        elif r.has_ai_analysis and r.ai_classification is not None:
            is_sif = (r.ai_classification == 1)
        if is_sif:
            sif_count += 1

        # Unresolved check
        is_unresolved = False
        if r.action_status:
            is_unresolved = (r.action_status.upper() != "CLOSED")
        elif r.status in ("ACTION_REQUIRED", "SUBMITTED", "AI_ANALYZED", "HSE_REVIEW_PENDING"):
            is_unresolved = True
        if is_unresolved:
            unresolved_count += 1

        # Barrier concerns
        observations = extract_normalized_barriers_from_dto(r)
        for obs in observations:
            barrier_counts[obs.canonical_category] += 1

        # Period tracking
        p_key = _get_time_period_key(r.date, "month")
        if p_key != "Unknown":
            period_months.add(p_key)

    # Indicator 1: REPEATED_REPORTS
    ind_repeated = {
        "type": "REPEATED_REPORTS",
        "status": "PRESENT" if n_reports >= 3 else "ABSENT",
        "evidence": f"{n_reports} unique safety reports"
    }

    # Indicator 2: UNRESOLVED_ISSUES
    ind_unresolved = {
        "type": "UNRESOLVED_ISSUES",
        "status": "PRESENT" if unresolved_count >= 1 else "ABSENT",
        "evidence": f"{unresolved_count} unresolved reports"
    }

    # Indicator 3: REPEATED_BARRIER
    top_barrier = None
    max_barrier_cnt = 0
    for b_cat, b_cnt in barrier_counts.items():
        if b_cnt > max_barrier_cnt:
            max_barrier_cnt = b_cnt
            top_barrier = b_cat

    ind_barrier = {
        "type": "REPEATED_BARRIER",
        "status": "PRESENT" if max_barrier_cnt >= 2 else "ABSENT",
        "evidence": f"Recurring concern: '{top_barrier}' in {max_barrier_cnt} reports" if top_barrier else "No recurring barrier"
    }

    # Indicator 4: INCREASING_RECURRENCE
    sorted_months = sorted(list(period_months))
    trend_dir = "Stable"
    if len(sorted_months) >= 2:
        first_half_cnt = len([r for r in matching_reports if _get_time_period_key(r.date, "month") == sorted_months[0]])
        last_half_cnt = len([r for r in matching_reports if _get_time_period_key(r.date, "month") == sorted_months[-1]])
        if last_half_cnt > first_half_cnt:
            trend_dir = "Increasing"
        elif last_half_cnt < first_half_cnt:
            trend_dir = "Decreasing"

    ind_trend = {
        "type": "INCREASING_RECURRENCE",
        "status": "PRESENT" if trend_dir == "Increasing" else "ABSENT",
        "evidence": f"Occurrence trend is {trend_dir} across {len(sorted_months)} months"
    }

    # Indicator 5: SIF_ASSOCIATION
    ind_sif = {
        "type": "SIF_ASSOCIATION",
        "status": "PRESENT" if sif_count >= 1 else "ABSENT",
        "evidence": f"{sif_count} SIF-Potential precursor reports"
    }

    # Indicator 6: PERSISTENT_EXPOSURE
    ind_persistence = {
        "type": "PERSISTENT_EXPOSURE",
        "status": "PRESENT" if len(sorted_months) >= 2 else "ABSENT",
        "evidence": f"Observed across {len(sorted_months)} distinct calendar months"
    }

    indicators = [ind_repeated, ind_unresolved, ind_barrier, ind_trend, ind_sif, ind_persistence]
    active_indicators = [i for i in indicators if i["status"] == "PRESENT"]
    active_cnt = len(active_indicators)

    # Determine overall escalation status
    if active_cnt >= 3:
        overall_status = "MULTIPLE_ESCALATION_INDICATORS_PRESENT"
    elif active_cnt >= 1:
        overall_status = "POTENTIAL_ESCALATION_INDICATORS_PRESENT"
    else:
        overall_status = "NO_ESCALATION"

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": overall_status,
        "methodology_version": ESCALATION_METHODOLOGY_VERSION,
        "sample": {
            "total_reports": n_reports,
            "analyzed_reports": len([r for r in matching_reports if r.has_ai_analysis or r.has_hse_review]),
            "sif_potential_count": sif_count,
            "unresolved_count": unresolved_count
        },
        "active_indicators_count": active_cnt,
        "indicators": indicators,
        "contributing_report_ids": contributing_ids,
        "limitations": ESCALATION_LIMITATIONS,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }


def detect_all_escalations(
    reports: List[AnalyticsReportDTO],
    dimension_name: str = "equipment_id"
) -> List[Dict[str, Any]]:
    """
    Evaluates risk escalation across all distinct entities for a given dimension.
    """
    dimension_lower = dimension_name.lower().strip()
    entity_ids: Set[str] = set()

    for r in reports:
        val = r.normalized.get(dimension_lower, getattr(r, dimension_lower, ""))
        if val and val != MISSING_VALUE_PLACEHOLDER:
            entity_ids.add(val)

    escalations: List[Dict[str, Any]] = []
    for eid in sorted(entity_ids):
        res = evaluate_entity_risk_escalation(dimension_name, eid, reports)
        if res["status"] != "INSUFFICIENT_DATA":
            escalations.append(res)

    return escalations
