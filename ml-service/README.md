# ML Service

FastAPI process that owns the model artifacts and SHAP explainer. Not exposed
to the internet — the backend is the only allowed caller.

```bash
pip install ".[dev]"
uvicorn app.main:app --port 8001 --reload
pytest
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | liveness |
| GET  | `/model/version` | active model metadata |
| POST | `/predict` | `{features, threshold}` → probability + tier |
| POST | `/explain` | `{features, top_n}` → ranked SHAP factors |
| POST | `/retrain` | `{csv_path}` → trains best of XGB/RF/LR by CV-AUC, isotonic-calibrates, persists joblib |

When no trained artifact exists, predict/explain fall back to a deterministic
clinical heuristic so the backend can demo end-to-end before `/retrain` is run.
