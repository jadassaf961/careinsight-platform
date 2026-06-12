# CareInsight Platform — Architecture

## Why this rebuild

The original CareInsight project is a Streamlit prototype: one process that runs UI, ML training, scoring, SHAP, PDF generation, and the AI assistant in a single application. That is appropriate for a competition demo but cannot:

- Be deployed inside a hospital network with role-based access
- Be audited (no per-action user trail)
- Integrate with EHR systems (no patient identity model)
- Scale ML compute independently from the UI
- Be versioned at the model level (the model lives in process memory)

This rebuild separates those concerns into a deployable product.

## High-level diagram

```
                 ┌─────────────────────┐
                 │  React + TS (Vite)  │
                 │  Tailwind + shadcn  │
                 └──────────┬──────────┘
                            │ HTTPS (JWT bearer)
                            ▼
                 ┌─────────────────────┐
                 │   FastAPI Backend   │
                 │  Auth · RBAC · API  │
                 │  Audit · Reports    │
                 └────┬───────────┬────┘
                      │           │ httpx (internal)
                      │           ▼
                      │  ┌─────────────────────┐
                      │  │   ML Service        │
                      │  │  /predict /explain  │
                      │  │  /model/version     │
                      │  └─────────────────────┘
                      ▼
              ┌──────────────┐
              │  PostgreSQL  │
              └──────────────┘
```

## Components

### Frontend (`frontend/`)
- React 18 + TypeScript + Vite + Tailwind CSS
- Auth via JWT in memory + refresh token in httpOnly cookie (future)
- TanStack Query for server state
- React Router for navigation
- Role-gated routes; a physician sees clinician views, an admin sees admin dashboards

### Backend (`backend/`)
- FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic
- All business logic — patient management, prediction orchestration, audit, PDF generation, chat
- Talks to PostgreSQL directly
- Talks to ML service over HTTP (httpx)
- Never embeds the model

### ML service (`ml-service/`)
- Separate FastAPI process on a different port
- Owns the trained model artifacts (joblib) and the SHAP explainer
- Endpoints: `/predict`, `/explain`, `/model/version`, `/retrain`
- Can be scaled / deployed independently

### Database (PostgreSQL)
- Single relational database; schema lives in `backend/alembic/versions/`
- UUIDv4 primary keys, `created_at` / `updated_at` everywhere
- JSONB for `clinical_features` so admission schema can evolve without migrations on every feature add

### EHR integration (`backend/app/integrations/ehr/`)
- Abstract `EHRAdapter` interface with `fetch_patient`, `fetch_admissions`, `push_assessment`
- Vendor stubs (`fhir.py`, `epic.py`, `cerner.py`, `meditech.py`) raise `NotImplementedError`
- Hospitals row carries an `ehr_vendor` field; a factory dispatches to the right adapter

## Request lifecycle (prediction)

1. Clinician opens patient chart → frontend calls `GET /api/v1/patients/{id}/risk`
2. Backend validates JWT, checks role, loads latest `Prediction` for the patient's most recent admission
3. If none exists or is stale, backend calls `POST ml-service/predict` with the admission's `clinical_features` JSONB
4. ML service returns `{probability, risk_tier, model_version}`
5. Backend persists a new `predictions` row, then `GET .../explanations` triggers `POST ml-service/explain` and persists `risk_factors`
6. `GET .../recommendations` runs `checklist_service` against persisted factors and risk tier
7. All four requests write to `audit_logs`

## Security model

- JWT with short TTL (15 min); refresh planned for production
- Bcrypt password hashing
- RBAC enforced at the route level via `Depends(require_role(...))`
- Audit middleware logs `user_id`, `method`, `path`, `resource_id`, `request_ip` for every authenticated request
- Multi-tenant boundary is `hospital_id` on every PHI table; query scoping is a known TODO before pilot (see `docs/gaps.md`)

## Compliance posture

HIPAA, GDPR, and consent management are scaffolded only. The database has a `consent_records` table and `docs/compliance/` carries control-mapping placeholders. Real compliance work (encryption-at-rest configuration, BAA-eligible hosting, retention policies, breach notification procedures) is out of scope for this scaffold.

## Why not Streamlit-in-React

A direct port would recreate the prototype's coupling: UI making business decisions, ML logic in pages, no audit trail, no identity model. The whole point of the rebuild is to make backend the source of truth and the UI a thin client.
