"""
Analytics Orchestrator Service (Part 3A & Part 3B)

Coordinates data fetching, authorization enforcement, normalization,
duplicate grouping, cross-report correlation, pattern detection,
dimension profiling, SIF density, trends, and hotspot analysis.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.database.models import User
from backend.analytics.config import ANALYTICS_MIN_PATTERN_COUNT, ANALYTICS_VERSION
from backend.analytics.data_access import get_analytics_reports, AnalyticsReportDTO
from backend.analytics.normalization import normalize_report
from backend.analytics.duplicates import detect_duplicates, DuplicateGroup
from backend.analytics.correlation import calculate_correlations, CorrelationResult
from backend.analytics.patterns import detect_recurring_patterns, RecurringPattern
from backend.analytics.related_reports import find_related_reports, RelatedReport

# Part 3B Extensions
from backend.analytics.density import calculate_sif_density, DensityResult
from backend.analytics.dimensions import analyze_dimension, DimensionProfile
from backend.analytics.trends import calculate_trends, TrendResult
from backend.analytics.hotspots import detect_hotspots, HotspotResult

# Part 3C Extensions
from backend.analytics.barrier_analytics import calculate_barrier_frequency, extract_barrier_recurrence, get_barrier_detail_profile
from backend.analytics.barrier_trends import calculate_barrier_trends
from backend.analytics.bdi import calculate_bdi_for_barrier, calculate_all_bdi, BDI_METHODOLOGY_VERSION

# Part 3D Extensions
from backend.analytics.escalation import evaluate_entity_risk_escalation, detect_all_escalations, ESCALATION_METHODOLOGY_VERSION
from backend.analytics.prioritization import evaluate_analytical_priority, calculate_all_priorities, PRIORITY_METHODOLOGY_VERSION


class AnalyticsService:
    """Central analytics orchestrator service for Part 3A & Part 3B."""

    @staticmethod
    def _fetch_and_normalize_reports(
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        refinery_unit_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        work_type_filter: Optional[str] = None,
        report_type_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sif_only: Optional[bool] = None,
    ) -> List[AnalyticsReportDTO]:
        """Helper to retrieve authorized reports and apply normalization."""
        raw_dtos = get_analytics_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            refinery_unit_filter=refinery_unit_filter,
            department_filter=department_filter,
            report_type_filter=report_type_filter,
            start_date=start_date,
            end_date=end_date,
            sif_only=sif_only,
        )

        normalized_dtos = [normalize_report(dto) for dto in raw_dtos]

        if work_type_filter:
            normalized_dtos = [
                r for r in normalized_dtos 
                if r.normalized.get("work_type") == work_type_filter.lower().strip()
            ]

        return normalized_dtos

    # -------------------------------------------------------------
    # PART 3A MODULES
    # -------------------------------------------------------------
    @classmethod
    def get_recurring_patterns(
        cls,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        refinery_unit_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        work_type_filter: Optional[str] = None,
        min_support: int = ANALYTICS_MIN_PATTERN_COUNT,
    ) -> Dict[str, Any]:
        """Fetch recurring patterns meeting configured minimum support."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            refinery_unit_filter=refinery_unit_filter,
            department_filter=department_filter,
            work_type_filter=work_type_filter,
        )

        patterns = detect_recurring_patterns(reports, min_support=min_support)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "total_reports_analyzed": len(reports),
            "min_support_threshold": min_support,
            "patterns_count": len(patterns),
            "patterns": [p.__dict__ for p in patterns],
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_pattern_by_id(
        cls,
        pattern_id: str,
        db: Session,
        user: Optional[User] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch details for a specific pattern ID."""
        result = cls.get_recurring_patterns(db=db, user=user)
        for p_dict in result.get("patterns", []):
            if p_dict.get("pattern_id") == pattern_id:
                return p_dict
        return None

    @classmethod
    def get_related_reports(
        cls,
        report_id: int,
        db: Session,
        user: Optional[User] = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """Fetch analytically related reports for a target report_id."""
        reports = cls._fetch_and_normalize_reports(db=db, user=user)
        related = find_related_reports(
            target_report_id=report_id,
            reports=reports,
            max_results=max_results,
        )

        target_report = next((r for r in reports if r.report_id == report_id), None)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "target_report_id": report_id,
            "target_report_number": target_report.report_number if target_report else "UNKNOWN",
            "related_count": len(related),
            "related_reports": [r.__dict__ for r in related],
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_duplicates(
        cls,
        db: Session,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Fetch detected duplicate and near-duplicate groups."""
        reports = cls._fetch_and_normalize_reports(db=db, user=user)
        groups = detect_duplicates(reports)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "total_reports_analyzed": len(reports),
            "duplicate_groups_count": len(groups),
            "duplicate_groups": [g.__dict__ for g in groups],
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_correlations(
        cls,
        db: Session,
        user: Optional[User] = None,
        min_count: int = 2,
    ) -> Dict[str, Any]:
        """Fetch cross-report correlations."""
        reports = cls._fetch_and_normalize_reports(db=db, user=user)
        res: CorrelationResult = calculate_correlations(reports, min_count=min_count)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "total_reports_analyzed": res.total_reports_analyzed,
            "single_dimension_correlations": [item.__dict__ for item in res.single_dimension_correlations],
            "pairwise_correlations": [item.__dict__ for item in res.pairwise_correlations],
            "multi_factor_correlations": [item.__dict__ for item in res.multi_factor_correlations],
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------
    # PART 3B MODULES
    # -------------------------------------------------------------
    @classmethod
    def get_sif_density(
        cls,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        refinery_unit_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        work_type_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch descriptive SIF precursor density metrics."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            refinery_unit_filter=refinery_unit_filter,
            department_filter=department_filter,
            work_type_filter=work_type_filter,
            start_date=start_date,
            end_date=end_date,
        )

        res: DensityResult = calculate_sif_density(reports)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "density_metrics": res.__dict__,
            "calculated_at": res.calculated_at,
        }

    @classmethod
    def get_dimension_analytics(
        cls,
        dimension_name: str,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        refinery_unit_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        work_type_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch organizational dimension analytics (sites, activities, equipment, locations, departments, units)."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            refinery_unit_filter=refinery_unit_filter,
            department_filter=department_filter,
            work_type_filter=work_type_filter,
            start_date=start_date,
            end_date=end_date,
        )

        profiles: List[DimensionProfile] = analyze_dimension(reports, dimension_name)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "dimension": dimension_name,
            "total_reports_analyzed": len(reports),
            "profiles_count": len(profiles),
            "profiles": [p.__dict__ for p in profiles],
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_trends(
        cls,
        db: Session,
        user: Optional[User] = None,
        period_type: str = "month",
        date_preset: Optional[str] = None,
        custom_start_date: Optional[str] = None,
        custom_end_date: Optional[str] = None,
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch time-trend analytics by week, month, or quarter."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
        )

        res: TrendResult = calculate_trends(
            reports=reports,
            period_type=period_type,
            date_preset=date_preset,
            custom_start_date=custom_start_date,
            custom_end_date=custom_end_date,
        )

        return {
            "analytics_version": ANALYTICS_VERSION,
            "trend_data": {
                "period_type": res.period_type,
                "date_preset": res.date_preset,
                "start_date": res.start_date,
                "end_date": res.end_date,
                "total_periods": res.total_periods,
                "total_reports_analyzed": res.total_reports_analyzed,
                "trend_points": [tp.__dict__ for tp in res.trend_points],
                "calculated_at": res.calculated_at,
            },
            "calculated_at": res.calculated_at,
        }

    @classmethod
    def get_hotspots(
        cls,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """Fetch multi-dimensional hotspot analytics."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
        )

        res: HotspotResult = detect_hotspots(reports, max_results=max_results)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "total_reports_analyzed": res.total_reports_analyzed,
            "hotspots_count": res.hotspots_count,
            "hotspots": [h.__dict__ for h in res.hotspots],
            "calculated_at": res.calculated_at,
        }

    # -------------------------------------------------------------
    # PART 3C MODULES
    # -------------------------------------------------------------
    @classmethod
    def get_barrier_analytics(
        cls,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        refinery_unit_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch summary barrier intelligence and frequencies."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            refinery_unit_filter=refinery_unit_filter,
            department_filter=department_filter,
            start_date=start_date,
            end_date=end_date,
        )

        frequencies = calculate_barrier_frequency(reports)
        recurring = extract_barrier_recurrence(reports)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "bdi_methodology_version": BDI_METHODOLOGY_VERSION,
            "total_reports_analyzed": len(reports),
            "barrier_categories_count": len(frequencies),
            "barriers": frequencies,
            "recurring_barriers": recurring,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_barrier_detail(
        cls,
        barrier_category: str,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch detailed analytical profile for a specific barrier category."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
            start_date=start_date,
            end_date=end_date,
        )

        profile = get_barrier_detail_profile(barrier_category, reports)
        bdi_data = calculate_bdi_for_barrier(barrier_category, reports)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "bdi_methodology_version": BDI_METHODOLOGY_VERSION,
            "profile": profile,
            "bdi_summary": bdi_data,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_bdi(
        cls,
        db: Session,
        user: Optional[User] = None,
        barrier_category: Optional[str] = None,
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        trend_period: str = "month",
    ) -> Dict[str, Any]:
        """Fetch BDI_v1 scores and evidence payloads."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
            start_date=start_date,
            end_date=end_date,
        )

        if barrier_category:
            bdi_result = calculate_bdi_for_barrier(barrier_category, reports, trend_period=trend_period)
            return {
                "analytics_version": ANALYTICS_VERSION,
                "bdi_methodology_version": BDI_METHODOLOGY_VERSION,
                "total_reports_analyzed": len(reports),
                "bdi_result": bdi_result,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            bdi_results = calculate_all_bdi(reports, trend_period=trend_period)
            return {
                "analytics_version": ANALYTICS_VERSION,
                "bdi_methodology_version": BDI_METHODOLOGY_VERSION,
                "total_reports_analyzed": len(reports),
                "bdi_results": bdi_results,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def get_bdi_trends(
        cls,
        db: Session,
        user: Optional[User] = None,
        barrier_category: Optional[str] = None,
        period: str = "month",
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch time-series barrier trends and occurrence evolution."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
        )

        trends = calculate_barrier_trends(reports, period=period, barrier_category=barrier_category)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "bdi_methodology_version": BDI_METHODOLOGY_VERSION,
            "period_type": period,
            "barrier_category_filter": barrier_category,
            "total_reports_analyzed": len(reports),
            "trends": trends,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------
    # PART 3D MODULES
    # -------------------------------------------------------------
    @classmethod
    def get_escalation_analytics(
        cls,
        db: Session,
        user: Optional[User] = None,
        dimension_name: str = "equipment_id",
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch potential risk escalation indicators across entities."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
            start_date=start_date,
            end_date=end_date,
        )

        escalation_results = detect_all_escalations(reports, dimension_name=dimension_name)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "escalation_methodology_version": ESCALATION_METHODOLOGY_VERSION,
            "dimension": dimension_name,
            "total_reports_analyzed": len(reports),
            "escalations_count": len(escalation_results),
            "escalation_entities": escalation_results,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_escalation_detail(
        cls,
        entity_type: str,
        entity_id: str,
        db: Session,
        user: Optional[User] = None,
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch detailed risk escalation indicators for a specific entity."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
            start_date=start_date,
            end_date=end_date,
        )

        escalation_detail = evaluate_entity_risk_escalation(entity_type, entity_id, reports)
        priority_detail = evaluate_analytical_priority(entity_type, entity_id, reports)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "escalation_methodology_version": ESCALATION_METHODOLOGY_VERSION,
            "priority_methodology_version": PRIORITY_METHODOLOGY_VERSION,
            "escalation_detail": escalation_detail,
            "priority_detail": priority_detail,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_analytical_priorities(
        cls,
        db: Session,
        user: Optional[User] = None,
        dimension_name: str = "equipment_id",
        site_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch Analytical Priority Tiers (PRI_v1) across entities."""
        reports = cls._fetch_and_normalize_reports(
            db=db,
            user=user,
            site_filter=site_filter,
            department_filter=department_filter,
            start_date=start_date,
            end_date=end_date,
        )

        priority_results = calculate_all_priorities(reports, dimension_name=dimension_name)

        return {
            "analytics_version": ANALYTICS_VERSION,
            "priority_methodology_version": PRIORITY_METHODOLOGY_VERSION,
            "dimension": dimension_name,
            "total_reports_analyzed": len(reports),
            "priorities_count": len(priority_results),
            "priorities": priority_results,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }


