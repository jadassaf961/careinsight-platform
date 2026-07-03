# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the application

Three services must all be running. Each in its own terminal, from the repo root:

```powershell
# Backend (FastAPI, port 8000)
cd backend
py -m pip install ".[dev]"        # first time only
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ML service (port 8001)
cd ml-service
py -m pip install ".[dev]"        # first time only
py -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend (Vite, port 5173)
cd frontend
npm install                        # first time only
npm run dev
```

Dev DB (SQLite) is auto-created at `backend/dev.db` on first backend boot with seeded demo data. Demo password for all accounts: `Demo123!`

To reset: `Remove-Item backend\dev.db` and restart the backend.

## Development commands

### Backend
```powershell
cd backend
py -m pytest                          # all tests
py -m pytest tests/test_patients.py  # single file
py -m ruff check app/                 # lint
py -m ruff check --fix app/           # lint + auto-fix
```

### Frontend
```powershell
cd frontend
npm run lint    # TypeScript type-check (tsc --noEmit)
npm test        # vitest run
npm run build   # production build (tsc -b && vite build)
```

### Secrets / environment
Backend reads from `backend/.env` (gitignored). Key variables:
- `DATABASE_URL` — defaults to `sqlite:///./dev.db`; set to `postgresql+psycopg://...` for Postgres
- `GEMINI_API_KEY` — enables the AI chat copilot (uses `gemini-2.5-flash`)
- `ML_SERVICE_URL` — defaults to `http://localhost:8001`
- `JWT_SECRET` — change from the dev default in any non-local environment

For Postgres, run `alembic upgrade head` inside `backend/` before starting the server.

## Architecture

### Three-service layout

```
frontend (React/Vite)  →  backend (FastAPI)  →  ml-service (FastAPI)
        5173                    8000                   8001
```

The **backend** is the only service the frontend talks to. The backend calls the **ml-service** synchronously over HTTP via `MLClient` (`backend/app/services/ml_client.py`) when a prediction or explanation is requested.

### Backend structure (`backend/app/`)

| Layer | Location | Notes |
|---|---|---|
| Config | `core/config.py` | Pydantic-Settings; reads env + `.env` |
| ORM models | `models/` | SQLAlchemy 2.0 mapped classes |
| Pydantic schemas | `schemas/` | Separate from ORM; use `model_validate()` |
| API routes | `api/v1/` | One file per resource; aggregated in `api/v1/__init__.py` |
| Services | `services/` | Business logic (pdf_service, ml_client, chat_service, checklist_service) |
| DB | `db/` | `session.py` (engine + `get_db`), `base.py` (Base + mixins), `seed.py` |
| Migrations | `alembic/` | Used for Postgres only; SQLite auto-creates tables on startup |

**Auth & RBAC:** JWT issued at `POST /auth/token`. Every protected route uses one of two FastAPI dependencies from `api/deps.py`:
- `require_any_clinical_role()` — any logged-in clinician
- `require_role(RoleName.PHYSICIAN, ...)` — specific roles only

**Multi-tenancy:** All clinical data is scoped to `hospital_id`. Every query that touches patient data must filter by `current.hospital_id`.

**Prediction flow:** `POST /predictions` → `MLClient.predict()` → `MLClient.explain()` → persist `Prediction` + `RiskFactor` rows + `Recommendation` rows (via `checklist_service`) in one transaction.

### ML service structure (`ml-service/app/`)

- `main.py` — three endpoints: `/predict`, `/explain`, `/retrain`
- `model_loader.py` — global in-memory model state (`get_state()` / `set_model()`)
- `pipeline/train.py` — trains Logistic Regression / Random Forest / XGBoost, selects best by CV AUC, calibrates, saves joblib artifact
- `pipeline/explain.py` — SHAP values for the trained model
- **No trained model?** Both `/predict` and `/explain` return deterministic heuristic scores so the full UI flow works immediately without training data.

### Frontend structure (`frontend/src/`)

- `lib/api.ts` — thin `fetch` wrapper; all types for API responses; adds `Authorization: Bearer` header from `localStorage`
- `pages/` — one file per route (`PatientSearch`, `PatientChart`, `Login`, `ClinicianDashboard`)
- `components/` — shared UI (`RiskGauge`, layout shell)
- State: TanStack Query v5 for server state, plain `useState` for local UI state
- Routing: React Router v6; routes defined in `main.tsx` (or `App.tsx`)
- Styling: Tailwind CSS; custom tokens (`brand-*`, `risk-high`, `risk-low`) defined in `tailwind.config`

### Testing conventions

Backend tests use an **in-memory SQLite** database (not the dev `dev.db`). `conftest.py` sets env vars before any import and provides:
- `client` — plain `TestClient`
- `auth_client` — `TestClient` with `get_current_user` overridden; call `client.set_user(user)` to inject a user
- `hospital`, `physician`, `admin_user`, `nurse` fixtures

The ML service is **not** mocked in backend tests — endpoints that call it will fail if it isn't running, so tests avoid hitting prediction endpoints directly.
