# Technical Documentation: Data Integrity & Authoritative Dashboard Aggregations

## Overview

This document defines the mathematical, architectural, and data model rules governing all operational metrics, Action Center summary counts, and safety analytics across the **Oil India Limited (OIL) HSE Safety Intelligence Platform**.

---

## 1. Primary Directives & Principles

1. **Backend-Authoritative Aggregations**:
   The frontend UI does **NOT** compute, estimate, or hardcode KPI counters. All dashboard numbers are fetched directly from authorized backend REST endpoints (`/api/action-center/summary`, `/api/action-center/sections`, `/api/analytics/*`).

2. **Zero Mock or Fabricated Numbers**:
   No random numbers (`Math.random()`), fallback constants (`|| 3`), or mock data are used in production routines. When zero records exist, the UI displays `0`. On API failures, explicit error banners are shown rather than silent fake fallbacks.

3. **Distinct Entity Counting**:
   Child history rows, audit logs, SLA event logs, and historical impact snapshots must **NEVER** multiply parent entity counts. All SQL summary queries enforce `func.count(func.distinct(Entity.id))`.

4. **Strict Site & Role-Based Access Control (RBAC)**:
   Scoping by `site` and `department` is enforced at the database query level prior to aggregation. Non-admin users cannot infer counts from unauthorized sites.

---

## 2. KPI Calculation Definitions & SQL Semantics

| KPI Metric Name | Primary Database Entity | Status & Filter Rules | SQL Aggregation Rule |
| :--- | :--- | :--- | :--- |
| **Total Safety Reports** | `SafetyReport` | Filtered by authorized site/user | `COUNT(DISTINCT safety_reports.id)` |
| **Pending HSE Reviews** | `InterventionRecommendation` | `status = 'PENDING_HSE_VALIDATION'` | `COUNT(DISTINCT intervention_recommendations.id)` |
| **Active Operational Actions** | `Action` | `status IN ('ASSIGNED', 'IN_PROGRESS', 'ON_HOLD', 'REOPENED')` | `COUNT(DISTINCT actions.id)` |
| **Due Soon Actions** | `ActionSLA` & `Action` | `ActionSLA.sla_status = 'DUE_SOON'` AND Action is Active | `COUNT(DISTINCT actions.id)` |
| **Overdue Actions** | `ActionSLA` & `Action` | `ActionSLA.sla_status = 'OVERDUE'` AND Action is Active | `COUNT(DISTINCT actions.id)` |
| **Completed Actions** | `Action` | `status = 'COMPLETED'` | `COUNT(DISTINCT actions.id)` |
| **Verification Pending** | `Action` | `status = 'VERIFICATION_PENDING'` | `COUNT(DISTINCT actions.id)` |
| **Verified Actions** | `Action` | `status = 'VERIFIED'` | `COUNT(DISTINCT actions.id)` |
| **Impact Available** | `ActionImpactAnalysis` & `Action` | `data_sufficiency_status = 'SUFFICIENT'` | `COUNT(DISTINCT actions.id)` |
| **Insufficient Data** | `ActionImpactAnalysis` & `Action` | `data_sufficiency_status = 'INSUFFICIENT_DATA'` | `COUNT(DISTINCT actions.id)` |

---

## 3. Prevention of Duplicate & Multiplied Counts

### Root Cause Analysis of Multiplied Counts
- **Join Multiplication**: Joining `Action` to `ActionImpactAnalysis` (which can contain multiple historical snapshot versions for the same action) can produce duplicate rows if using simple `count()`.
- **Resolution**: Every endpoint in `backend/api/action_center.py` calls `.with_entities(func.count(func.distinct(Action.id))).scalar()`, guaranteeing 1 action is counted exactly once regardless of snapshot history length.

---

## 4. Cache & State Refresh Behavior

- On submitting a safety report, reviewing an intervention, completing an action, or verifying an action, frontend state triggers invalidation and refetches `fetchAllData()`.
- Re-running seed scripts or starting backend processes is strictly idempotent and does not accumulate duplicate seed rows.
