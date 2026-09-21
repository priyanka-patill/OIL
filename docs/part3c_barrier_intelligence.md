# Part 3C — Barrier Intelligence & Barrier Degradation Index Technical Architecture

**Project**: Oil India Limited (OIL) HSE Safety Intelligence Platform  
**Target Scope**: Part 3C Architecture, Data Flow, Taxonomy Mapping, APIs & Testing  
**Date**: September 17, 2026

---

## 1. Overview & Objectives

Part 3C extends the OIL HSE Safety Intelligence Platform with **Barrier Intelligence & Barrier Degradation Index (BDI_v1)**. It provides structured insights into safety barrier weaknesses, recurring degradation patterns, cross-dimension co-occurrences, time-series trends, and sample-guarded BDI scoring based on authoritative database records, AI analysis, and HSE-in-the-loop review data.

---

## 2. Module & Code Structure

| Module Path | Core Function |
| :--- | :--- |
| [`backend/analytics/data_access.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/data_access.py) | Updates `AnalyticsReportDTO` to include `action_status` for unresolved report tracking. |
| [`backend/analytics/barrier_normalization.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/barrier_normalization.py) | Maps free-text concerns & Part 2C flags to canonical categories while preserving original text. |
| [`backend/analytics/barrier_analytics.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/barrier_analytics.py) | Extracts barrier occurrences, counts frequency, detects recurrence, and builds cross-dimension profiles. |
| [`backend/analytics/barrier_trends.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/barrier_trends.py) | Computes time-series trends (Weekly, Monthly, Quarterly) for barrier occurrences. |
| [`backend/analytics/bdi.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/bdi.py) | Evaluates sample size ($n \ge 3$), computes BDI scores ($0\text{--}100$), and generates evidence payloads. |
| [`backend/analytics/service.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/service.py) | Exposes Part 3C methods via the unified `AnalyticsService` façade. |
| [`backend/api/analytics.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/api/analytics.py) | Exposes REST endpoints (`/api/analytics/barriers`, `/bdi`, `/bdi/trends`) with JWT auth & RBAC filters. |
| [`tests/test_part3c_barrier_analytics.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/tests/test_part3c_barrier_analytics.py) | Comprehensive test suite for Part 3C features, leakage regression, and API verification. |

---

## 3. Data Flow Architecture

```
[ Database: SafetyReport + AIAnalysis + HSEReview ]
                        │
                        ▼
    [ backend/analytics/data_access.py ] ── Enforces RBAC & loads AnalyticsReportDTO
                        │
                        ▼
 [ backend/analytics/barrier_normalization.py ] ── Standardizes free-text & Part 2C flags
                        │
                        ▼
   [ backend/analytics/barrier_analytics.py ] ── Extracts occurrence matrix (1/report/category)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
[ backend/analytics/barrier_trends.py ]  [ backend/analytics/bdi.py ]
(Weekly/Monthly/Quarterly series)      (Sample check n >= 3, component scoring R, P, U, S, T)
         │                             │
         └──────────────┬──────────────┘
                        ▼
    [ backend/analytics/service.py ] ── Unified Analytics Façade
                        │
                        ▼
      [ backend/api/analytics.py ] ── REST API Endpoints with BDI_v1 tag
```

---

## 4. API Specification

### 1. `GET /api/analytics/barriers`
Returns a summary list of all barrier categories with occurrences, unique report counts, SIF-Potential counts, unresolved counts, recurrence status, and BDI summaries.

### 2. `GET /api/analytics/barriers/{barrier_category}`
Returns a detailed analytical profile for a specific barrier category, including cross-dimension breakdowns (Site, Activity, Equipment, Department, Location), AI vs. HSE review distinctions, and contributing report IDs.

### 3. `GET /api/analytics/bdi`
Returns detailed BDI metrics for all barriers or a specific filtered barrier, including BDI score ($0\text{--}100$), sample sufficiency status (`SUFFICIENT_DATA`, `LIMITED_DATA`, `INSUFFICIENT_DATA`), component scores ($R, P, U, S, T_{\text{adj}}$), methodology version `BDI_v1`, and limitations.

### 4. `GET /api/analytics/bdi/trends`
Returns time-series evolution of BDI scores and occurrence counts across Weekly, Monthly, or Quarterly intervals with date range filters (`7d`, `30d`, `90d`, `6m`, `12m`, custom).

---

## 5. Security, RBAC & Leakage Protection

- **RBAC Scope Filter**: Enforced at the database query level prior to analytics extraction. Users with `HSE_USER` role only see analytics for their assigned site and department.
- **Zero Leakage**: `source_sheet` and `"12_High_Potential"` are strictly 100% excluded from all logic. Mandatory automated regression tests guarantee zero leakage impact.
- **Auditability**: Every BDI output includes `contributing_report_ids`, `calculated_at` timestamps, and `BDI_v1` version tags.
