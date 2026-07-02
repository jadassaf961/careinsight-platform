# CareInsight Care Transitions Platform — Design

**Date:** 2026-07-02
**Status:** Approved direction, pending spec review
**Author:** Jad Assaf (with Claude)

## 1. Why this exists

CareInsight today is a readmission-risk predictor with dashboards around it. Investor feedback (Symz Capital, June 2026) and independent research confirmed the problem: risk prediction is a *feature* — Epic ships readmission scores natively — not a company. A standalone score is a column a hospital can ignore; it has no daily active users, no workflow lock-in, and no pricing model.

**The direction change:** CareInsight becomes the software that runs a hospital's discharge-to-30-days process — the care transitions window where hospitals lose the most money and patients, and where no incumbent software lives in the MENA market. The predictor stops being the product and becomes the engine inside a workflow.

**Positioning:** the operations layer for MENA hospitals that will never run Epic. Target hospitals run a mix of legacy/local HIS and (occasionally) modern EHRs, so the product is EHR-agnostic and sits on top of whatever exists.

**Why this beats the "feature" critique:**

- A workflow product with daily active users in four roles (nurse, physician, pharmacist, case manager) is a system hospitals depend on, not a score they glance at.
- The closed outcomes loop builds a proprietary asset: readmission-outcome data from MENA populations, retraining MENA-specific models. Epic does not have this data and cannot easily get it.
- WhatsApp-native, Arabic-capable patient follow-up is structurally hard for western incumbents to replicate and is the region's real communication channel.

**Business model:** per-bed/month SaaS ($8–15/bed/month; a 200-bed hospital = $20–36K/year) plus a one-time integration/onboarding fee. Recurring, per-unit pricing.

**Expansion narrative (not built now):** care transitions (this spec) → patient flow / bed management (module 2) → regional clinical outcomes data network.

## 2. Scope

### v1 delivers five modules

1. **Discharge Readiness Board** — evolved WardView: per-patient readmission risk, expected discharge date, and open discharge blockers, grouped so "dischargeable today but blocked" surfaces first.
2. **Transition Checklists** — every discharge spawns role-assigned tasks generated from the prediction's risk factors (e.g., medication-complexity risk → pharmacist medication-reconciliation task). SHAP explanations become work orders.
3. **Post-discharge follow-up engine** — WhatsApp check-ins scheduled at days 2, 7, 14, and 30 after discharge, with structured questions (symptoms, medication adherence, red flags). Bilingual templates (English + Arabic) with a per-patient language preference.
4. **Escalation queue** — the case manager worklist: concerning answers, red flags, and unreachable patients, prioritized, with a resolve-with-notes flow.
5. **Outcomes loop** — actual readmissions recorded (manual entry in v1), producing the readmission-rate trend and local-data model accuracy. Feeds the existing ML `/retrain` endpoint.

### v1 explicitly excludes (phase 2, named for the roadmap story)

- HL7/ADT or any live EHR integration (v1 uses CSV import + manual entry)
- Bed management / patient-flow module
- Celery/Redis task queue (APScheduler in-process is sufficient at pilot scale)
- Patient-facing app
- French message templates
- Outcome-based pricing tooling

### Success criteria

1. A case manager at Rizk Hospital can run a real discharge through the full loop end-to-end.
2. The full loop — admission → risk → tasks → discharge → WhatsApp check-in → escalation → recorded outcome — demos in under 5 minutes with nothing faked off-screen (simulated messaging provider on stage, real provider in the pilot).
3. Pricing surfaces (admin ROI calculator) reflect per-bed/month.

## 3. Architecture

The three-service layout is unchanged: frontend (React/Vite, 5173) → backend (FastAPI, 8000) → ml-service (FastAPI, 8001). The ML service is untouched in v1; its `/predict`, `/explain`, and `/retrain` already serve the loop. All new work is backend extension + frontend evolution.

### 3.1 New ORM models (`backend/app/models/`)

All carry `hospital_id` and follow the existing multi-tenancy rule: every query filters by `current.hospital_id`.

| Model | Purpose | Key fields |
|---|---|---|
| `TransitionPlan` | One per admission once discharge planning starts | target discharge date; status: `planning` → `ready` → `discharged` → `closed` |
| `TransitionTask` | Checklist items | role, title, status (`open`/`done`/`skipped`), due date, `source` (risk factor or default rule that generated it) |
| `FollowUpCheckin` | Scheduled check-ins | day offset (2/7/14/30), scheduled datetime, status: `scheduled` → `sent` → `responded` / `no_response` / `send_failed` / `manual` / `skipped` |
| `CheckinResponse` | Patient answers | structured answers, computed concern score, raw message reference |
| `Escalation` | Case manager work item | trigger reason, priority, assigned user, status, resolution notes |
| `ReadmissionEvent` | Outcome record | links a new admission to a prior discharge within 30 days; manual entry in v1 |
| `MessageTemplate` | Check-in question sets | language (`en`/`ar`), day offset, question structure |

`Patient` gains `preferred_language` and `phone_number` (if not already present) plus an opt-out flag.

### 3.2 New/changed services (`backend/app/services/`)

- **`transition_service`** — plan and task lifecycle. The existing `checklist_service` grows into the task generator: it already maps predictions to `Recommendation` rows; those become assignable `TransitionTask` rows with owners and states. When no prediction exists, tasks generate from a default template; risk-driven tasks are added when a prediction lands.
- **`followup_service`** — creates the check-in schedule on discharge, finds due check-ins, scores responses, creates escalations.
- **`messaging/`** package — provider interface with two implementations, selected by env var (`MESSAGING_PROVIDER=simulated|twilio`):
  - `SimulatedProvider` — messages surface in an in-app phone panel; zero external dependencies; used for demos and development.
  - `TwilioWhatsAppProvider` — real WhatsApp via Twilio; inbound replies arrive at `POST /webhooks/messaging`.

