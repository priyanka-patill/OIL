"""
Automated Safety Risk Level Assessment Engine (RISK_EVAL_v1)

Calculates backend-authoritative Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
from empirical safety evidence: SIF ML prediction, hazard categories,
barrier concerns, precursor flags, and previous similar reports count.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("backend.services.risk_service")

RISK_METHODOLOGY_VERSION = "RISK_EVAL_v1"

HIGH_SEVERITY_HAZARD_KEYWORDS = [
    "confined space", "working at height", "hot work", "line of fire",
    "electrical", "pressure", "toxic", "flammable", "gas leak",
    "heavy lifting", "crane", "chemical"
]

CRITICAL_BARRIER_KEYWORDS = [
    "energy isolation", "permit", "gas testing", "confined space control",
    "fall protection", "lockout", "tagout"
]


def calculate_report_risk(
    report_dict: Dict[str, Any],
    ml_result: Dict[str, Any],
    hazards: List[str],
    barriers: List[str],
    previous_similar_reports_count: int = 0
) -> Dict[str, Any]:
    """
    Computes system-calculated Risk Level Assessment (RISK_EVAL_v1) for a safety report.
    
    Inputs:
    - report_dict: Dictionary of observation attributes & precursor flags.
    - ml_result: Part 1C ML prediction result (probability, prediction, classification).
    - hazards: List of identified hazard strings.
    - barriers: List of identified barrier concern strings.
    - previous_similar_reports_count: Calculated count of matching historical reports.
    
    Returns:
    - risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    - risk_explanation: List of bulleted evidence descriptions.
    - methodology_version: "RISK_EVAL_v1"
    """
    sif_prob = float(ml_result.get("probability", 0.0))
    is_sif_ml = (ml_result.get("classification") == 1) or (ml_result.get("prediction") == "SIF-Potential")

    # Detect high-severity hazards
    high_severity_hazards = []
    for h in hazards:
        h_lower = h.lower()
        if any(kw in h_lower for kw in HIGH_SEVERITY_HAZARD_KEYWORDS):
            high_severity_hazards.append(h)

    # Detect critical barrier concerns
    critical_barriers = []
    for b in barriers:
        b_lower = b.lower()
        if any(kw in b_lower for kw in CRITICAL_BARRIER_KEYWORDS):
            critical_barriers.append(b)

    # Flags
    ppe_flag = bool(report_dict.get("ppe_noncompliance", False))
    sup_flag = bool(report_dict.get("supervisor_negligence", False))
    maint_flag = bool(report_dict.get("maintenance_delay_or_issue", False))
    repeat_flag = bool(report_dict.get("repeated_issue_ignored", False))

    evidence_bullets: List[str] = []

    if is_sif_ml:
        evidence_bullets.append(f"SIF-Potential ML prediction detected (Model Probability: {sif_prob:.1%})")
    else:
        evidence_bullets.append(f"Non-SIF ML classification (Model Probability: {sif_prob:.1%})")

    if high_severity_hazards:
        evidence_bullets.append(f"High-severity hazard(s) identified: {', '.join(high_severity_hazards)}")
    elif hazards:
        evidence_bullets.append(f"Safety hazard(s) identified: {', '.join(hazards)}")

    if critical_barriers:
        evidence_bullets.append(f"Critical barrier degradation concern: {', '.join(critical_barriers)}")
    elif barriers:
        evidence_bullets.append(f"Barrier concern(s) detected: {', '.join(barriers)}")

    if repeat_flag:
        evidence_bullets.append("Repeated safety hazard previously reported/ignored")

    if sup_flag:
        evidence_bullets.append("Supervisor negligence / Permit deficiency observed")

    if ppe_flag:
        evidence_bullets.append("PPE non-compliance observed")

    if maint_flag:
        evidence_bullets.append("Maintenance delay / equipment defect observed")

    if previous_similar_reports_count > 0:
        evidence_bullets.append(f"System identified {previous_similar_reports_count} similar historical safety report(s)")

    # -------------------------------------------------------------
    # RISK ASSESSMENT MATRIX (RISK_EVAL_v1)
    # -------------------------------------------------------------
    risk_level = "LOW"

    # CRITICAL EVALUATION
    if (is_sif_ml and (critical_barriers or high_severity_hazards) and (previous_similar_reports_count >= 2 or repeat_flag)) or \
       (len(high_severity_hazards) >= 2 and sup_flag):
        risk_level = "CRITICAL"

    # HIGH EVALUATION
    elif is_sif_ml or len(high_severity_hazards) > 0 or len(critical_barriers) > 0 or previous_similar_reports_count >= 3 or repeat_flag:
        risk_level = "HIGH"

    # MEDIUM EVALUATION
    elif sif_prob >= 0.35 or ppe_flag or maint_flag or previous_similar_reports_count in (1, 2) or hazards or barriers:
        risk_level = "MEDIUM"

    # LOW EVALUATION
    else:
        risk_level = "LOW"

    logger.info(f"Risk Level calculated: {risk_level} (SIF prob: {sif_prob:.1%}, hazards: {len(hazards)}, barriers: {len(barriers)}, similar_reports: {previous_similar_reports_count}).")

    return {
        "risk_level": risk_level,
        "risk_explanation": evidence_bullets,
        "methodology_version": RISK_METHODOLOGY_VERSION
    }
