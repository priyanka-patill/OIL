# OIL SIF Precursor Detection System — Part 2B Frontend Architecture

This document details the frontend application architecture, UI design system, component hierarchy, role-based navigation, API integration layer, and Part 2C extension boundaries implemented in **Part 2B** for Oil India Limited (OIL).

---

## 1. Executive Summary & Stack Overview

- **Framework**: React 18 + Vite 5
- **Routing**: React Router v6 (`BrowserRouter`, `Routes`, `ProtectedRoute`)
- **Styling**: Tailwind CSS with custom Oil India industrial dark slate theme (`#0b192c`, `#1e293b`, `#f97316`, `#eab308`)
- **Icons**: Lucide React
- **API Client**: Axios instance with Bearer JWT token interceptor and 401 session expiration handler
- **State Management**: React Context (`AuthProvider`) managing `user`, `role`, `token`, `isAuthenticated`, `isLoading`

---

## 2. Directory Structure of `frontend/`

```
ps2/frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── api/
    │   ├── client.js             # Axios client with Bearer header & 401 interceptor
    │   ├── authApi.js            # Login, Signup, Logout, Me API calls
    │   ├── reportsApi.js         # Report list, getById, create, update, review API calls
    │   └── adminApi.js           # Admin user management & audit log API calls
    ├── context/
    │   └── AuthContext.jsx       # Auth provider restoring user state via /api/auth/me
    ├── components/
    │   ├── common/
    │   │   ├── StatusBadge.jsx       # Status badges (SUBMITTED, HSE_VALIDATED, etc.)
    │   │   ├── ReportTypeBadge.jsx   # Observation type badges (NEAR_MISS, UNSAFE_ACT, etc.)
    │   │   ├── LoadingSpinner.jsx    # Full-screen and inline loading indicators
    │   │   ├── Pagination.jsx        # Server-side pagination bar
    │   │   └── NotificationToast.jsx # Floating status toasts
    │   ├── layout/
    │   │   ├── AppLayout.jsx         # Shell layout with Sidebar & Header
    │   │   ├── Header.jsx            # Sticky header with plant site & user status
    │   │   ├── Sidebar.jsx           # Responsive sidebar with role-aware menu
    │   │   └── ProtectedRoute.jsx    # Session & RBAC role guard wrapper
    │   └── reports/
    │       └── AIAnalysisPanel.jsx   # Reserved Part 2C AI analysis panel placeholder
    └── pages/
        ├── LoginPage.jsx         # Login screen connected to /api/auth/login
        ├── SignupPage.jsx        # User signup connected to /api/auth/signup
        ├── DashboardPage.jsx     # Dashboard with real backend metrics & report table
        ├── ReportListPage.jsx    # Report directory with search, filters, pagination
        ├── ReportNewPage.jsx     # 4-section report form matching ReportCreate schema
        ├── ReportDetailPage.jsx  # Complete report viewer, audit history & review modal
        ├── AdminUsersPage.jsx    # Admin user listing & role assignment table
        └── AdminAuditLogsPage.jsx # Admin system audit trail inspector
```

---

## 3. Role-Based Frontend UX Matrix

| Role | Accessible Navigation | Dashboard | Submit Report | View / Search Reports | Review Reports | Admin Tools |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`HSE_USER`** | Dashboard, Safety Reports, Submit Report | ✅ Real Data | ✅ Enabled | ✅ Own / Site | ❌ Hidden | ❌ Hidden |
| **`HSE_MANAGER`** | Dashboard, Safety Reports, Submit Report | ✅ Real Data | ✅ Enabled | ✅ All Reports | ✅ Accept/Reject Form | ❌ Hidden |
| **`ADMIN`** | Dashboard, Reports, Submit, Users, Audit Logs | ✅ Real Data | ✅ Enabled | ✅ All Reports | ✅ Accept/Reject Form | ✅ User & Audit Logs |

---

## 4. API Endpoints Integrated

1. **Authentication**:
   - `POST /api/auth/login` -> Authenticates credentials, stores JWT access token in `localStorage`.
   - `POST /api/auth/signup` -> Registers user (enforces `HSE_USER` default role on backend).
   - `GET /api/auth/me` -> Validates active token on page refresh.

2. **Safety Reports**:
   - `GET /api/reports` -> Lists reports with search, site, type, status filters & server-side pagination.
   - `POST /api/reports` -> Submits structured observation matching `ReportCreate` Pydantic schema.
   - `GET /api/reports/{id}` -> Fetches report details and review history.
   - `POST /api/reports/{id}/review` -> Submits HSE Manager review decision (`ACCEPTED`/`REJECTED`).

3. **Admin Management**:
   - `GET /api/admin/users` -> Fetches user list for role modification.
   - `PUT /api/admin/users/{id}` -> Updates user role or active status.
   - `GET /api/admin/audit-logs` -> Fetches system audit trail.

---

## 5. Part 2C Extension Contract

1. **`AIAnalysisPanel.jsx`**: Reserved UI section on `ReportDetailPage.jsx` displaying *"AI SIF precursor analysis will be connected in Part 2C"*. When Part 2C populates `ai_analysis` on `GET /api/reports/{id}`, this component automatically renders prediction labels, probabilities, and model explanations.
2. **Leakage Safeguard**: `source_sheet` is strictly excluded from all forms and components.

---

## 6. How to Run the Frontend Application

```powershell
# 1. Start Part 2A Backend (Port 8000)
uvicorn backend.main:app --reload --port 8000

# 2. Launch Vite Frontend Dev Server (Port 5173)
cd frontend
npm run dev
```

Visit [`http://localhost:5173`](http://localhost:5173) in your browser.
