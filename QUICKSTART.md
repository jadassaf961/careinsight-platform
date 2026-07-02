# Quickstart — No Docker, native dev

Three PowerShell windows, ~5 minutes total. Backend uses SQLite (auto-created on first boot).

## Prerequisites

- Python 3.11+ (you have 3.14 — works)
- Node 20+ and npm (for the frontend)

Verify:
```powershell
py --version
node --version
npm --version
```

## Window 1 — Backend (FastAPI + SQLite)

```powershell
cd C:\Users\user\Desktop\careinsight-platform\backend
py -m pip install ".[dev]"    # first time only — skip on subsequent runs
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

First boot will create `dev.db` and seed one hospital + one user per role.
Demo password: **`Demo123!`**
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

## Window 2 — ML service

```powershell
cd C:\Users\user\Desktop\careinsight-platform\ml-service
py -m pip install ".[dev]"    # first time only — skip on subsequent runs
py -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

- ML docs: <http://localhost:8001/docs>

With no trained artifact present, `/predict` returns a deterministic heuristic
score so the end-to-end UI flow works immediately.

## Window 3 — Frontend (Vite)

```powershell
cd C:\Users\user\Desktop\careinsight-platform\frontend
npm install    # first time only — skip on subsequent runs
npm run dev
```

- App: <http://localhost:5173>

Log in as `physician@careinsight.dev` / `Demo123!`. Open one of the seeded
patients, click **Run prediction**, then **Generate PDF**.

## Available demo accounts

All use the same password `Demo123!`:

| Email | Role |
|---|---|
| admin@careinsight.dev | admin |
| physician@careinsight.dev | physician |
| resident@careinsight.dev | resident |
| nurse@careinsight.dev | nurse |
| casemanager@careinsight.dev | case_manager |
| analyst@careinsight.dev | analyst |

## Switching to Postgres later

Set the env var before starting the backend:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/careinsight"
cd C:\Users\user\Desktop\careinsight-platform\backend
alembic upgrade head
py -m uvicorn app.main:app --reload
```

## Reset the dev DB

```powershell
Remove-Item C:\Users\user\Desktop\careinsight-platform\backend\dev.db
```
Restart the backend — fresh schema and seed.
