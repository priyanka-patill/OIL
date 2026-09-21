# OIL HSE Safety Assistant — Technical Architecture & Integration Guide

## 1. Overview & Purpose
The **OIL HSE Safety Assistant** is an authenticated, provider-agnostic conversational AI system integrated into the Oil India Limited (OIL) HSE SIF Precursor Detection & Analytics Platform.

It provides natural-language assistance for:
- General HSE concepts (LOTO, hot work, confined space, gas testing, near misses).
- Authorized safety reports, ML SIF analysis scores, and HSE review decisions.
- Real-time safety intelligence, recurring precursor patterns, and barrier degradation metrics.
- User-assigned operational actions, SLA compliance, overdue alerts, and completion tracking.
- Platform navigation and workflow help.

---

## 2. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND SHELL                     │
│  [ChatbotLauncher] -> [ChatWindow] -> [ChatMessageList]     │
└──────────────────────────────┬──────────────────────────────┘
                               │ POST /api/chat (Bearer Token)
┌──────────────────────────────▼──────────────────────────────┐
│                    FASTAPI BACKEND ROUTER                   │
│                    backend/api/chat.py                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    CONVERSATIONAL SERVICE                   │
│                 backend/services/chat_service.py            │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐  ┌────────────▼──────────────┐
│ AUTHORIZED RETRIEVAL ENGINE │  │ PROVIDER-AGNOSTIC LLM CALL │
│ backend/services/chat_tools │  │ backend/services/llm_serv. │
└──────────────┬──────────────┘  └────────────┬──────────────┘
               │                              │
┌──────────────▼──────────────┐  ┌────────────▼──────────────┐
│ SQLALCHEMY DATABASE         │  │ LLM API / DOMAIN FALLBACK  │
│ SQLite data/app.db          │  │ Gemini / OpenAI / Fallback │
└─────────────────────────────┘  └────────────────────────────┘
```

---

## 3. Core Principles & Governance Rules
1. **Zero Data Fabrication**: All statistics, report numbers, action IDs, priorities, and SLA statuses are queried deterministically from the database.
2. **Strict Site & User Authorization**: Access control is enforced on the server based on `current_user.id`, `current_user.site`, and `current_user.role`. Cross-site or unauthorized data leakage is strictly blocked.
3. **No Internal Terminology**: User-facing responses never contain internal development phase labels (e.g., `Part 1A`, `Part 3C`, `Part 4F`).
4. **AI Safety Rule**: The assistant is an informational guide, NOT an operational work authorization tool. It never authorizes hazardous work (such as hot work or entry) and directs users to official Permits to Work, site procedures, and HSE supervisors.
5. **No `source_sheet` Shortcut**: Raw workbook metadata like `12_High_Potential` is never used as evidence or classification shortcuts.

---

## 4. API Specification

### Endpoint: `POST /api/chat`
**Request Body**:
```json
{
  "message": "What actions are assigned to me?",
  "conversation_id": "conv-123456"
}
```

**Response Body**:
```json
{
  "success": true,
  "message": "Message processed successfully.",
  "data": {
    "conversation_id": "conv-123456",
    "message": "You currently have 1 active action assigned to you...",
    "sources": [],
    "actions": [
      {
        "label": "View My Actions",
        "path": "/actions/my"
      }
    ]
  }
}
```

---

## 5. Configuration Settings
Environment variables in `.env`:
```env
LLM_API_KEY=
LLM_MODEL=gemini-1.5-flash
LLM_BASE_URL=
LLM_PROVIDER=auto
LLM_MAX_TOKENS=1000
LLM_TIMEOUT=30
```
If `LLM_API_KEY` is not set, the platform seamlessly uses the built-in domain synthesis engine to generate responses without crashing.
