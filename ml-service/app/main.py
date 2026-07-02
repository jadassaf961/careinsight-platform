"""ml-service FastAPI app: /predict, /explain, /model/version, /retrain."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.model_loader import get_state, set_model
from app.pipeline.explain import compute_shap
from app.pipeline.predict import risk_tier
from app.pipeline.preprocessing import preprocess_single
from app.pipeline.schema import feature_names
from app.pipeline.train import train_from_csv
from app.schemas import (
    ExplainRequest,
    ExplainResponse,
    FactorOut,
    ModelVersionResponse,
    PredictRequest,
    PredictResponse,
    RetrainRequest,
    RetrainResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CareInsight ML Service")


def _fallback_probability(features: dict) -> float:
    """Deterministic placeholder used when no model artifact is present yet.

    Computes a crude weighted score from the most informative clinical features
    so the backend can demo end-to-end before /retrain is run. Real probabilities
    come from the trained model once it exists.
    """
    score = 0.0
    score += min(float(features.get("num_previous_admissions", 0)), 10) * 0.04
    score += min(float(features.get("medications_count", 0)), 20) * 0.015
    score += max(0.0, float(features.get("age", 50)) - 60) * 0.01
    score += max(0.0, float(features.get("last_creatinine", 1.0)) - 1.2) * 0.15
    if str(features.get("admission_type", "")).lower() == "emergency":
        score += 0.15
    if str(features.get("followup_compliance", "")).lower() == "poor":
        score += 0.12
    if str(features.get("social_support", "")).lower() == "weak":
        score += 0.08
    if str(features.get("chronic_conditions", "")).lower() in {"diabetes", "heart disease"}:
        score += 0.10
    return max(0.0, min(0.95, score))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/model/version", response_model=ModelVersionResponse)
def model_version() -> ModelVersionResponse:
    state = get_state()
    return ModelVersionResponse(
        name=settings.model_name,
        version=settings.model_version,
        algorithm=state.get("algorithm") or "unloaded",
        is_trained=state.get("model") is not None,
    )


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    state = get_state()
    model = state.get("model")
    if model is None:
        prob = _fallback_probability(req.features)
        algorithm = "fallback_heuristic"
    else:
        X = preprocess_single(req.features)
        prob = float(model.predict_proba(X)[0, 1])
        algorithm = state["algorithm"]
    return PredictResponse(
        probability=round(prob, 6),
        risk_tier=risk_tier(prob, req.threshold),
        model_name=settings.model_name,
        model_version=f"{settings.model_version}-{algorithm}",
    )


@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest) -> ExplainResponse:
    state = get_state()
    model = state.get("model")
    names = feature_names()
    if model is None:
        # Heuristic ranking of clinical drivers when no model is present
        weights = {
            "num_previous_admissions": 0.04 * float(req.features.get("num_previous_admissions", 0)),
            "medications_count": 0.015 * float(req.features.get("medications_count", 0)),
            "age": 0.01 * max(0.0, float(req.features.get("age", 50)) - 60),
            "last_creatinine": 0.15 * max(0.0, float(req.features.get("last_creatinine", 1.0)) - 1.2),
            "followup_compliance": 0.12 if str(req.features.get("followup_compliance", "")).lower() == "poor" else 0.0,
            "social_support": 0.08 if str(req.features.get("social_support", "")).lower() == "weak" else 0.0,
            "chronic_conditions": 0.10 if str(req.features.get("chronic_conditions", "")).lower() in {"diabetes", "heart disease"} else 0.0,
            "admission_type": 0.15 if str(req.features.get("admission_type", "")).lower() == "emergency" else 0.0,
        }
        items = sorted(weights.items(), key=lambda kv: abs(kv[1]), reverse=True)[: req.top_n]
        return ExplainResponse(
            factors=[FactorOut(feature_name=k, shap_value=round(v, 5)) for k, v in items],
            model_name=settings.model_name,
            model_version=f"{settings.model_version}-fallback",
        )

    X = preprocess_single(req.features)
    sv = compute_shap(model, state["algorithm"], X)
    idx = np.argsort(np.abs(sv))[::-1][: req.top_n]
    return ExplainResponse(
        factors=[
            FactorOut(feature_name=names[i], shap_value=round(float(sv[i]), 5))
            for i in idx
        ],
        model_name=settings.model_name,
        model_version=f"{settings.model_version}-{state['algorithm']}",
    )


@app.post("/retrain/upload", response_model=RetrainResponse)
def retrain_upload(file: UploadFile = File(...)) -> RetrainResponse:
    """Accept a CSV file upload, train, hot-swap model in memory, return metrics."""
    content = file.file.read()
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        result = train_from_csv(tmp_path, settings.model_registry_dir)
        import joblib
        blob = joblib.load(result.model_path)
        set_model(blob["model"], blob["algorithm"])
        return RetrainResponse(
            status="ok",
            name=settings.model_name,
            version=settings.model_version,
            algorithm=result.algorithm,
            cv_auc=result.cv_auc,
            test_auc=result.test_auc,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/retrain", response_model=RetrainResponse)
def retrain(req: RetrainRequest) -> RetrainResponse:
    if not req.csv_path:
        raise HTTPException(status_code=400, detail="csv_path required")
    csv = Path(req.csv_path)
    if not csv.exists():
        raise HTTPException(status_code=404, detail=f"CSV not found: {csv}")
    result = train_from_csv(csv, settings.model_registry_dir)
    import joblib
    blob = joblib.load(result.model_path)
    set_model(blob["model"], blob["algorithm"])
    return RetrainResponse(
        status="ok",
        name=settings.model_name,
        version=settings.model_version,
        algorithm=result.algorithm,
        cv_auc=result.cv_auc,
        test_auc=result.test_auc,
    )