### 3.3 Scheduling

APScheduler runs in-process in the FastAPI app, polling every few minutes for due check-ins and dispatching them through the provider. Pilot scale (one hospital, tens of discharges/week) does not justify a distributed queue.

### 3.4 Check-in scoring is rule-based, not ML

- Red-flag answer (e.g., chest pain = yes) → immediate high-priority escalation.
- Missed medications → medium-priority escalation.
- Two consecutive check-ins with no response → follow-up escalation ("unreachable").

Deterministic and explainable to clinicians. The ML stays where it is strong: admission-time risk.

### 3.5 New API routes (`backend/app/api/v1/`)

One file per resource, aggregated in `api/v1/__init__.py`, guarded by the existing `require_any_clinical_role` / `require_role` dependencies:

- `transitions.py` — plans and tasks (create/advance plan, complete tasks, board query)
- `checkins.py` — schedules, responses, simulated-reply endpoint (demo mode only)
- `escalations.py` — queue query, assign, resolve
- `outcomes.py` — readmission events, outcome metrics
- `webhooks.py` — `POST /webhooks/messaging` (unauthenticated, provider-signature-verified)

### 3.6 End-to-end data flow

```
Admission → prediction (existing) → TransitionPlan + tasks from risk factors
Discharge confirmed → FollowUpCheckins scheduled (days 2/7/14/30)
APScheduler → due check-ins sent via provider (WhatsApp or simulated)
Patient reply → webhook → CheckinResponse scored → Escalation if concerning
Case manager resolves escalation → notes recorded
Readmission (if any) recorded → outcomes dashboard + /retrain training data
```

## 4. Frontend

Existing pages evolve; one new demo component. TanStack Query for all server state; new types and endpoints in `lib/api.ts`.

- **WardView (`/ward`) → Discharge Readiness Board.** Rows gain expected discharge date and an open-blockers chip ("3 tasks · pharmacist, physician"). Grouping order: *dischargeable-but-blocked* (warning styling) → on track → not yet planned.
- **PatientChart → new "Transition" tab.** Three panels: task checklist (grouped by role, click-to-complete, shows originating risk factor), follow-up timeline (check-ins with status and inline patient answers), and this patient's escalations. Risk gauge and SHAP factors remain on the overview tab.
- **CaseManagerDashboard → Escalation Queue.** Priority-sorted worklist; each row shows patient, trigger, and days waiting; click to resolve with outcome notes.
- **ClinicianDashboard** — adds a "My open transition tasks" widget filtered to the user's role.
- **AdminDashboard** — adds the Outcomes panel: 30-day readmission-rate trend, check-in response rate, escalations caught pre-readmission, model AUC on local data. ROI calculator switched to per-bed/month pricing.
- **New component: `SimulatedPhone`** — slide-out WhatsApp-styled panel, visible only in simulated messaging mode: shows outbound check-ins, lets the demo operator type the patient's reply. Demo-mode state is visibly badged in the app shell.
- **ModelLab, PatientSearch, Login** — unchanged.

## 5. Error handling

Governing rule: **the system never silently drops a patient.**

- **Send failure:** retry with backoff; after 3 failures mark `send_failed` and create an escalation ("delivery failed — call manually"). Messaging outages degrade into phone-call work items, never lost follow-ups.
- **No response:** two consecutive unanswered check-ins auto-escalate.
- **Webhook safety:** replies from unrecognized numbers are stored raw and flagged for admin review; duplicate deliveries are idempotent (keyed on provider message ID); payloads are signature-verified.
- **Opt-out & consent:** "STOP" marks the patient opted out and converts remaining check-ins to `manual` escalations. Missing phone number → check-ins created as `manual` from the start. Required for WhatsApp Business compliance.
- **ML service down:** transition plans are independent of the ML service; default-template tasks generate immediately, risk-driven tasks attach when a prediction succeeds.
- **Demo mode** is visibly badged so simulated messages cannot be mistaken for real patient contact.

## 6. Testing

Follows existing conventions: in-memory SQLite, `auth_client` fixture, ML service never called in backend tests.

- **Scoring rules:** table-driven tests mapping answer combinations → expected escalation priority. Densest coverage — this is clinical logic.
- **Scheduling:** the "find due check-ins" function is tested directly with frozen time; APScheduler never runs in tests.
- **Messaging:** a `FakeProvider` records sends; provider selection, retry/backoff, and `send_failed` escalation are tested against it.
- **Webhook:** idempotency, signature verification, unknown-sender handling.
- **RBAC + tenancy:** every new route gets an explicit role test and a cross-hospital isolation test.
- **Frontend:** vitest for the escalation queue and checklist components; `npm run lint` (tsc) as the type gate.

## 7. Rough build order

1. Models + migrations/auto-create, seed data extended with demo transition scenarios, CSV import for patients/admissions (pilot data loading)
2. `transition_service` + tasks generation + `/transitions` API + Discharge Readiness Board
3. `followup_service` + messaging package (simulated provider first) + scheduler + `SimulatedPhone`
4. Escalations (service, API, queue UI)
5. Outcomes (recording, metrics, admin panel, ROI calculator update)
6. Twilio WhatsApp provider + webhook (pilot-only; demo works without it)

(Detailed task breakdown belongs to the implementation plan, not this spec.)
