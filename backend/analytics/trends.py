"""
Time-Trend Analytics Engine (Part 3B)

Calculates temporal trends across weekly, monthly, and quarterly periods
with configurable date-range presets, custom date validation, and contributing report traceability.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone

from backend.analytics.data_access import AnalyticsReportDTO
from backend.analytics.density import calculate_sif_density


@dataclass
class TrendPoint:
    """Detailed summary metrics for a specific time period."""

    period_type: str  # week, month, quarter
    period_key: str   # e.g., '2026-W04', '2026-01', '2026-Q1'
    start_date: str
    end_date: str
    total_reports: int
    eligible_analyzed_reports: int
    ai_sif_count: int
    ai_sif_density: Optional[float]
    hse_validated_sif_count: int
    hse_validated_sif_density: Optional[float]
    data_sufficiency: str
    contributing_report_ids: List[int] = field(default_factory=list)


@dataclass
class TrendResult:
    """Aggregated trend analysis response."""

    period_type: str
    date_preset: Optional[str]
    start_date: str
    end_date: str
    total_periods: int
    total_reports_analyzed: int
    trend_points: List[TrendPoint]
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """Safely parse ISO date string (YYYY-MM-DD)."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def get_preset_date_range(preset: str) -> Tuple[datetime, datetime]:
    """
    Returns (start_date, end_date) for common presets:
    7d, 30d, 90d, 6m, 12m.
    """
    now = datetime.now(timezone.utc)
    end_dt = now

    preset_lower = preset.lower().strip()
    if preset_lower == "7d":
        start_dt = now - timedelta(days=7)
    elif preset_lower == "30d":
        start_dt = now - timedelta(days=30)
    elif preset_lower == "90d":
        start_dt = now - timedelta(days=90)
    elif preset_lower == "6m":
        start_dt = now - timedelta(days=180)
    elif preset_lower == "12m":
        start_dt = now - timedelta(days=365)
    else:
        # Default to 90d if unknown preset
        start_dt = now - timedelta(days=90)

    return start_dt, end_dt


def get_period_key(dt: datetime, period_type: str) -> str:
    """Returns period key format: YYYY-Www, YYYY-MM, or YYYY-Qx."""
    if period_type == "week":
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    elif period_type == "quarter":
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"
    else:  # month
        return f"{dt.year}-{dt.month:02d}"


def calculate_trends(
    reports: List[AnalyticsReportDTO],
    period_type: str = "month",
    date_preset: Optional[str] = None,
    custom_start_date: Optional[str] = None,
    custom_end_date: Optional[str] = None,
) -> TrendResult:
    """
    Groups reports by time period (week, month, quarter) and calculates density trends.
    Applies preset or custom date range filtering.
    """
    period_clean = period_type.lower().strip()
    if period_clean not in ("week", "month", "quarter"):
        period_clean = "month"

    # Filter reports by date range if provided
    filtered_reports = list(reports)
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    if date_preset:
        start_dt, end_dt = get_preset_date_range(date_preset)
    elif custom_start_date or custom_end_date:
        if custom_start_date:
            start_dt = parse_iso_date(custom_start_date)
            if not start_dt:
                raise ValueError(f"Invalid custom_start_date format: '{custom_start_date}'. Use YYYY-MM-DD.")
        if custom_end_date:
            end_dt = parse_iso_date(custom_end_date)
            if not end_dt:
                raise ValueError(f"Invalid custom_end_date format: '{custom_end_date}'. Use YYYY-MM-DD.")

        if start_dt and end_dt and start_dt > end_dt:
            raise ValueError("custom_start_date cannot be greater than custom_end_date.")

    if start_dt or end_dt:
        start_str = start_dt.strftime("%Y-%m-%d") if start_dt else "0000-01-01"
        end_str = end_dt.strftime("%Y-%m-%d") if end_dt else "9999-12-31"
        filtered_reports = [
            r for r in filtered_reports
            if r.date and (start_str <= r.date[:10] <= end_str)
        ]

    # Group reports by period_key
    grouped: Dict[str, List[AnalyticsReportDTO]] = {}
    for r in filtered_reports:
        r_dt = parse_iso_date(r.date)
        if not r_dt:
            continue
        key = get_period_key(r_dt, period_clean)
        grouped.setdefault(key, []).append(r)

    period_keys = sorted(list(grouped.keys()))
    trend_points: List[TrendPoint] = []

    for key in period_keys:
        bucket = grouped[key]
        density_res = calculate_sif_density(bucket)

        dates = [r.date for r in bucket if r.date]
        dates.sort()
        p_start = dates[0] if dates else key
        p_end = dates[-1] if dates else key
        bucket_report_ids = [r.report_id for r in bucket]

        tp = TrendPoint(
            period_type=period_clean,
            period_key=key,
            start_date=p_start,
            end_date=p_end,
            total_reports=density_res.total_reports,
            eligible_analyzed_reports=density_res.eligible_analyzed_reports,
            ai_sif_count=density_res.ai_sif_potential_count,
            ai_sif_density=density_res.ai_sif_precursor_density,
            hse_validated_sif_count=density_res.hse_sif_validated_count,
            hse_validated_sif_density=density_res.hse_sif_precursor_density,
            data_sufficiency=density_res.data_sufficiency,
            contributing_report_ids=bucket_report_ids,
        )
        trend_points.append(tp)

    overall_start = trend_points[0].start_date if trend_points else (start_dt.strftime("%Y-%m-%d") if start_dt else "ALL")
    overall_end = trend_points[-1].end_date if trend_points else (end_dt.strftime("%Y-%m-%d") if end_dt else "ALL")

    return TrendResult(
        period_type=period_clean,
        date_preset=date_preset,
        start_date=overall_start,
        end_date=overall_end,
        total_periods=len(trend_points),
        total_reports_analyzed=len(filtered_reports),
        trend_points=trend_points,
        calculated_at=datetime.now(timezone.utc).isoformat(),
    )
