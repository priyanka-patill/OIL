"""
Part 4A — Intervention Recommendation Engine

Deterministic, transparent, evidence-backed recommendation generation engine.
Transforms Part 2 AI analysis and Part 3 Safety Intelligence findings into
AI/System-Suggested Interventions requiring HSE validation.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.database.models import InterventionCategory, InterventionPriority, InterventionStatus

logger = logging.getLogger("backend.services.intervention_recommendation_engine")

RECOMMENDATION_ENGINE_VERSION = "intervention_rules_v1"
ANALYTICS_VERSION = "safety_intelligence_v1"
DEFAULT_MODEL_VERSION = "sif_model_v1"


def evaluate_intervention_priority(
    sif_classification: str,
    evidence_count: int,
    is_pattern: bool,
    is_recurring_barrier: bool,
    bdi_score: Optional[float],
    has_escalation: bool,
    has_unresolved: bool,
    sample_sufficient: bool = True
) -> InterventionPriority:
    """
    Evaluates transparent Priority Suggestion (PRI_SUGGESTION) for an intervention recommendation.
    Not a risk probability or SLA urgency. Strictly an evidence indicator for HSE review.
    """
    if not sample_sufficient:
        return InterventionPriority.INSUFFICIENT_DATA

    is_sif = sif_classification in ["SIF-Potential", "SIF_PRECURSOR", "1"]

    if is_sif and (is_pattern or is_recurring_barrier or (bdi_score is not None and bdi_score >= 50.0) or has_escalation):
        return InterventionPriority.HIGH
    elif is_sif:
        return InterventionPriority.MEDIUM
    elif is_pattern or is_recurring_barrier or has_unresolved or (bdi_score is not None and bdi_score >= 30.0):
        return InterventionPriority.MEDIUM
    elif evidence_count > 0:
        return InterventionPriority.LOW
    else:
        return InterventionPriority.INSUFFICIENT_DATA


def map_intervention_category(
    barrier: str,
    lsrs: List[str],
    hazards: List[str],
    work_type: str,
    report_flags: Dict[str, bool]
) -> InterventionCategory:
    """
    Determines controlled Intervention Category based on actual safety intelligence inputs.
    """
    barrier_lower = (barrier or "").lower()
    lsr_str = " ".join([l.lower() for l in lsrs])
    hazard_str = " ".join([h.lower() for h in hazards])
    work_lower = (work_type or "").lower()

    if "energy isolation" in barrier_lower or "isolation" in lsr_str or "loto" in work_lower:
        return InterventionCategory.ENERGY_ISOLATION
    elif "confined space" in barrier_lower or "confined space" in lsr_str:
        return InterventionCategory.CONFINED_SPACE_CONTROL
    elif "gas detection" in barrier_lower or "atmospheric testing" in lsr_str or "gas" in hazard_str:
        return InterventionCategory.GAS_TESTING
    elif "working at height" in barrier_lower or "height" in lsr_str or "fall" in hazard_str:
        return InterventionCategory.WORKING_AT_HEIGHT_CONTROL
    elif "hot work" in barrier_lower or "hot work" in lsr_str or "fire" in hazard_str or "explosion" in hazard_str:
        return InterventionCategory.HOT_WORK_CONTROL
    elif "lifting" in barrier_lower or "lifting" in lsr_str or "crane" in work_lower or "line of fire" in lsr_str:
        return InterventionCategory.LIFTING_CONTROL
    elif report_flags.get("ppe_noncompliance") or "ppe" in barrier_lower or "personal protective" in barrier_lower:
        return InterventionCategory.PPE_CONTROL
    elif "permit" in barrier_lower or "permit to work" in lsr_str:
        return InterventionCategory.PERMIT_CONTROL
    elif report_flags.get("maintenance_delay_or_issue") or "maintenance" in work_lower:
        return InterventionCategory.MAINTENANCE
    elif "guarding" in barrier_lower or "moving equipment" in hazard_str:
        return InterventionCategory.EQUIPMENT_GUARDING
    elif report_flags.get("supervisor_negligence") or "supervisor" in work_lower:
        return InterventionCategory.SUPERVISION
    elif report_flags.get("repeated_issue_ignored"):
        return InterventionCategory.PROCEDURE_REVIEW
    else:
        return InterventionCategory.OTHER


def generate_recommendation_payload(
    report_data: Dict[str, Any],
    ai_analysis_data: Optional[Dict[str, Any]] = None,
    pattern_data: Optional[Dict[str, Any]] = None,
    barrier_data: Optional[Dict[str, Any]] = None,
    escalation_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates a complete, evidence-traceable Intervention Recommendation structure.
    Does NOT create operational actions or SLA assignments.
    """
    # Extract AI analysis details
    prediction = ai_analysis_data.get("prediction", "Non-SIF-Potential") if ai_analysis_data else "Non-SIF-Potential"
    model_ver = ai_analysis_data.get("model_version", DEFAULT_MODEL_VERSION) if ai_analysis_data else DEFAULT_MODEL_VERSION
    
    lsrs = []
    if ai_analysis_data and ai_analysis_data.get("life_saving_rules_json"):
        try:
            lsrs = json.loads(ai_analysis_data["life_saving_rules_json"])
        except Exception:
            lsrs = []
            
    hazards = []
    if ai_analysis_data and ai_analysis_data.get("hazards_json"):
        try:
            hazards = json.loads(ai_analysis_data["hazards_json"])
        except Exception:
            hazards = []

    barriers = []
    if ai_analysis_data and ai_analysis_data.get("barrier_concerns_json"):
        try:
            barriers = json.loads(ai_analysis_data["barrier_concerns_json"])
        except Exception:
            barriers = []

    primary_barrier = barriers[0] if barriers else (barrier_data.get("barrier_category") if barrier_data else "")

    # Extract boolean precursor flags
    report_flags = {
        "ppe_noncompliance": report_data.get("ppe_noncompliance", False),
        "supervisor_negligence": report_data.get("supervisor_negligence", False),
        "maintenance_delay_or_issue": report_data.get("maintenance_delay_or_issue", False),
        "repeated_issue_ignored": report_data.get("repeated_issue_ignored", False),
    }

    # Determine Category
    category = map_intervention_category(
        barrier=primary_barrier,
        lsrs=lsrs,
        hazards=hazards,
        work_type=report_data.get("work_type", ""),
        report_flags=report_flags
    )

    # Contextual evidence
    is_pattern = pattern_data is not None and (pattern_data.get("occurrence_count", 0) > 1 or pattern_data.get("support_count", 0) > 1)
    is_recurring_barrier = barrier_data is not None and (barrier_data.get("recurrence_count", 0) > 1)
    bdi_score = barrier_data.get("bdi_score") if barrier_data else None
    has_escalation = escalation_data is not None and len(escalation_data.get("indicators", [])) > 0
    has_unresolved = report_data.get("action_status") == "ACTION_REQUIRED" or (barrier_data and barrier_data.get("unresolved_count", 0) > 0)

    # Determine Priority Suggestion
    priority = evaluate_intervention_priority(
        sif_classification=prediction,
        evidence_count=1 + (pattern_data.get("occurrence_count", 0) if pattern_data else 0),
        is_pattern=is_pattern,
        is_recurring_barrier=is_recurring_barrier,
        bdi_score=bdi_score,
        has_escalation=has_escalation,
        has_unresolved=has_unresolved,
        sample_sufficient=True
    )

    # Formulate Title, Recommendation Text, and Rationale based on Category
    site_str = report_data.get("site", "Refinery Site")
    equip_str = report_data.get("equipment_id", "Asset")
    work_str = report_data.get("work_type", report_data.get("activity", "Operational Activity"))

    if category == InterventionCategory.ENERGY_ISOLATION:
        title = f"Verify Energy Isolation & LOTO Controls for {equip_str}"
        rec_text = (
            f"1. Conduct immediate field verification of Lockout/Tagout (LOTO) isolation on {equip_str} at {site_str}.\n"
            f"2. Audit the zero-energy verification procedure prior to maintenance permit approval.\n"
            f"3. Verify padlocks, tags, and physical isolation barrier integrity."
        )
        rationale = f"Energy Isolation concerns were identified in report observations associated with {work_str}."
    elif category == InterventionCategory.CONFINED_SPACE_CONTROL:
        title = f"Strengthen Confined Space Entry & Gas Testing for {equip_str}"
        rec_text = (
            f"1. Mandatory pre-entry atmospheric testing (Oxygen, Flammable, Toxic gases) for {equip_str}.\n"
            f"2. Verify attendant standby and emergency rescue equipment availability.\n"
            f"3. Re-validate entry permit authorization before personnel entry."
        )
        rationale = f"Confined space entry hazard indicators identified during {work_str}."
    elif category == InterventionCategory.WORKING_AT_HEIGHT_CONTROL:
        title = f"Audit Working at Height & Fall Barrier Controls at {site_str}"
        rec_text = (
            f"1. Inspect full-body harness, 100% tie-off anchorage points, and lifelines.\n"
            f"2. Conduct scaffolding tag verification and toe-board/guardrail inspection.\n"
            f"3. Verify drop-object prevention netting and tool lanyards."
        )
        rationale = f"Working at height / fall hazard precursors identified during {work_str}."
    elif category == InterventionCategory.HOT_WORK_CONTROL:
        title = f"Review Hot Work Permit & Fire Protection Barriers at {site_str}"
        rec_text = (
            f"1. Verify continuous combustible gas monitoring and fire watch stationing.\n"
            f"2. Clear 35 ft radius of combustible materials and deploy fire blankets.\n"
            f"3. Inspect pressurized fire hose / portable fire extinguisher availability."
        )
        rationale = f"Hot work / thermal hazard precursors identified during {work_str}."
    elif category == InterventionCategory.MAINTENANCE:
        title = f"Conduct Equipment Maintenance & Barrier Audit on {equip_str}"
        rec_text = (
            f"1. Perform mechanical preventive maintenance inspection on {equip_str}.\n"
            f"2. Verify physical machine guarding, vibration, and seal integrity.\n"
            f"3. Expedite backlog maintenance work orders affecting safety barriers."
        )
        rationale = f"Equipment maintenance delays or mechanical safety barrier issues reported."
    elif category == InterventionCategory.PPE_CONTROL:
        title = f"Reinforce PPE Compliance & Suitability at {site_str}"
        rec_text = (
            f"1. Verify task-specific Personal Protective Equipment (PPE) availability and condition.\n"
            f"2. Conduct supervisor pre-job toolbox check for PPE compliance.\n"
            f"3. Replace damaged or non-compliant protective equipment immediately."
        )
        rationale = f"PPE non-compliance or suitability concerns identified in observation data."
    elif category == InterventionCategory.SUPERVISION:
        title = f"Enhance Supervisory Oversight & Permit Compliance during {work_str}"
        rec_text = (
            f"1. Mandate supervisor physical presence during critical work permit steps.\n"
            f"2. Re-verify permit-to-work sign-offs and hazard identification prior to task start.\n"
            f"3. Conduct supervisory pre-job safety brief with all working crew members."
        )
        rationale = f"Supervisory oversight or permit compliance issues identified in report."
    else:
        title = f"Review Safety Barriers and Operational Procedures for {work_str}"
        rec_text = (
            f"1. Review safe operating procedures applicable to {work_str} at {site_str}.\n"
            f"2. Conduct field-level hazard assessment prior to continuing operations.\n"
            f"3. Communicate safety observation findings during site safety meeting."
        )
        rationale = f"Safety observation precursor evidence identified during operational activities."

    if is_pattern:
        rationale += f" Supporting evidence includes Part 3A recurring pattern cluster ({pattern_data.get('occurrence_count', 2)} occurrences)."
    if is_recurring_barrier:
        rationale += f" Part 3C barrier intelligence shows recurring concern for barrier '{primary_barrier}'."

    # Build Traceable Evidence Payload
    evidence_payload = {
        "report_id": report_data.get("id"),
        "report_number": report_data.get("report_number"),
        "site": site_str,
        "department": report_data.get("department"),
        "work_type": work_str,
        "equipment_id": equip_str,
        "sif_classification": prediction,
        "hazards": hazards,
        "life_saving_rules": lsrs,
        "barrier_category": primary_barrier,
        "is_recurring_pattern": is_pattern,
        "pattern_id": pattern_data.get("pattern_id") if pattern_data else None,
        "bdi_score": bdi_score,
        "escalation_indicators": escalation_data.get("indicators", []) if escalation_data else [],
        "first_observed": report_data.get("date"),
        "latest_observed": report_data.get("date"),
        "evidence_count": 1 + (pattern_data.get("occurrence_count", 0) if pattern_data else 0),
    }

    evidence_summary = (
        f"Generated from Report {report_data.get('report_number')} ({prediction}) at {site_str} "
        f"covering {work_str}. Primary barrier concern: '{primary_barrier or 'General'}'. "
        f"Evidence count: {evidence_payload['evidence_count']}."
    )

    return {
        "title": title,
        "category": category,
        "recommendation_text": rec_text,
        "rationale": rationale,
        "priority_suggestion": priority,
        "evidence_summary": evidence_summary,
        "evidence_json": json.dumps(evidence_payload),
        "evidence_count": evidence_payload["evidence_count"],
        "first_observed": report_data.get("date"),
        "latest_observed": report_data.get("date"),
        "sif_classification": prediction,
        "hazards_json": json.dumps(hazards),
        "life_saving_rules_json": json.dumps(lsrs),
        "bdi_score": bdi_score,
        "escalation_indicators_json": json.dumps(escalation_data.get("indicators", [])) if escalation_data else None,
        "model_version": model_ver,
        "analytics_version": ANALYTICS_VERSION,
        "methodology_version": RECOMMENDATION_ENGINE_VERSION,
        "status": InterventionStatus.PENDING_HSE_VALIDATION,
    }
