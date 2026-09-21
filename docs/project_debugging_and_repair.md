# Project Debugging, Audit & Repair Summary

## 1. Root Cause of Registration HTTP 404 Error
During user registration on the frontend, attempts to create an account resulted in `Request failed with status code 404`.

### Technical Investigation Findings:
- **Port Conflict / Lingering Process**: A background process (`PID 3644`) was bound to `127.0.0.1:8000`, intercepting requests sent to `http://localhost:8000` or `http://127.0.0.1:8000`. This lingering process was serving an old service that did NOT mount `/api/auth` endpoints.
- **Resolution**: Identified process binding via `netstat -ano`, terminated the conflicting process (`PID 3644`), and bound `backend.main:app` cleanly to `127.0.0.1:8000`.

## 2. API Prefix and Contract Alignment
- Backend router registration in `backend/main.py`: `app.include_router(auth.router, prefix="/api")` exposes `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`.
- Frontend Axios client in `frontend/src/api/client.js`: `baseURL = import.meta.env.VITE_API_BASE_URL || '/api'`.
- Vite Proxy in `frontend/vite.config.js`: Proxies `/api` directly to `http://localhost:8000`.
- Endpoint mapping verified cleanly end-to-end with no trailing slash mismatch or duplicate prefix issues.

## 3. Authentication & Security Architecture
- Password Hashing: Password hashing is enforced server-side using `pwd_context` (bcrypt via passlib). Passwords are never stored or returned in plaintext.
- Registration Payload: `UserSignup` validates `name`, `email`, `password` (min 6 chars), `department`, and `site`.
- Role Defaults: Public signup enforces safe default role `HSE_USER`. User cannot self-assign `ADMIN` or `HSE_MANAGER`.
- JWT Token Authentication: `POST /api/auth/login` returns `access_token`, `token_type: bearer`, and user payload. `GET /api/auth/me` validates bearer token and restores current user profile.

## 4. Leakage Protection Audit (`source_sheet` / `"12_High_Potential"`)
- Verified `models/final_model/feature_config.json`: `source_sheet` is explicitly listed in `excluded_features`.
- Stress Test Verified: Created test reports with `source_sheet="12_High_Potential"` vs `source_sheet="Normal_Near_Misses"`. Verified that ML predictions, SIF scores (`0.3541`), Life-Saving Rule mappings, and analytics remain 100% identical.

## 5. End-to-End Workflow Verification
- **Part 1 & 2**: Safety report submission $\rightarrow$ AI SIF Analysis $\rightarrow$ HSE Review.
- **Part 3**: Safety Intelligence Analytics $\rightarrow$ Barrier Intelligence (BDI) $\rightarrow$ Escalation & Pattern Detection.
- **Part 4A**: AI/System Intervention Recommendation Foundation.
- **Part 4B**: Human-in-the-Loop HSE Review & Approval (ACCEPT, MODIFY, REJECT).
- **Part 4C**: Action Management & Assignment.
- **Part 4D**: SLA Monitoring & Escalation (ACTIVE, DUE_SOON, OVERDUE).
- **Part 4E**: Completion, Verification & Impact Tracking.
- **Part 4F**: HSE Action Center Summary & Section Aggregation.

## 6. Commands to Run Local Platform
### Start Backend Server:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
### Start Frontend Dev Server:
```bash
npm run dev
```
### Run Unit & Integration Test Suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
python scratch/test_e2e_full.py
```
