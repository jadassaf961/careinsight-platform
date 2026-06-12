# Database Schema

Postgres 16. Migrations are managed with Alembic in `backend/alembic/`.

## Tables

| Table | Purpose |
|---|---|
| `hospitals` | Tenant root. `ehr_vendor` drives the integration adapter chosen. |
| `departments` | Hospital sub-units (e.g. Internal Medicine, Cardiology). |
| `roles` | RBAC roles — admin, physician, resident, nurse, case_manager, analyst. |
| `users` | Clinicians + admins; scoped to one hospital. |
| `patients` | PHI. Soft-deleted via `deleted_at`. Hospital-scoped. |
| `admissions` | One row per inpatient stay. `clinical_features` JSONB stores the ML feature dict. |
| `model_versions` | Registry of ML models. Partial unique index enforces ≤ 1 active version. |
| `predictions` | One row per scoring; links admission → model_version. |
| `risk_factors` | Persisted SHAP values (per prediction, ranked). |
| `recommendations` | Persisted checklist items (per prediction). |
| `interventions` | Clinician-recorded actions on an admission. |
| `reports` | Generated PDFs (artifact URI optional). |
| `audit_logs` | Per-request audit trail written by middleware. |
| `consent_records` | HIPAA/GDPR consent placeholder (no enforcement yet). |

## Conventions

- **UUIDv4** primary keys on every table — no integer sequences exposed to clients
- **`created_at`, `updated_at`** on every row via mixin (timezone-aware)
- **Soft delete via `deleted_at`** on PHI tables (currently `patients` only)
- **JSONB** for evolving structured data (`clinical_features`, `audit_logs.payload`)
- **Hospital scoping** — every PHI table carries `hospital_id` (directly or via patient)
- **Partial unique index** on `model_versions(is_active=true)` enforces single active version

## Useful indexes

- `(hospital_id, mrn)` unique on `patients`
- `(department_id, admitted_at)` on `admissions` for shift / cohort queries
- `(prediction_id, rank)` on `risk_factors` for fast top-N reads
- `(resource_type, resource_id)` + `created_at` on `audit_logs`

## ER outline

```
hospitals 1—* departments
hospitals 1—* users (role_id → roles)
hospitals 1—* patients
patients 1—* admissions —* predictions —* risk_factors
                          predictions —* recommendations
admissions —* interventions (recorded_by_user_id → users)
predictions 1—* reports
model_versions 1—* predictions
```

## Running migrations

```bash
cd backend
alembic upgrade head        # apply all pending
alembic revision --autogenerate -m "describe change"
alembic downgrade -1        # revert one step
```

## Seed data

`python -m app.db.seed` (or set `SEED_DEMO_DATA=true` and let lifespan run it)
creates one hospital, one department, one user per role, one active model
version, and three demo patients with admissions populated for end-to-end demo.
