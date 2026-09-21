# OIL HSE Safety Intelligence Platform — API Contract Documentation

## 1. Authentication Endpoints (`/api/auth`)

### `POST /api/auth/signup`
- **Description**: Registers a new user account. Defaults to role `HSE_USER`.
- **Request Body**:
  ```json
  {
    "name": "Full Name",
    "email": "user@oil.in",
    "password": "Password123!",
    "department": "Operations",
    "site": "Digboi Refinery"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "success": true,
    "message": "User account registered successfully.",
    "data": {
      "id": 1,
      "name": "Full Name",
      "email": "user@oil.in",
      "role": "HSE_USER",
      "department": "Operations",
      "site": "Digboi Refinery",
      "is_active": true,
      "created_at": "2026-09-17T10:00:00Z"
    }
  }
  ```

### `POST /api/auth/login`
- **Description**: Authenticates user credentials and returns JWT bearer access token.
- **Request Body**:
  ```json
  {
    "email": "user@oil.in",
    "password": "Password123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "Login successful.",
    "data": {
      "access_token": "<jwt-token>",
      "token_type": "bearer",
      "expires_in_minutes": 120,
      "user": { "id": 1, "name": "Full Name", "email": "user@oil.in", "role": "HSE_USER" }
    }
  }
  ```

### `GET /api/auth/me`
- **Description**: Returns authenticated user profile. Requires Bearer Token.
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "Success",
    "data": { "id": 1, "name": "Full Name", "email": "user@oil.in", "role": "HSE_USER" }
  }
  ```

### `POST /api/auth/logout`
- **Description**: Invalidation endpoint for client session cleanup.

---

## 2. Safety Reports & AI Analysis (`/api/reports`)

### `POST /api/reports`
- **Description**: Submits a new safety/near-miss observation report.
- **Request Body**: `ReportCreate` schema (date, site, refinery_unit, description, ppe_noncompliance, supervisor_negligence, etc.)

### `POST /api/reports/{id}/analyze`
- **Description**: Triggers Part 1C ML model analysis to classify SIF potential, score, and Life-Saving Rules.

### `POST /api/reports/{id}/review`
- **Description**: Submits human-in-the-loop HSE Manager review and classification.

---

## 3. Intervention Recommendations & Review (`/api/interventions`)

### `POST /api/interventions/generate`
- **Description**: Generates AI/system intervention recommendation for analyzed report.

### `POST /api/interventions/{id}/review`
- **Description**: Human HSE review (`decision: "ACCEPT" | "MODIFY" | "REJECT"`).

---

## 4. Action Lifecycle & SLA (`/api/actions`)

### `POST /api/actions`
- **Description**: Converts HSE-accepted intervention into an organizational action.

### `GET /api/actions/{id}/sla`
- **Description**: Fetches real-time authoritative SLA countdown, remaining minutes, and status.

### `POST /api/actions/{id}/complete`
- **Description**: Assignee submits completion evidence and transitions status to `VERIFICATION_PENDING`.

### `POST /api/actions/{id}/verify`
- **Description**: HSE Manager verifies action (`VERIFY`) or reopens (`REOPEN`).

### `GET /api/actions/{id}/impact`
- **Description**: Evaluates Part 4E before/after intervention impact analysis.

---

## 5. Action Center & Analytics (`/api/action-center`, `/api/analytics`)

### `GET /api/action-center/summary`
- **Description**: Aggregates authoritative KPI counts (`pending_reviews`, `active_actions`, `verified`, `due_soon`, `overdue`).

### `GET /api/analytics/bdi`
- **Description**: Computes Barrier Degradation Index scores and evidence payloads across sites.
