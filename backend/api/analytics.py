"""
Analytics Engine API Router (Part 3A & Part 3B)

Exposes REST endpoints for recurring patterns, related reports, duplicate detection,
cross-report correlation, organizational dimensions, SIF precursor density, trends, and hotspots.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.security.dependencies import get_current_user
from backend.analytics.service import AnalyticsService
from backend.analytics.config import ANALYTICS_MIN_PATTERN_COUNT

router = APIRouter(prefix="/analytics", tags=["Analytics Foundation & Hotspots"])


# -------------------------------------------------------------
# PART 3A ENDPOINTS
# -------------------------------------------------------------
@router.get("/patterns", response_model=dict)
def get_recurring_patterns(
    site: Optional[str] = Query(None, description="Filter by site"),
    refinery_unit: Optional[str] = Query(None, description="Filter by refinery unit"),
    department: Optional[str] = Query(None, description="Filter by department"),
    work_type: Optional[str] = Query(None, description="Filter by work type"),
    min_support: int = Query(ANALYTICS_MIN_PATTERN_COUNT, ge=1, description="Minimum pattern occurrence count"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve recurring safety patterns meeting minimum support threshold."""
    return AnalyticsService.get_recurring_patterns(
        db=db,
        user=current_user,
        site_filter=site,
        refinery_unit_filter=refinery_unit,
        department_filter=department,
        work_type_filter=work_type,
        min_support=min_support,
    )


