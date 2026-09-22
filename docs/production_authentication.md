# Production Authentication & Signup Flow Documentation

## Overview
This document specifies the production authentication architecture, signup flow, API contract, Render environment configuration, CORS setup, and SPA routing setup for the Oil India Limited (OIL) HSE SIF Analytics application.

---

## 1. End-to-End Registration Flow

```
[ USER FILLS SIGNUP FORM ]
            │ (Name, Email, Password, Department, Site)
            ▼
[ POST /api/auth/signup ]
            │
            ├─► 1. Pydantic UserSignup Validation (Name: min 2, Password: min 6, valid Email)
            ├─► 2. Duplicate Email Check (Returns HTTP 409 Conflict if registered)
            ├─► 3. Password Hashing (Bcrypt)
            ├─► 4. User Persisted in DB (Role: HSE_USER, IsActive: True)
            ├─► 5. Returns HTTP 201 Created with APIResponse Envelope
            ▼
[ FRONTEND HANDLES RESPONSE ]
            │
            ├─► Validates success === true OR response.data.id exists
            ├─► Displays Success Toast: "Account created successfully! Redirecting to login..."
            ├─► Clears form submitting state & waits 1.5s
            └─► Navigates to /login
            ▼
[ USER LOGS IN AT /login ]
            │
            ├─► POST /api/auth/login
            ├─► Receives Bearer JWT Token & User Profile
            ├─► Token stored in localStorage ('oil_auth_token')
            └─► Navigates to /dashboard
```

---

## 2. API Contract Specification

### 2.1 Registration Endpoint: `POST /api/auth/signup`

#### Request Payload (`UserSignup` Schema)
```json
{
  "name": "Ramesh Kumar",
  "email": "ramesh@oil.in",
  "password": "Password123!",
  "department": "Operations",
  "site": "Digboi Refinery"
}
```

#### Success Response (`HTTP 201 Created`)
```json
{
  "success": true,
  "message": "User account registered successfully.",
  "data": {
    "id": 14,
    "name": "Ramesh Kumar",
    "email": "ramesh@oil.in",
    "role": "HSE_USER",
    "department": "Operations",
    "site": "Digboi Refinery",
    "is_active": true,
    "created_at": "2026-09-22T19:20:00+00:00"
  }
}
```

#### Error Responses
- **`HTTP 409 Conflict`**: Email already registered.
  ```json
  { "success": false, "message": "Email address 'ramesh@oil.in' is already registered.", "data": null }
  ```
- **`HTTP 422 Unprocessable Entity`**: Payload validation error (short password / invalid email).
- **`HTTP 500 Internal Error`**: Database write failure.

---

## 3. Render Deployment Setup & Environment Variables

### 3.1 Frontend Service Setup (Render Static Site)
- **Primary Domain**: `https://oil-indian-limited-sif-1.onrender.com`
- **Build Command**: `npm run build`
- **Publish Directory**: `dist`
- **Environment Variables**:
  - `VITE_API_BASE_URL`: Full URL of the backend FastAPI service (e.g. `https://oil-indian-limited-sif-backend.onrender.com/api`).
- **SPA Routing Rewrite Rule**:
  - **Source**: `/*`
  - **Destination**: `/index.html`
  - **Action**: `Rewrite`

### 3.2 Backend Service Setup (Render Web Service)
- **Environment Variables**:
  - `CORS_ORIGINS`: `https://oil-indian-limited-sif-1.onrender.com,http://localhost:5173`
  - `DATABASE_URL`: SQLite or PostgreSQL database connection string.
  - `SECRET_KEY`: Production secret key for JWT token signing.

---

## 4. Frontend Response Interceptor Safeguard

To prevent SPA rewrite fallback issues where misconfigured API URLs return the static `index.html` page with HTTP status 200:

1. `frontend/src/api/client.js` checks if the response payload is an HTML string (`<!DOCTYPE html>`).
2. If detected, it immediately throws a clear, actionable error:
   `"Server returned HTML instead of API JSON response. Please ensure VITE_API_BASE_URL points to the backend API."`
3. `SignupPage.jsx` catches the error and displays a helpful error message to the user rather than failing silently.
