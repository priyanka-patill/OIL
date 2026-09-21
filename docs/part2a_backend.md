# OIL SIF Precursor Detection System — Part 2A Backend Architecture

This document details the backend foundation, database ORM models, authentication system, role-based access control (RBAC), and API specifications implemented in **Part 2A** for Oil India Limited (OIL).

---

## 1. Architecture & Technology Stack

```
                     User / API Client
                             │
                             ▼
              FastAPI Engine (backend/main.py)
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     Authentication    Role Authorization   Pydantic Settings
   (bcrypt + PyJWT)  (HSE_USER/MANAGER/ADMIN)  (backend/config.py)
            │                │                │
            └────────────────┼────────────────┘
                             │
                             ▼
                    Service Layer & ORM
              (SQLAlchemy ORM + SQLite app.db)
            ┌────────────────┬────────────────┐
            ▼                ▼                ▼
      Safety Reports     HSE Reviews      Audit Logs
```

- **Framework**: FastAPI (Python 3.10+)
- **ASGI Server**: Uvicorn
- **ORM & Database**: SQLAlchemy ORM with SQLite (`data/app.db`) for development
- **Security & Passwords**: Passlib with `bcrypt`
- **Tokens**: PyJWT (JSON Web Tokens signed with HS256)
- **Validation**: Pydantic v2 & Pydantic Settings

---

## 2. Database Schema & ER Diagram

```
User (users)
  │
  ├───< SafetyReport (safety_reports)
  │       │
  │       ├───< AIAnalysis (ai_analyses) [Reserved for Part 2C]
  │       │
  │       └───< HSEReview (hse_reviews)
  │
  └───< AuditLog (audit_logs)
```

### Table Definitions

1. **`users`**:
   - `id` (PK), `name`, `email` (unique index), `password_hash`, `role` (`HSE_USER`, `HSE_MANAGER`, `ADMIN`), `department`, `site`, `is_active`, `created_at`, `updated_at`.

2. **`safety_reports`**:
   - `id` (PK), `report_number` (unique index, format `OIL-2026-000001`), `created_by` (FK -> `users.id`), `report_type` (`UNSAFE_ACT`, `UNSAFE_CONDITION`, `NEAR_MISS`, `INCIDENT`), `date`, `site`, `refinery_unit`, `location`, `equipment_id`, `work_type`, `activity`, `department`, `description`, precursor boolean flags (`ppe_noncompliance`, `supervisor_negligence`, `maintenance_delay_or_issue`, `repeated_issue_ignored`, `previous_similar_reports`), post-investigation fields (`immediate_cause`, `potential_consequence`, `risk_level`, `corrective_action`, `action_status`), `status` (`DRAFT`, `SUBMITTED`, `AI_ANALYZED`, `HSE_REVIEW_PENDING`, `HSE_VALIDATED`, `ACTION_REQUIRED`, `CLOSED`).

3. **`ai_analyses`** *(Reserved for Part 2C ML integration)*:
   - `id` (PK), `report_id` (FK -> `safety_reports.id`), `model_version`, `prediction`, `classification`, `probability_or_score`, `threshold`, `explanation_json`, `life_saving_rules_json`, `hazards_json`, `barrier_concerns_json`, `analysis_status`, `created_at`.

4. **`hse_reviews`**:
   - `id` (PK), `report_id` (FK -> `safety_reports.id`), `reviewer_id` (FK -> `users.id`), `ai_prediction_accepted`, `hse_decision` (`PENDING`, `ACCEPTED`, `MODIFIED`, `REJECTED`), `modified_classification`, `review_comment`, `reviewed_at`.

5. **`audit_logs`**:
   - `id` (PK), `user_id` (FK -> `users.id`), `action` (`LOGIN_SUCCESS`, `REPORT_CREATED`, `REPORT_UPDATED`, `HSE_REVIEW_CREATED`, etc.), `entity_type`, `entity_id`, `metadata_json`, `timestamp`.

---

## 3. Role-Based Access Control (RBAC) Permission Matrix

| Role | Submit Reports | View Reports | Update Reports | Submit HSE Reviews | Admin Users & Audit Logs |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`HSE_USER`** | ✅ Yes | ✅ Own/Permitted | ✅ Own/Drafts | ❌ No | ❌ No |
| **`HSE_MANAGER`** | ✅ Yes | ✅ All Site Reports | ✅ All Reports | ✅ Yes (Accept/Modify/Reject) | ❌ No |
| **`ADMIN`** | ✅ Yes | ✅ All Reports | ✅ All Reports | ✅ Yes | ✅ Full Access |

---

## 4. API Endpoint Summary

### Authentication (`/api/auth`)
- `POST /api/auth/signup`: Public user registration (defaults strictly to `HSE_USER`).
- `POST /api/auth/login`: Authenticates credentials and returns Bearer JWT access token.
- `POST /api/auth/logout`: Logs out current user and records audit log.
- `GET /api/auth/me`: Returns current authenticated user profile.

### Safety Reports (`/api/reports`)
- `POST /api/reports`: Creates a new safety observation report. Generates unique report number.
- `GET /api/reports`: List safety reports with search, site, type, status, department filters & pagination.
- `GET /api/reports/{id}`: Get single report details.
- `PUT /api/reports/{id}`: Update safety report.

### HSE Reviews (`/api/reports/{id}/review`)
- `POST /api/reports/{id}/review`: Submit HSE review decision (`ACCEPTED`, `MODIFIED`, `REJECTED`). Requires `HSE_MANAGER` or `ADMIN`.
- `GET /api/reports/{id}/review`: Get review history for a report.

### Admin Management (`/api/admin`)
- `GET /api/admin/users`: List system users. Requires `ADMIN`.
- `PUT /api/admin/users/{user_id}`: Update user role, site, department, or active status. Requires `ADMIN`.
- `GET /api/admin/audit-logs`: Query structured audit logs with filtering. Requires `ADMIN`.

### System Health
- `GET /health`: Health check endpoint returning `{"status": "ok", "environment": "development", "database": "healthy"}`.

---

## 5. Part 1C ML Compatibility Field Mapping

| Web / API Report Field | Part 1C ML Input Field | Description |
| :--- | :--- | :--- |
| `description` | `Near_Miss_Description` | Free-text safety observation logged by worker/observer. |
| `refinery_unit` | `Refinery_Unit` | Operational refinery location unit. |
| `equipment_id` | `Equipment_ID` | Tag identifier of involved equipment. |
| `work_type` | `Work_Type` | Operational task category. |
| `department` | `Department` | Reporting department. |
| `ppe_noncompliance` | `PPE_NonCompliance` | Precursor flag. |
| `supervisor_negligence` | `Supervisor_Negligence` | Precursor flag. |
| `maintenance_delay_or_issue` | `Maintenance_Delay_or_Issue` | Precursor flag. |
| `repeated_issue_ignored` | `Repeated_Issue_Ignored` | Precursor flag. |
| `previous_similar_reports` | `Previous_Similar_Reports` | Historical site incident count. |

> [!WARNING]
> **Source Sheet & Target Leakage Safeguard**: `source_sheet` is strictly excluded from prediction inputs. `predict_sif()` automatically strips `source_sheet` and post-investigation fields if passed.

---

## 6. How to Run & Test Part 2A

### 1. Seed Development Database
```powershell
python -m backend.seed
```

### 2. Run Backend Uvicorn Dev Server
```powershell
uvicorn backend.main:app --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc API Spec: `http://localhost:8000/redoc`

### 3. Run Backend Unit Tests
```powershell
python -m unittest discover -s tests -p "test_backend_*.py"
```
