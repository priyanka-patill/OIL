# Part 3B — Hotspots, SIF Density & Trend Analytics

## Overview

Part 3B extends the Part 3A analytics engine to provide organizational-level insights for Oil India Limited (OIL) HSE safety operations.
It addresses the central operational question:

> **"Where are SIF precursors repeatedly appearing across sites, facilities, equipment, activities, and operational departments?"**

All metrics are calculated dynamically from stored database records and Part 3A normalized DTOs without introducing second ML classifiers, risk escalation scores, or probability estimates.

---

## Architecture & Module Additions

Part 3B extends `backend/analytics/` with the following specialized modules:

```
backend/
└── analytics/
    ├── density.py       # SIF Precursor Density & Data Sufficiency Engine
    ├── dimensions.py    # Organizational Dimension Profiles (Sites, Activities, Equipment, Locations, Departments, Units)
    ├── trends.py        # Time-Trend Analytics (Weekly, Monthly, Quarterly) & Date Filters
    └── hotspots.py      # Multi-Dimensional Concentration Analysis & Evidence Generation
```

---

## Key Functional Capabilities

### 1. SIF Precursor Density Engine
- **Descriptive Ratio**: `SIF Precursor Density = SIF-Potential Reports / Eligible Analyzed Reports`.
- **Eligible Analyzed Report**: Defined as a safety report possessing a valid AI SIF analysis (`has_ai_analysis == True`).
- **Zero-Denominator Handling**: If `eligible_analyzed_reports == 0`, `density = None` and `data_sufficiency = "NOT_AVAILABLE"`.
- **Small-Sample Protection**: Communicates dataset confidence via explicit data sufficiency indicators:
  - `SUFFICIENT`: >= 10 analyzed reports.
  - `LIMITED`: 3 to 9 analyzed reports.
  - `INSUFFICIENT`: 1 to 2 analyzed reports.
  - `NOT_AVAILABLE`: 0 analyzed reports.
- Maintains strict separation between **AI SIF density** and **HSE-validated SIF density**.

### 2. Organizational Dimension Analytics
- Generates analytical profiles across 6 primary dimensions:
  1. `Site` (e.g. Digboi Refinery, Duliajan HQ)
  2. `Activity` (e.g. Seal Replacement, Hot Work, Inspection)
  3. `Equipment` (e.g. Pump P-101, Boiler B-500)
  4. `Location` (e.g. Cracker Plant, Substation 1)
  5. `Department` (e.g. Mechanical, Operations, Electrical)
  6. `Refinery Unit` (e.g. Unit 1, Unit 3, HQ Main)
- Each profile provides total reports, analyzed counts, SIF counts, density, data sufficiency status, common hazards, common barriers, co-occurring activities/equipment, and contributing report references.

### 3. Time-Trend Analytics
- Aggregates report volume, analyzed volume, SIF counts, and precursor density across `week` (ISO `YYYY-Www`), `month` (`YYYY-MM`), or `quarter` (`YYYY-Qx`).
- Supports preset date ranges (`7d`, `30d`, `90d`, `6m`, `12m`) and custom `start_date` / `end_date` ranges with strict validation.

### 4. Hotspot Analysis & Non-Punitive Evidence
- Identifies multi-dimensional concentrations combining raw report volume, SIF precursor density, and Part 3A recurring pattern co-occurrences.
- Employs objective, evidence-backed terminology (`"Analytical Hotspot"`, `"Observed Concentration"`). Strictly avoids punitive labels (`"Worst Site"`, `"Most Dangerous"`).

### 5. RBAC Security & Leakage Protection
- Applies RBAC site and department authorization **before** data aggregation to ensure `HSE_USER` accounts cannot access or aggregate data outside their authorized scope.
- `source_sheet` and `"12_High_Potential"` are strictly excluded from all density, trend, hotspot, and dimension calculations.

---

## API Specification

- `GET /api/analytics/density`: SIF precursor density summary and raw counts.
- `GET /api/analytics/sites`: Site profile analytics.
- `GET /api/analytics/activities`: Activity profile analytics.
- `GET /api/analytics/equipment`: Equipment profile analytics.
- `GET /api/analytics/locations`: Location profile analytics.
- `GET /api/analytics/departments`: Department profile analytics.
- `GET /api/analytics/refinery-units`: Refinery Unit profile analytics.
- `GET /api/analytics/trends`: Temporal trends by `week`, `month`, or `quarter`.
- `GET /api/analytics/hotspots`: Multi-dimensional concentration analysis.
