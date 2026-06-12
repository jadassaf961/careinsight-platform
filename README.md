# CareInsight Platform

> Production-grade hospital readmission risk platform. Clinician-facing application with FastAPI backend, separate ML service, PostgreSQL database, and React frontend. Designed for future integration with Epic, Cerner, Meditech, and FHIR.

This is the production rebuild of the [CareInsight Streamlit prototype](https://github.com/jadassaf961/Ai-competition). The prototype remains the reference implementation of the ML pipeline; this repository re-platforms it for hospital deployment.

---

## Architecture

```
React + TS (Vite)    ──HTTPS──▶    FastAPI Backend    ──httpx──▶    ML Service (FastAPI)
                                          │
                                          ▼
                                     PostgreSQL
```

See [docs/architecture.md](docs/architecture.md) for the full design.

## Repository layout

```
careinsight-platform/
├── frontend/          React + TypeScript + Vite + Tailwind
├── backend/           FastAPI + SQLAlchemy + Alembic
├── ml-service/        FastAPI model server (XGBoost / RF / LR + SHAP)
├── database/          ERD + schema notes (migrations in backend/alembic/)
├── infrastructure/    Docker Compose, CI workflows, env templates
└── docs/              architecture, api, database, deployment, gaps
```

## Quickstart (local development)

Prerequisites: Docker Desktop, Node 20+, Python 3.11+.

```bash
cp infrastructure/.env.example infrastructure/.env
# edit .env, set JWT_SECRET and GEMINI_API_KEY

docker compose -f infrastructure/docker-compose.yml \
               -f infrastructure/docker-compose.dev.yml up --build
```

Once running:
- Backend API: http://localhost:8000/docs
- ML service: http://localhost:8001/docs
- Frontend: http://localhost:5173
- Postgres: localhost:5432 (user/pass in `.env`)

The dev seed creates one hospital, one department, and one user per role. Credentials are printed to the backend container logs on first boot.

## Running tests

```bash
# Backend
cd backend && pytest

# ML service
cd ml-service && pytest

# Frontend
cd frontend && npm test
```

## Documentation

- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [Database schema](docs/database.md)
- [Deployment](docs/deployment.md)
- [Gaps before hospital pilot](docs/gaps.md)
- [HIPAA control mapping (placeholder)](docs/compliance/hipaa.md)
- [GDPR data-subject rights (placeholder)](docs/compliance/gdpr.md)

## Status

This repository is a development scaffold. It is **not approved for clinical use**. Risk scores produced here are decision-support only and require qualified clinician review. See [docs/gaps.md](docs/gaps.md) for the work remaining before any hospital pilot.

## License

Proprietary — CareInsight team. All rights reserved.
