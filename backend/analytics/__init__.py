"""
OIL HSE Safety Intelligence Platform - Analytics Engine (Part 3A & Part 3B)
"""

from backend.analytics.config import (
    ANALYTICS_MIN_PATTERN_COUNT,
    ANALYTICS_VERSION,
    SIMILARITY_THRESHOLD,
    MISSING_VALUE_PLACEHOLDER,
)
from backend.analytics.data_access import AnalyticsReportDTO, get_analytics_reports
from backend.analytics.normalization import normalize_text, normalize_report
from backend.analytics.duplicates import detect_duplicates, DuplicateGroup
from backend.analytics.correlation import calculate_correlations, CorrelationResult
from backend.analytics.patterns import detect_recurring_patterns, RecurringPattern
from backend.analytics.related_reports import find_related_reports, RelatedReport

# Part 3B Extensions
from backend.analytics.density import calculate_sif_density, DensityResult, get_data_sufficiency_status
from backend.analytics.dimensions import analyze_dimension, DimensionProfile
from backend.analytics.trends import calculate_trends, TrendResult, TrendPoint
from backend.analytics.hotspots import detect_hotspots, HotspotResult, HotspotItem

from backend.analytics.service import AnalyticsService

__all__ = [
    "ANALYTICS_MIN_PATTERN_COUNT",
    "ANALYTICS_VERSION",
    "SIMILARITY_THRESHOLD",
    "MISSING_VALUE_PLACEHOLDER",
    "AnalyticsReportDTO",
    "get_analytics_reports",
    "normalize_text",
    "normalize_report",
    "detect_duplicates",
    "DuplicateGroup",
    "calculate_correlations",
    "CorrelationResult",
    "detect_recurring_patterns",
    "RecurringPattern",
    "find_related_reports",
    "RelatedReport",
    # Part 3B Exports
    "calculate_sif_density",
    "DensityResult",
    "get_data_sufficiency_status",
    "analyze_dimension",
    "DimensionProfile",
    "calculate_trends",
    "TrendResult",
    "TrendPoint",
    "detect_hotspots",
    "HotspotResult",
    "HotspotItem",
    "AnalyticsService",
]
