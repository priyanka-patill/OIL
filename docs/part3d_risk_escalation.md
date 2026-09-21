# Part 3D — Potential Risk Escalation & Analytical Prioritization Technical Architecture

**Project**: Oil India Limited (OIL) HSE Safety Intelligence Platform  
**Target Scope**: Part 3D Architecture, Data Flow, Indicator Formulas, APIs & Verification  
**Date**: September 17, 2026

---

## 1. Overview & Objectives

Part 3D extends the OIL HSE Safety Intelligence Platform with **Potential Risk Escalation (`RE_v1`)** and **Analytical Prioritization (`PRI_v1`)**. It provides non-predictive, evidence-backed indicators showing whether safety precursor issues are persistent, repeatedly observed, unresolved, recurring across barriers, or showing concerning time-series changes across organizational entities (Equipment, Site, Activity, Department, Location).

---

## 2. Module & Code Structure

| Module Path | Core Function |
| :--- | :--- |
| [`backend/analytics/escalation.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/escalation.py) | Evaluates 6 risk escalation evidence indicators and small-sample protection ($n < 3$). |
| [`backend/analytics/prioritization.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/prioritization.py) | Assigns Analytical Priority Tiers (`PRI_v1`) combining SIF density, BDI, and active escalation flags. |
| [`backend/analytics/service.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/analytics/service.py) | Exposes Part 3D risk escalation and priority methods through the unified `AnalyticsService` façade. |
| [`backend/api/analytics.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/backend/api/analytics.py) | Exposes REST endpoints (`/api/analytics/escalation`, `/priorities`, `/priorities/trends`) with JWT auth & RBAC. |
| [`tests/test_part3d_risk_escalation.py`](file:///c:/Users/ASUS/OneDrive/Desktop/ps2/tests/test_part3d_risk_escalation.py) | Comprehensive test suite for Part 3D features, leakage regression, and API verification. |

---

## 3. Data Flow Architecture

```
[ Database: SafetyReport + AIAnalysis + HSEReview ]
                        │
                        ▼
    [ backend/analytics/data_access.py ] ── Enforces RBAC & loads AnalyticsReportDTO
                        │
                        ▼
    [ backend/analytics/escalation.py ] ── Evaluates 6 Risk Escalation Indicators (RE_v1)
                        │
                        ▼
  [ backend/analytics/prioritization.py ] ── Assigns Analytical Priority Tiers (PRI_v1)
                        │
                        ▼
    [ backend/analytics/service.py ] ── Unified Analytics Façade
                        │
                        ▼
      [ backend/api/analytics.py ] ── REST API Endpoints with RE_v1 & PRI_v1 tags
```

---

## 4. API Specification

### 1. `GET /api/analytics/escalation`
Returns summary of potential risk escalation indicators across entities (equipment, site, activity, department, location).

### 2. `GET /api/analytics/escalation/{entity_type}/{entity_id}`
Returns detailed risk escalation profile for a specific entity with 6 evidence indicators and contributing report IDs.

### 3. `GET /api/analytics/priorities`
Returns Analytical Priority indicators (`PRI_v1`) across entities along with supporting evidence payloads.

### 4. `GET /api/analytics/priorities/trends`
Returns time-series evolution of potential risk escalation indicators across Weekly, Monthly, or Quarterly intervals with date range filters.

---

## 5. Security & Data Leakage Protection

- **RBAC Scope Enforcement**: Pre-filtering applied at database query layer.
- **Zero Data Leakage**: `source_sheet` and `"12_High_Potential"` are 100% excluded. Automated regression tests verify zero impact.
- **Full Traceability**: Every escalation output includes `contributing_report_ids`, `calculated_at` timestamps, and `RE_v1` / `PRI_v1` version metadata tags.
