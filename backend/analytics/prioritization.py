"""
Analytical Prioritization Engine (Part 3D)

Assigns transparent, evidence-based Analytical Priority Tiers (PRI_v1) to help HSE users
identify entities warranting further review, integrating SIF density (Part 3B),
Barrier Degradation (Part 3C), and Potential Escalation Indicators (Part 3D).
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.density import calculate_sif_density
from backend.analytics.barrier_analytics import get_barrier_detail_profile
from backend.analytics.bdi import calculate_bdi_for_barrier
from backend.analytics.escalation import evaluate_entity_risk_escalation
from backend.analytics.config import MISSING_VALUE_PLACEHOLDER

PRIORITY_METHODOLOGY_VERSION = "PRI_v1"
PRIORITY_MIN_REPORTS = 3

PRIORITY_LIMITATIONS = [
    "Analytical Priority is a descriptive evidence indicator intended to support HSE review.",
    "It is not a probability score for SIF, accident, or fatality events.",
    "Priority assignments depend on reporting thoroughness and corrective action tracking coverage."
]


def evaluate_analytical_priority(
    entity_type: str,
    entity_id: str,
    reports: List[AnalyticsReportDTO]
) -> Dict[str, Any]:
    """
    Computes Analytical Priority Tier (PRI_v1) and supporting evidence payload for an entity.
    Returns INSUFFICIENT_DATA if unique reports < PRIORITY_MIN_REPORTS (3).
    """
    # 1. Fetch Escalation Data
    esc_data = evaluate_entity_risk_escalation(entity_type, entity_id, reports)
    n_reports = esc_data["sample"]["total_reports"]

    if n_reports < PRIORITY_MIN_REPORTS:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "priority_tier": "INSUFFICIENT_DATA",
            "message": f"Insufficient data (minimum {PRIORITY_MIN_REPORTS} unique reports required for priority evaluation)",
            "methodology_version": PRIORITY_METHODOLOGY_VERSION,
            "sample": esc_data["sample"],
            "escalation_summary": None,
            "barrier_summary": None,
            "contributing_report_ids": esc_data["contributing_report_ids"],
            "limitations": PRIORITY_LIMITATIONS,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }

    # 2. Fetch Matching Reports & SIF Density
    entity_type_lower = entity_type.lower().strip()
    entity_id_lower = entity_id.lower().strip()

    matching_reports: List[AnalyticsReportDTO] = []
    for r in reports:
        val = r.normalized.get(entity_type_lower, getattr(r, entity_type_lower, ""))
        if val and str(val).lower().strip() == entity_id_lower and val != MISSING_VALUE_PLACEHOLDER:
            matching_reports.append(r)

    density_res = calculate_sif_density(matching_reports)
    sif_density_val = (
        density_res.hse_sif_precursor_density 
        if density_res.hse_sif_precursor_density is not None 
        else (density_res.ai_sif_precursor_density or 0.0)
    )

    # 3. Identify Top Barrier Concern & BDI
    top_barrier_name = None
    max_bdi_score = 0
    if matching_reports:
        # Check top barrier concern
        barrier_counts: Dict[str, int] = {}
        for r in matching_reports:
            for b in r.get_effective_barriers():
                barrier_counts[b] = barrier_counts.get(b, 0) + 1
        if barrier_counts:
            top_barrier_name = max(barrier_counts, key=barrier_counts.get)
            bdi_data = calculate_bdi_for_barrier(top_barrier_name, matching_reports)
            if bdi_data.get("bdi"):
                max_bdi_score = bdi_data["bdi"]

    active_cnt = esc_data["active_indicators_count"]

    # 4. Priority Tier Assignment Matrix
    if active_cnt >= 3 and (sif_density_val >= 0.20 or max_bdi_score >= 60):
        priority_tier = "HIGH_PRIORITY"
    elif active_cnt >= 1 or (sif_density_val >= 0.10 or max_bdi_score >= 40):
        priority_tier = "MEDIUM_PRIORITY"
    else:
        priority_tier = "LOW_PRIORITY"

    active_indicator_names = [i["type"] for i in esc_data["indicators"] if i["status"] == "PRESENT"]

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "priority_tier": priority_tier,
        "methodology_version": PRIORITY_METHODOLOGY_VERSION,
        "sample": {
            "total_reports": n_reports,
            "analyzed_reports": esc_data["sample"]["analyzed_reports"],
            "sif_potential_count": esc_data["sample"]["sif_potential_count"],
            "sif_precursor_density": round(sif_density_val, 4)
        },
        "escalation_summary": {
            "status": esc_data["status"],
            "active_indicators_count": active_cnt,
            "active_indicators": active_indicator_names
        },
        "barrier_summary": {
            "top_barrier": top_barrier_name,
            "bdi_score": max_bdi_score if max_bdi_score > 0 else None
        },
        "contributing_report_ids": esc_data["contributing_report_ids"],
        "limitations": PRIORITY_LIMITATIONS,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }


def calculate_all_priorities(
    reports: List[AnalyticsReportDTO],
    dimension_name: str = "equipment_id"
) -> List[Dict[str, Any]]:
    """
    Computes Analytical Priority Tiers across all distinct entities in a dimension.
    """
    dimension_lower = dimension_name.lower().strip()
    entity_ids: Set[str] = set()

    for r in reports:
        val = r.normalized.get(dimension_lower, getattr(r, dimension_lower, ""))
        if val and val != MISSING_VALUE_PLACEHOLDER:
            entity_ids.add(val)

    priorities: List[Dict[str, Any]] = []
    for eid in sorted(entity_ids):
        res = evaluate_analytical_priority(dimension_name, eid, reports)
        if res["priority_tier"] != "INSUFFICIENT_DATA":
            priorities.append(res)

    return priorities
