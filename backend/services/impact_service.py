"""
Part 4E — Observational Before/After Impact Tracking Service

Calculates, evaluates, and immutably stores observational safety indicators before vs. after an intervention.

IMPORTANT METHODOLOGY RULES (impact_methodology_v1):
1. STRICT NON-CAUSAL FRAMING: Observed change descriptions are strictly observational ("Observed change after intervention"). Zero causal claims ("caused", "prevented", "eliminated", "reduced fatality risk").
2. DATA SUFFICIENCY: Enforces minimum sample rules (min 2 relevant before-period reports). Small samples return INSUFFICIENT_DATA rather than misleading improvement percentages.
3. ZERO DENOMINATOR PROTECTION: Divisors are checked to prevent division by zero.
4. ANTI-LEAKAGE ENFORCEMENT: 'source_sheet' and '12_High_Potential' have ZERO influence on impact analysis.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from backend.database.models import (
    Action, ActionImpactAnalysis, SafetyReport, AIAnalysis,
    InterventionRecommendation, utc_now
)

logger = logging.getLogger(__name__)

METHODOLOGY_VERSION = "impact_methodology_v1"
DISCLAIMER_TEXT = (
    "These comparisons describe observed changes between the defined before and after periods. "
    "They do not establish that the intervention caused the observed change."
)

MIN_REQUIRED_BEFORE_REPORTS = 2


def ensure_utc(dt: Optional[datetime]) -> datetime:
    """Utility helper ensuring datetime object is UTC timezone-aware."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def determine_intervention_date(action: Action) -> datetime:
    """
    Authoritative intervention date selection:
    Prefers HSE verified_at date, falls back to completion_date, or current UTC date.
    """
    if action.verified_at:
        return ensure_utc(action.verified_at)
    if action.completion_date:
        return ensure_utc(action.completion_date)
    return ensure_utc(utc_now())


def determine_observation_periods(
    intervention_date: datetime,
    before_days: int = 90,
    after_days: int = 90
) -> Dict[str, Any]:
    """Calculate before and after observation date windows around intervention date."""
    int_utc = ensure_utc(intervention_date)

    before_end_dt = int_utc
    before_start_dt = int_utc - timedelta(days=before_days)

    after_start_dt = int_utc + timedelta(days=1)
    after_end_dt = int_utc + timedelta(days=after_days)

    return {
        "before_start": before_start_dt.strftime("%Y-%m-%d"),
        "before_end": before_end_dt.strftime("%Y-%m-%d"),
        "after_start": after_start_dt.strftime("%Y-%m-%d"),
        "after_end": after_end_dt.strftime("%Y-%m-%d"),
        "before_days": before_days,
        "after_days": after_days,
        "intervention_date": int_utc.strftime("%Y-%m-%d")
    }


def query_scoped_reports(
    db: Session,
    site: Optional[str],
    department: Optional[str],
    barrier_id: Optional[str],
    pattern_id: Optional[str],
    start_date_str: str,
    end_date_str: str
) -> List[SafetyReport]:
    """
    Fetch precursor safety reports within defined observation period matching intervention scope.
    """
    query = db.query(SafetyReport)

    # Filter by date range (using date or func.date(created_at))
    query = query.filter(
        or_(
            and_(SafetyReport.date >= start_date_str, SafetyReport.date <= end_date_str),
            and_(SafetyReport.date.is_(None), func.date(SafetyReport.created_at) >= start_date_str, func.date(SafetyReport.created_at) <= end_date_str)
        )
    )

    if site:
        query = query.filter(SafetyReport.site == site)
    if department:
        query = query.filter(SafetyReport.department == department)

    reports = query.all()

    # Scope filtering by barrier or pattern if specified
    if barrier_id or pattern_id:
        filtered = []
        for r in reports:
            matches = False
            r_text = f"{r.description or ''} {r.work_type or ''} {r.activity or ''}".lower()

            if barrier_id:
                b_low = barrier_id.lower()
                if b_low in r_text:
                    matches = True
                elif r.ai_analyses:
                    for ai in r.ai_analyses:
                        if b_low in str(ai.barrier_concerns_json or "").lower() or b_low in str(ai.explanation_json or "").lower():
                            matches = True
                            break

            if pattern_id and r.ai_analyses:
                p_low = pattern_id.lower()
                for ai in r.ai_analyses:
                    if p_low in str(ai.explanation_json or "").lower():
                        matches = True
                        break

            if not barrier_id and not pattern_id:
                matches = True

            if matches:
                filtered.append(r)
        return filtered

    return reports


def count_sif_reports(reports_list: List[SafetyReport]) -> int:
    """Count SIF-Potential reports within a report callset."""
    sif_cnt = 0
    for r in reports_list:
        is_sif = False
        if r.ai_analyses:
            for ai in r.ai_analyses:
                if ai.prediction in ('SIF_POTENTIAL', 'SIF', 'HIGH') or ai.classification == 1:
                    is_sif = True
                    break
        if is_sif:
            sif_cnt += 1
    return sif_cnt


