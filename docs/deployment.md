# Deployment

The platform is fully containerized. Local dev, staging, and production all
run the same images; only environment variables and the compose overrides change.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2 on Linux)
- 4 GB RAM minimum, 8 GB recommended (XGBoost + SHAP)

## Local development

```bash
cd careinsight-platform
cp infrastructure/.env.example infrastructure/.env
# edit infrastructure/.env, at minimum set JWT_SECRET and GEMINI_API_KEY

docker compose -f infrastructure/docker-compose.yml \
               -f infrastructure/docker-compose.dev.yml \
               --env-file infrastructure/.env up --build
```

Services:
- Postgres: `localhost:5432`
- Backend API: `http://localhost:8000` (`/docs` for Swagger)
- ML service: `http://localhost:8001` (`/docs`)
- Frontend dev server: `http://localhost:5173`

The backend lifespan auto-runs Alembic and the dev seed on first boot. Look
for the demo password line in the backend container logs.

## Production

In production, the dev compose override is omitted. The frontend container
serves the Vite-built static bundle via nginx and proxies `/api/` to the backend.

```bash
docker compose -f infrastructure/docker-compose.yml --env-file infrastructure/.env up -d
```

For a real deployment, you would additionally:
- Run Postgres on managed infrastructure (RDS / Cloud SQL / Azure DB)
- Front the backend with TLS termination (ALB / Cloud Load Balancer)
- Pin image tags (not `:latest`) and ship images via a registry
- Disable `SEED_DEMO_DATA`
- Rotate `JWT_SECRET` to a long random value (32+ bytes)
- Configure WAL-archived backups for the DB

## CI

`infrastructure/ci/github-actions.yml` runs three matrix jobs on push / PR:
backend pytest, ml-service pytest, frontend tsc + build. Copy this into
`.github/workflows/ci.yml` to activate.

## Operations runbook

- **DB migration failure on deploy**: backend container will exit. Inspect logs,
  fix the migration in `backend/alembic/versions/`, redeploy.
- **ml-service unreachable from backend**: backend will return 503 from
  prediction endpoints. Check `ML_SERVICE_URL` env var and ml-service container
  health.
- **Audit table growth**: schedule a retention job to archive `audit_logs`
  older than 180 days. Not implemented in this scaffold.
- **Model rollback**: set the prior `model_versions` row to `is_active=true`
  (the partial unique index will block more than one).
