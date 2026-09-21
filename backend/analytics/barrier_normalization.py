"""
Barrier Normalization & Taxonomy Mapping Layer (Part 3C)

Maps free-text barrier concerns and precursor audit flags to a controlled taxonomy
while preserving the original user/AI barrier text for complete auditability.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Controlled Barrier Taxonomy Categories
BARRIER_PPE = "Personal Protective Equipment (PPE)"
BARRIER_ENERGY_ISOLATION = "Energy Isolation"
BARRIER_SUPERVISION_PERMIT = "Supervision & Work Permit Control"
BARRIER_MAINTENANCE = "Equipment Maintenance & Reliability"
BARRIER_RECURRENCE = "Hazard Recurrence & Isolation Control"
BARRIER_GAS_TESTING = "Gas Testing & Environmental Monitoring"
BARRIER_GUARDING = "Machine Guarding & Physical Safety"
BARRIER_COMMUNICATION = "Safety Communication & Tool Box Talk"
BARRIER_UNMAPPED = "Unmapped / Other"

STANDARD_BARRIER_TAXONOMY = [
    BARRIER_PPE,
    BARRIER_ENERGY_ISOLATION,
    BARRIER_SUPERVISION_PERMIT,
    BARRIER_MAINTENANCE,
    BARRIER_RECURRENCE,
    BARRIER_GAS_TESTING,
    BARRIER_GUARDING,
    BARRIER_COMMUNICATION,
    BARRIER_UNMAPPED,
]


@dataclass
class NormalizedBarrierObservation:
    """Represents a normalized barrier observation linked to raw evidence."""
    canonical_category: str
    original_barrier_text: str
    source_type: str  # 'AI', 'HSE', 'PRECURSOR_FLAG', 'STRUCTURED'


# Explicit Keyword Mapping Table
KEYWORD_MAPPING_RULES: List[Tuple[List[str], str]] = [
    (
        ["ppe", "helmet", "glasses", "goggles", "harness", "gloves", "boots", "earplug", "face shield", "without ppe", "no helmet"],
        BARRIER_PPE
    ),
    (
        ["loto", "lockout", "tagout", "isolation", "de-energize", "deenergize", "blind", "spade", "energy isolation", "lock out"],
        BARRIER_ENERGY_ISOLATION
    ),
    (
        ["permit", "ptw", "work permit", "supervisor", "supervision", "unauthorized", "permit expired", "no permit", "clearance"],
        BARRIER_SUPERVISION_PERMIT
    ),
    (
        ["maintenance", "vibration", "leak", "seal leak", "corroded", "corrosion", "defective valve", "faulty", "bearing", "tripped", "reliability"],
        BARRIER_MAINTENANCE
    ),
    (
        ["repeat", "previous", "recurring", "ignored", "repeated issue"],
        BARRIER_RECURRENCE
    ),
    (
        ["gas test", "gas testing", "h2s", "explosimeter", "oxygen level", "toxic gas", "flammable gas", "ventilation"],
        BARRIER_GAS_TESTING
    ),
    (
        ["guard", "guarding", "scaffolding", "railing", "handrail", "interlock", "barrier mesh", "unprotected drop", "toe board"],
        BARRIER_GUARDING
    ),
    (
        ["tbt", "toolbox", "handover", "briefing", "communication", "miscommunication", "shift change"],
        BARRIER_COMMUNICATION
    ),
]


def map_barrier_text_to_category(raw_text: str) -> str:
    """
    Normalizes free-text barrier descriptions into standard taxonomy categories.
    Falls back to 'Unmapped / Other' if no keyword matches.
    """
    if not raw_text or not isinstance(raw_text, str):
        return BARRIER_UNMAPPED

    text_lower = raw_text.strip().lower()

    for keywords, category in KEYWORD_MAPPING_RULES:
        if any(kw in text_lower for kw in keywords):
            return category

    return BARRIER_UNMAPPED


def extract_normalized_barriers_from_dto(report_dto: Any) -> List[NormalizedBarrierObservation]:
    """
    Extracts all barrier observations from a report DTO, normalizing them
    while preserving raw text and tracking whether sources are AI, HSE, or precursor flags.
    Ensures 1 occurrence per category per report.
    """
    observations: List[NormalizedBarrierObservation] = []
    seen_categories = set()

    # 1. Primary: HSE Validated Barriers if available
    if report_dto.has_hse_review and report_dto.hse_barriers:
        for raw_barrier in report_dto.hse_barriers:
            category = map_barrier_text_to_category(raw_barrier)
            if category not in seen_categories:
                seen_categories.add(category)
                observations.append(
                    NormalizedBarrierObservation(
                        canonical_category=category,
                        original_barrier_text=raw_barrier,
                        source_type="HSE"
                    )
                )

    # 2. Secondary: AI Barriers if no HSE review or to supplement
    if report_dto.has_ai_analysis and report_dto.ai_barriers:
        for raw_barrier in report_dto.ai_barriers:
            category = map_barrier_text_to_category(raw_barrier)
            if category not in seen_categories:
                seen_categories.add(category)
                observations.append(
                    NormalizedBarrierObservation(
                        canonical_category=category,
                        original_barrier_text=raw_barrier,
                        source_type="AI"
                    )
                )

    # 3. Tertiary: Precursor Boolean Flags fallback
    if not seen_categories:
        if report_dto.ppe_noncompliance and BARRIER_PPE not in seen_categories:
            seen_categories.add(BARRIER_PPE)
            observations.append(
                NormalizedBarrierObservation(
                    canonical_category=BARRIER_PPE,
                    original_barrier_text="PPE Non-Compliance Flag",
                    source_type="PRECURSOR_FLAG"
                )
            )
        if report_dto.supervisor_negligence and BARRIER_SUPERVISION_PERMIT not in seen_categories:
            seen_categories.add(BARRIER_SUPERVISION_PERMIT)
            observations.append(
                NormalizedBarrierObservation(
                    canonical_category=BARRIER_SUPERVISION_PERMIT,
                    original_barrier_text="Supervisor Negligence Flag",
                    source_type="PRECURSOR_FLAG"
                )
            )
        if report_dto.maintenance_delay_or_issue and BARRIER_MAINTENANCE not in seen_categories:
            seen_categories.add(BARRIER_MAINTENANCE)
            observations.append(
                NormalizedBarrierObservation(
                    canonical_category=BARRIER_MAINTENANCE,
                    original_barrier_text="Maintenance Issue Flag",
                    source_type="PRECURSOR_FLAG"
                )
            )
        if report_dto.repeated_issue_ignored and BARRIER_RECURRENCE not in seen_categories:
            seen_categories.add(BARRIER_RECURRENCE)
            observations.append(
                NormalizedBarrierObservation(
                    canonical_category=BARRIER_RECURRENCE,
                    original_barrier_text="Repeated Issue Ignored Flag",
                    source_type="PRECURSOR_FLAG"
                )
            )

    return observations
