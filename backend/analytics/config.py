"""
Analytics Foundation Configuration (Part 3A)
"""

import os

# Minimum number of occurrences for a combination to be classified as a Recurring Pattern
ANALYTICS_MIN_PATTERN_COUNT = int(os.getenv("ANALYTICS_MIN_PATTERN_COUNT", "3"))

# Analytics Engine Versioning (distinct from ML model version)
ANALYTICS_VERSION = "safety_intelligence_v1"

# Cosine similarity threshold for description near-duplicate matching
SIMILARITY_THRESHOLD = float(os.getenv("ANALYTICS_SIMILARITY_THRESHOLD", "0.75"))

# Standard placeholder for missing/null analytical dimensions
MISSING_VALUE_PLACEHOLDER = "UNKNOWN"

# Primary dimensions evaluated in cross-report correlation & pattern detection
ANALYTICAL_DIMENSIONS = [
    "equipment_id",
    "activity",
    "work_type",
    "location",
    "refinery_unit",
    "department",
    "site",
    "report_type",
]

# Structured precursor flags evaluated in multi-factor correlation
PRECURSOR_DIMENSIONS = [
    "ppe_noncompliance",
    "supervisor_negligence",
    "maintenance_delay_or_issue",
    "repeated_issue_ignored",
]
