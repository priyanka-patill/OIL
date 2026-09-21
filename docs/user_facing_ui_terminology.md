# User-Facing UI Terminology Mapping Standard

## Overview

Internal project development phase codes (e.g., `Part 1C`, `Part 2C`, `Part 3A-E`, `Part 4A-F`) represent project engineering phases and architecture abstractions. To maintain a production-ready, professional user experience for Oil India Limited (OIL) HSE personnel, all visible UI elements use operational safety terminology.

---

## Terminology Standard Mapping

| Internal Architecture Phase | Former UI Label | Production User-Facing Terminology | UI Component Location |
| :--- | :--- | :--- | :--- |
| **Part 4F** | `OIL HSE Safety Intelligence Platform — PART 4F` | `OIL HSE SAFETY INTELLIGENCE PLATFORM` | Action Center Top Header Banner |
| **Part 4F** | `Part 4F HSE Action Center` | `HSE Action Center` | Sidebar & Page Titles |
| **Part 4E** | `Part 4E Human-in-the-Loop` | `HSE Review & Verification` | Action Center Section Header |
| **Part 4E** | `PART 4E — Assignee Action Completion Workflow` | `ASSIGNEE ACTION COMPLETION WORKFLOW` | Action Detail Page Panel |
| **Part 4E** | `PART 4E — HSE Reviewer Verification & Reopen Panel` | `HSE REVIEWER VERIFICATION & REOPEN PANEL` | Action Detail Page Panel |
| **Part 4E** | `PART 4E — Observational Before/After Impact Engine (v1)` | `OBSERVATIONAL BEFORE/AFTER IMPACT ENGINE` | Action Detail Page Panel |
| **Part 4D** | `Part 4D Time-Aware Tracking` | `SLA & Operational Tracking` | Action Center Section Header |
| **Part 4D** | `PART 4D — Action & SLA Management` | `ACTION & SLA MANAGEMENT` | My Actions Page Header |
| **Part 4D** | `PART 4D — Manager & Organizational View` | `ACTION MANAGEMENT & MONITORING` | Assigned Actions Page Header |
| **Part 4D** | `PART 4D — SLA Monitoring & Escalation Engine` | `SLA MONITORING & ESCALATION ENGINE` | Action Detail Page Panel |
| **Part 4B** | `Part 4B — HSE Human-in-the-Loop Review` | `HSE Review & Validation` | Intervention Review Modal |
| **Part 4A** | `Part 4A — AI-Suggested Intervention Recommendations` | `AI-Suggested Intervention Recommendations` | Intervention Panel Header |
| **Part 3E** | `Part 3E Safety Intelligence` | `Safety Intelligence` | Sidebar & Navigation |
| **Part 3D** | `Part 3D non-predictive evidence indicators` | `Risk escalation evidence indicators` | Analytics Escalation Section |
| **Part 3C** | `Part 3C systematic tracking of barrier recurrence` | `Systematic tracking of barrier recurrence` | Analytics Barrier Section |
| **Part 3A** | `Part 3A cross-report pattern mining` | `Cross-report pattern mining` | Analytics Pattern Section |
| **Part 2C** | `Part 2C Extensions / AI Engine (Disabled)` | *(Removed from Navigation Menu)* | Sidebar Menu |
| **Part 2C** | `Part 2C AI analysis pending` | `AI Safety Analysis` | Dashboard Metric Card |
| **Part 1C** | `Part 1C Engine Connected` | `AI Model Connected` | AI Analysis Panel Header |
| **Part 1C** | `Part 1C AI Safety Analysis executed successfully!` | `AI Safety Analysis executed successfully!` | Report Detail Notification |

---

## Guidelines for Code & Documentation

- Developer documentation in `docs/` and internal Python/JavaScript source code comments may retain `Part X` labels for historical traceability.
- All user-facing strings rendered in JSX (titles, subheadings, tooltips, cards, buttons, badges, modals, toast notifications) **MUST** strictly follow the production terminology table above.
- Automated compliance is enforced by `tests/test_ui_label_compliance.py`.