@router.get("/patterns/{pattern_id}", response_model=dict)
def get_pattern_by_id(
    pattern_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific recurring safety pattern by ID."""
    pattern = AnalyticsService.get_pattern_by_id(
        pattern_id=pattern_id,
        db=db,
        user=current_user,
    )
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pattern with ID '{pattern_id}' not found or unauthorized.",
        )
    return pattern


@router.get("/related-reports/{report_id}", response_model=dict)
def get_related_reports(
    report_id: int,
    max_results: int = Query(5, ge=1, le=20, description="Maximum related reports to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve analytically related reports for a target report with evidence explanations."""
    return AnalyticsService.get_related_reports(
        report_id=report_id,
        db=db,
        user=current_user,
        max_results=max_results,
    )


@router.get("/duplicates", response_model=dict)
def get_duplicate_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detected exact, near-duplicate, and potentially similar report groups."""
    return AnalyticsService.get_duplicates(
        db=db,
        user=current_user,
    )


@router.get("/correlation", response_model=dict)
def get_correlations(
    min_count: int = Query(2, ge=1, description="Minimum correlation occurrence count"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve cross-report dimension correlations (single, pairwise, multi-factor)."""
    return AnalyticsService.get_correlations(
        db=db,
        user=current_user,
        min_count=min_count,
    )


# -------------------------------------------------------------
# PART 3B ENDPOINTS
# -------------------------------------------------------------
@router.get("/density", response_model=dict)
def get_sif_density(
    site: Optional[str] = Query(None, description="Filter by site"),
    refinery_unit: Optional[str] = Query(None, description="Filter by refinery unit"),
    department: Optional[str] = Query(None, description="Filter by department"),
    work_type: Optional[str] = Query(None, description="Filter by work type"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve descriptive SIF precursor density metrics and small-sample data sufficiency indicators."""
    return AnalyticsService.get_sif_density(
        db=db,
        user=current_user,
        site_filter=site,
        refinery_unit_filter=refinery_unit,
        department_filter=department,
        work_type_filter=work_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/sites", response_model=dict)
def get_site_analytics(
    department: Optional[str] = Query(None, description="Filter by department"),
    work_type: Optional[str] = Query(None, description="Filter by work type"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Site profile analytics."""
    return AnalyticsService.get_dimension_analytics(
        dimension_name="site",
        db=db,
        user=current_user,
        department_filter=department,
        work_type_filter=work_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/activities", response_model=dict)
def get_activity_analytics(
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Activity profile analytics."""
    return AnalyticsService.get_dimension_analytics(
        dimension_name="activity",
        db=db,
        user=current_user,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/equipment", response_model=dict)
def get_equipment_analytics(
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Equipment profile analytics."""
    return AnalyticsService.get_dimension_analytics(
        dimension_name="equipment_id",
        db=db,
        user=current_user,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/locations", response_model=dict)
def get_location_analytics(
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Location profile analytics."""
    return AnalyticsService.get_dimension_analytics(
        dimension_name="location",
        db=db,
        user=current_user,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/departments", response_model=dict)
def get_department_analytics(
    site: Optional[str] = Query(None, description="Filter by site"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Department profile analytics."""
    return AnalyticsService.get_dimension_analytics(
        dimension_name="department",
        db=db,
        user=current_user,
        site_filter=site,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/refinery-units", response_model=dict)
def get_refinery_unit_analytics(
    site: Optional[str] = Query(None, description="Filter by site"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Refinery Unit profile analytics."""
    return AnalyticsService.get_dimension_analytics(
        dimension_name="refinery_unit",
        db=db,
        user=current_user,
        site_filter=site,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/trends", response_model=dict)
def get_trends(
    period: str = Query("month", description="Aggregation period: week, month, or quarter"),
    date_preset: Optional[str] = Query(None, description="Date preset: 7d, 30d, 90d, 6m, 12m"),
    start_date: Optional[str] = Query(None, description="Custom start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Custom end date YYYY-MM-DD"),
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve temporal trends for report volume and SIF precursor density."""
    try:
        return AnalyticsService.get_trends(
            db=db,
            user=current_user,
            period_type=period,
            date_preset=date_preset,
            custom_start_date=start_date,
            custom_end_date=end_date,
            site_filter=site,
            department_filter=department,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )


@router.get("/hotspots", response_model=dict)
def get_hotspots(
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum hotspots to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve multi-dimensional concentration analysis (hotspots)."""
    return AnalyticsService.get_hotspots(
        db=db,
        user=current_user,
        site_filter=site,
        department_filter=department,
        max_results=max_results,
    )


# -----------------------------------------------------------------
# PART 3C — BARRIER INTELLIGENCE & BDI ENDPOINTS
# -----------------------------------------------------------------
@router.get("/barriers", response_model=dict)
def get_barrier_analytics(
    site: Optional[str] = Query(None, description="Filter by site"),
    refinery_unit: Optional[str] = Query(None, description="Filter by refinery unit"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve barrier frequency and recurrence analytics."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )
    return AnalyticsService.get_barrier_analytics(
        db=db,
        user=current_user,
        site_filter=site,
        refinery_unit_filter=refinery_unit,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/barriers/{barrier_category}", response_model=dict)
def get_barrier_detail(
    barrier_category: str,
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed profile for a specific barrier category."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )
    return AnalyticsService.get_barrier_detail(
        barrier_category=barrier_category,
        db=db,
        user=current_user,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/bdi", response_model=dict)
def get_bdi(
    barrier: Optional[str] = Query(None, description="Filter by specific barrier category"),
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    period: str = Query("month", description="Trend calculation period: week, month, quarter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Barrier Degradation Index (BDI_v1) scores and evidence payloads."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )
    return AnalyticsService.get_bdi(
        db=db,
        user=current_user,
        barrier_category=barrier,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
        trend_period=period,
    )


@router.get("/bdi/trends", response_model=dict)
def get_bdi_trends(
    barrier: Optional[str] = Query(None, description="Filter by specific barrier category"),
    period: str = Query("month", description="Aggregation period: week, month, quarter"),
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve time-series trends for barrier occurrences and BDI evolution."""
    return AnalyticsService.get_bdi_trends(
        db=db,
        user=current_user,
        barrier_category=barrier,
        period=period,
        site_filter=site,
        department_filter=department,
    )


# -----------------------------------------------------------------
# PART 3D — POTENTIAL RISK ESCALATION & PRIORITIZATION ENDPOINTS
# -----------------------------------------------------------------
@router.get("/escalation", response_model=dict)
def get_escalation_analytics(
    dimension: str = Query("equipment_id", description="Dimension to evaluate: equipment_id, site, activity, department, location"),
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve potential risk escalation indicators across entities."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )
    return AnalyticsService.get_escalation_analytics(
        db=db,
        user=current_user,
        dimension_name=dimension,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/escalation/{entity_type}/{entity_id}", response_model=dict)
def get_escalation_detail(
    entity_type: str,
    entity_id: str,
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed risk escalation and priority profile for a specific entity."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )
    return AnalyticsService.get_escalation_detail(
        entity_type=entity_type,
        entity_id=entity_id,
        db=db,
        user=current_user,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/priorities", response_model=dict)
def get_analytical_priorities(
    dimension: str = Query("equipment_id", description="Dimension to evaluate: equipment_id, site, activity, department, location"),
    site: Optional[str] = Query(None, description="Filter by site"),
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[str] = Query(None, description="Filter by start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter by end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Analytical Priority Tiers (PRI_v1) across entities."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )
    return AnalyticsService.get_analytical_priorities(
        db=db,
        user=current_user,
        dimension_name=dimension,
        site_filter=site,
        department_filter=department,
        start_date=start_date,
        end_date=end_date,
    )


