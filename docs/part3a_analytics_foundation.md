# Part 3A — Analytics Foundation & Cross-Report Intelligence

## Overview

Part 3A establishes the core, multi-report analytical engine for the Oil India Limited (OIL) HSE Safety Intelligence Platform.
It shifts the analytical scope from evaluating single isolated reports to analyzing collections of safety reports across facilities, equipment, operational activities, and precursors.

---

## Architecture & Module Structure

The analytics infrastructure is implemented as a decoupled, service-layer package under `backend/analytics/`:

```
backend/
└── analytics/
    ├── __init__.py           # Package exports
    ├── config.py             # Central thresholds (min support, versioning)
    ├── data_access.py        # AnalyticsReportDTO & RBAC pre-filtered DB queries
    ├── normalization.py     # Reversible text/categorical canonicalization
    ├── duplicates.py        # Exact, near-duplicate & similarity grouping
    ├── correlation.py       # Single, pairwise & multi-factor correlation engine
    ├── patterns.py          # Recurring pattern detector with support thresholds
    ├── related_reports.py   # Target report matching & evidence explanation
    └── service.py           # Central orchestrator service
```

---

## Key Functional Capabilities

### 1. RBAC-Aware Pre-Filtering & Security
- Authorization filtering is strictly applied **before** data aggregation.
- An `HSE_USER` assigned to `Digboi Refinery` can only aggregate patterns from reports originating within `Digboi Refinery`. Restricted site or department records are completely excluded prior to correlation, eliminating aggregate data leakage.

### 2. Normalization Engine
- Performs case-folding and whitespace stripping while keeping original database text fields untouched.
- Handles missing or empty values as explicit `"UNKNOWN"` dimensions rather than dropping records or treating missing equipment as universal equipment.
- Preserves technical hyphens, numbers, and identifiers (e.g., `Pump A-101` remains distinct from `Pump A101`).

### 3. Duplicate & Near-Duplicate Detection
- **Level 1 (Exact)**: Matches canonical report numbers or exact normalized content fingerprints (`date`, `site`, `location`, `equipment_id`, `activity`, `description`).
- **Level 2 (Near-Duplicate)**: TF-IDF cosine text similarity on descriptions exceeding `0.75` threshold.
- **Level 3 (Potentially Similar)**: Shared structured dimensions.
- **Non-Destructive**: Never alters or deletes source report records in the database.

### 4. Cross-Report Correlation & Pattern Detection
- Identifies single-dimension, pairwise, and multi-factor recurrences across equipment, activity, work type, location, hazards, barriers, and precursors.
- Configurable minimum support threshold (`ANALYTICS_MIN_PATTERN_COUNT`, default `3`).
- Single occurrences are categorized as `Observed Combination` and excluded from `Recurring Pattern` outputs.
- Maintains complete separation between **AI SIF counts** and **HSE-validated SIF counts**.

### 5. Evidence-Backed Related Reports & Traceability
- Given any `report_id`, finds related reports with explicit evidence explanations (e.g., `Matching Equipment: Pump P-101`, `Matching Activity: Seal Replacement`, `Shared Barrier: Energy Isolation`).
- Every pattern links directly to contributing report IDs (`Pattern -> Contributing Report IDs -> Individual Report`).

### 6. Data Leakage Immunity
- `source_sheet` and `"12_High_Potential"` are strictly excluded from all fingerprinting, text similarity, correlation, and pattern algorithms.

---

## API Endpoints

- `GET /api/analytics/patterns`: Fetch recurring patterns with query filters (`site`, `refinery_unit`, `department`, `work_type`, `min_support`).
- `GET /api/analytics/patterns/{pattern_id}`: Fetch detailed breakdown for a specific pattern ID.
- `GET /api/analytics/related-reports/{report_id}`: Fetch related reports with evidence explanations for a target report.
- `GET /api/analytics/duplicates`: Fetch detected exact and near-duplicate groups.
- `GET /api/analytics/correlation`: Fetch top correlated dimension pairs and tuples.