def count_barrier_occurrences(reports_list: List[SafetyReport], barrier_category: Optional[str]) -> int:
    """Count occurrences of a specific barrier category within reports."""
    if not barrier_category:
        return len(reports_list)
    cnt = 0
    b_low = barrier_category.lower()
    for r in reports_list:
        r_text = f"{r.description or ''} {r.work_type or ''} {r.activity or ''}".lower()
        found = b_low in r_text
        if not found and r.ai_analyses:
            for ai in r.ai_analyses:
                if b_low in str(ai.barrier_concerns_json or "").lower():
                    found = True
                    break
        if found:
            cnt += 1
    return cnt


def calculate_and_store_impact(
    db: Session,
    action: Action,
    before_days: int = 90,
    after_days: int = 90
) -> ActionImpactAnalysis:
    """
    Calculate 5 observational safety indicators and immutably store an ActionImpactAnalysis snapshot.
    """
    int_date = determine_intervention_date(action)
    periods = determine_observation_periods(int_date, before_days=before_days, after_days=after_days)

    # Fetch scope attributes
    site = action.site
    dept = action.assigned_department
    barrier_id = action.barrier_id
    pattern_id = action.pattern_id

    # Fetch before and after reports matching intervention scope
    before_reports = query_scoped_reports(db, site, dept, barrier_id, pattern_id, periods["before_start"], periods["before_end"])
    after_reports = query_scoped_reports(db, site, dept, barrier_id, pattern_id, periods["after_start"], periods["after_end"])

    # Also fetch site-wide analyzed report denominators for precursor density calculation
    all_before = db.query(SafetyReport).filter(
        SafetyReport.site == site,
        or_(
            and_(SafetyReport.date >= periods["before_start"], SafetyReport.date <= periods["before_end"]),
            and_(SafetyReport.date.is_(None), func.date(SafetyReport.created_at) >= periods["before_start"], func.date(SafetyReport.created_at) <= periods["before_end"])
        )
    ).all()

    all_after = db.query(SafetyReport).filter(
        SafetyReport.site == site,
        or_(
            and_(SafetyReport.date >= periods["after_start"], SafetyReport.date <= periods["after_end"]),
            and_(SafetyReport.date.is_(None), func.date(SafetyReport.created_at) >= periods["after_start"], func.date(SafetyReport.created_at) <= periods["after_end"])
        )
    ).all()

    before_sif_cnt = count_sif_reports(before_reports)
    after_sif_cnt = count_sif_reports(after_reports)

    before_all_denom = len(all_before)
    after_all_denom = len(all_after)

    # 1. Related Report Recurrence
    before_recurrence = len(before_reports)
    after_recurrence = len(after_reports)

    # 3. Barrier Recurrence
    before_barrier_cnt = count_barrier_occurrences(before_reports, barrier_id)
    after_barrier_cnt = count_barrier_occurrences(after_reports, barrier_id)

    # 4. SIF Precursor Density (SIF / analyzed_reports) with zero denominator check
    before_density = round((before_sif_cnt / before_all_denom) * 100, 2) if before_all_denom > 0 else None
    after_density = round((after_sif_cnt / after_all_denom) * 100, 2) if after_all_denom > 0 else None

    # 5. Pattern Frequency
    before_pattern_cnt = before_recurrence
    after_pattern_cnt = after_recurrence

    # Evaluate Data Sufficiency Rules
    is_sufficient = True
    sufficiency_reasons = []

    if before_recurrence < MIN_REQUIRED_BEFORE_REPORTS:
        is_sufficient = False
        sufficiency_reasons.append(
            f"Only {before_recurrence} relevant precursor report(s) were observed in the before period "
            f"(minimum required sample for statistical relevance is {MIN_REQUIRED_BEFORE_REPORTS})."
        )

    if before_all_denom == 0:
        is_sufficient = False
        sufficiency_reasons.append("No analyzed reports available in the before period for density calculation.")

    sufficiency_status = "SUFFICIENT" if is_sufficient else "INSUFFICIENT_DATA"
    sufficiency_reason = " ".join(sufficiency_reasons) if sufficiency_reasons else "Data volume meets minimum sample requirements for descriptive comparison."

    # Determine overall observed change status (Descriptive / Non-causal)
    if not is_sufficient:
        overall_change = "INSUFFICIENT_DATA"
    elif after_recurrence < before_recurrence:
        overall_change = "OBSERVED_DECREASE"
    elif after_recurrence > before_recurrence:
        overall_change = "OBSERVED_INCREASE"
    else:
        overall_change = "OBSERVED_STABLE"

    # Construct 5 Safety Indicators Metrics JSON Payload
    metrics_payload = {
        "related_report_recurrence": {
            "name": "Related Report Recurrence",
            "before": before_recurrence,
            "after": after_recurrence,
            "change": after_recurrence - before_recurrence,
            "status": "INSUFFICIENT_DATA" if not is_sufficient else ("OBSERVED_DECREASE" if after_recurrence < before_recurrence else ("OBSERVED_INCREASE" if after_recurrence > before_recurrence else "OBSERVED_STABLE")),
            "description": f"Observed count changed from {before_recurrence} to {after_recurrence} reports."
        },
        "sif_potential_reports": {
            "name": "SIF-Potential Precursor Reports",
            "before_count": before_sif_cnt,
            "before_denominator": len(before_reports),
            "after_count": after_sif_cnt,
            "after_denominator": len(after_reports),
            "status": "INSUFFICIENT_DATA" if not is_sufficient else ("OBSERVED_DECREASE" if after_sif_cnt < before_sif_cnt else ("OBSERVED_INCREASE" if after_sif_cnt > before_sif_cnt else "OBSERVED_STABLE")),
            "description": f"SIF-Potential precursor observations changed from {before_sif_cnt}/{len(before_reports)} to {after_sif_cnt}/{len(after_reports)}."
        },
        "barrier_recurrence": {
            "name": "Barrier Recurrence",
            "barrier_category": barrier_id or "General Barrier",
            "before": before_barrier_cnt,
            "after": after_barrier_cnt,
            "status": "INSUFFICIENT_DATA" if not is_sufficient else ("OBSERVED_DECREASE" if after_barrier_cnt < before_barrier_cnt else ("OBSERVED_INCREASE" if after_barrier_cnt > before_barrier_cnt else "OBSERVED_STABLE")),
            "description": f"Barrier occurrence changed from {before_barrier_cnt} to {after_barrier_cnt} occurrences."
        },
        "sif_precursor_density": {
            "name": "SIF Precursor Density",
            "before_sif": before_sif_cnt,
            "before_total_analyzed": before_all_denom,
            "before_density_pct": before_density,
            "after_sif": after_sif_cnt,
            "after_total_analyzed": after_all_denom,
            "after_density_pct": after_density,
            "status": "INSUFFICIENT_DATA" if (before_density is None or after_density is None or not is_sufficient) else ("OBSERVED_DECREASE" if after_density < before_density else ("OBSERVED_INCREASE" if after_density > before_density else "OBSERVED_STABLE")),
            "description": f"Precursor density changed from {before_density if before_density is not None else 'N/A'}% to {after_density if after_density is not None else 'N/A'}%."
        },
        "pattern_frequency": {
            "name": "Recurring Pattern Frequency",
            "pattern_id": pattern_id or "N/A",
            "before": before_pattern_cnt,
            "after": after_pattern_cnt,
            "status": "INSUFFICIENT_DATA" if not is_sufficient else ("OBSERVED_DECREASE" if after_pattern_cnt < before_pattern_cnt else ("OBSERVED_INCREASE" if after_pattern_cnt > before_pattern_cnt else "OBSERVED_STABLE")),
            "description": f"Pattern frequency changed from {before_pattern_cnt} to {after_pattern_cnt} occurrences."
        },
        "contributing_report_ids_before": [r.id for r in before_reports],
        "contributing_report_ids_after": [r.id for r in after_reports],
        "disclaimer": DISCLAIMER_TEXT
    }

    impact_record = ActionImpactAnalysis(
        action_id=action.id,
        intervention_id=action.intervention_id,
        report_id=action.report_id,
        pattern_id=pattern_id,
        barrier_id=barrier_id,
        intervention_date=int_date,
        before_start=periods["before_start"],
        before_end=periods["before_end"],
        after_start=periods["after_start"],
        after_end=periods["after_end"],
        metrics_json=json.dumps(metrics_payload),
        overall_observed_change=overall_change,
        data_sufficiency_status=sufficiency_status,
        data_sufficiency_reason=sufficiency_reason,
        methodology_version=METHODOLOGY_VERSION,
        calculated_at=utc_now()
    )

    db.add(impact_record)
    db.commit()
    db.refresh(impact_record)

    logger.info(f"Calculated Part 4E Impact Snapshot #{impact_record.id} for Action #{action.id} (Status: {overall_change})")
    return impact_record


def get_latest_impact_analysis(db: Session, action_id: int) -> Optional[ActionImpactAnalysis]:
    """Retrieve latest calculated impact snapshot for an action."""
    return (
        db.query(ActionImpactAnalysis)
        .filter(ActionImpactAnalysis.action_id == action_id)
        .order_by(ActionImpactAnalysis.id.desc())
        .first()
    )
