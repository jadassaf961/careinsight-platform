# API Reference

All endpoints live under `/api/v1`. Auth uses JWT bearer tokens.
Live OpenAPI spec at `http://localhost:8000/docs`.

## Auth

| Method | Path | Body | Returns | Roles |
|---|---|---|---|---|
| POST | `/auth/login` | `{email, password}` | `{access_token, token_type, expires_in_seconds}` | public |
| POST | `/auth/refresh` | — | new token | authenticated |
| GET  | `/auth/me` | — | current user profile | authenticated |

## Patients

| Method | Path | Body | Returns | Roles |
|---|---|---|---|---|
| GET  | `/patients?q=&page=&page_size=` | — | paginated list | any clinical |
| POST | `/patients` | `{mrn,first_name,last_name,dob,sex}` | created patient | physician, admin |
| GET  | `/patients/{id}` | — | patient | any clinical |
| GET  | `/patients/{id}/admissions` | — | list of admissions | any clinical |
| POST | `/patients/{id}/admissions` | admission body | created admission | physician, admin |
| GET  | `/patients/{id}/risk` | — | latest risk summary | any clinical |
| GET  | `/patients/{id}/explanations` | — | SHAP factors | physician, case_manager, admin |
| GET  | `/patients/{id}/recommendations` | — | checklist | physician, nurse, case_manager |

## Predictions

| Method | Path | Body | Returns | Roles |
|---|---|---|---|---|
| POST | `/predictions` | `{admission_id, threshold?}` | new prediction + persisted SHAP + recs | physician, admin |
| GET  | `/predictions/{id}` | — | prediction | any clinical |

## Reports

| Method | Path | Body | Returns | Roles |
|---|---|---|---|---|
| POST | `/reports/pdf` | `{prediction_id}` | `application/pdf` stream | physician, case_manager |

## Chat (AI Copilot)

| Method | Path | Body | Returns | Roles |
|---|---|---|---|---|
| POST | `/chat` | `{patient_id, message, history[]}` | `{reply, disclaimer}` | physician, case_manager |

The assistant is bound by a strict system prompt: it explains predictions and
risk drivers in plain clinical language; it does NOT diagnose, prescribe, or
issue treatment decisions, and always closes with a disclaimer line.

## Dashboard

| Method | Path | Returns | Roles |
|---|---|---|---|
| GET | `/dashboard/metrics` | counts: patients, active admissions, high-risk, predictions/24h | any clinical |
| GET | `/dashboard/readmissions` | high-risk rate over all predictions | admin, analyst |

## Admin

| Method | Path | Body | Returns | Roles |
|---|---|---|---|---|
| POST | `/admin/import/csv` | multipart CSV | `{created_patients, skipped_rows, errors[]}` | admin |
| GET | `/admin/audit-logs?user_id=&resource_type=&limit=` | — | audit rows | admin |

## ML service (internal)

Backend talks to ml-service over HTTP at `ML_SERVICE_URL`. Not exposed publicly.

| Method | Path | Body | Returns |
|---|---|---|---|
| GET  | `/health` | — | `{status:"ok"}` |
| GET  | `/model/version` | — | active model metadata |
| POST | `/predict` | `{features, threshold}` | `{probability, risk_tier, model_name, model_version}` |
| POST | `/explain` | `{features, top_n}` | `{factors[], model_name, model_version}` |
| POST | `/retrain` | `{csv_path}` | training metadata + persisted artifact |

When no trained artifact is present in the registry, `/predict` and `/explain`
return values from a deterministic clinical-heuristic fallback. Call `/retrain`
with a CSV matching the reference schema to replace it.
