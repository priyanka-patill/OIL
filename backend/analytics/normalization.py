"""
Analytics Normalization Layer (Part 3A)

Ensures equivalent text and categorical values are grouped consistently
without modifying original database strings.
"""

import re
from typing import Optional
from backend.analytics.config import MISSING_VALUE_PLACEHOLDER, ANALYTICAL_DIMENSIONS
from backend.analytics.data_access import AnalyticsReportDTO


def normalize_text(val: Optional[str]) -> str:
    """
    Normalizes text for analytical grouping:
    1. Handles None, empty, or whitespace-only inputs -> 'UNKNOWN'
    2. Strips leading and trailing whitespace
    3. Replaces multiple internal spaces/newlines with a single space
    4. Converts to lowercase
    5. Preserves technical hyphens, numbers, and slashes (e.g., 'Pump A-101' is preserved as 'pump a-101')
    """
    if val is None:
        return MISSING_VALUE_PLACEHOLDER
    
    text = str(val).strip()
    if not text or text.upper() == MISSING_VALUE_PLACEHOLDER:
        return MISSING_VALUE_PLACEHOLDER

    # Collapse internal whitespace
    text = re.sub(r"\s+", " ", text)
    # Lowercase for canonical analytical matching
    normalized = text.lower()

    return normalized if normalized else MISSING_VALUE_PLACEHOLDER


def normalize_report(dto: AnalyticsReportDTO) -> AnalyticsReportDTO:
    """
    Populates the `normalized` dict on the AnalyticsReportDTO with canonical values.
    Original fields on dto remain unchanged.
    """
    norm_dict = {}
    for field_name in ANALYTICAL_DIMENSIONS:
        raw_val = getattr(dto, field_name, None)
        norm_dict[field_name] = normalize_text(raw_val)

    # Also normalize description
    norm_dict["description"] = normalize_text(dto.description)

    # Store normalized hazards and barriers
    norm_dict["hazards"] = [normalize_text(h) for h in dto.get_effective_hazards()]
    norm_dict["barriers"] = [normalize_text(b) for b in dto.get_effective_barriers()]
    norm_dict["lsrs"] = [normalize_text(l) for l in dto.get_effective_lsrs()]

    dto.normalized = norm_dict
    return dto
