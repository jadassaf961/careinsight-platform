"""ml-service request/response schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: dict[str, Any] = Field(default_factory=dict)
    threshold: float = 0.5


class PredictResponse(BaseModel):
    probability: float
    risk_tier: str
    model_name: str
    model_version: str


class ExplainRequest(BaseModel):
    features: dict[str, Any] = Field(default_factory=dict)
    top_n: int = 10


class FactorOut(BaseModel):
    feature_name: str
    shap_value: float


class ExplainResponse(BaseModel):
    factors: list[FactorOut]
    model_name: str
    model_version: str


class ModelVersionResponse(BaseModel):
    name: str
    version: str
    algorithm: str
    is_trained: bool


class RetrainRequest(BaseModel):
    csv_path: str | None = None


class RetrainResponse(BaseModel):
    status: str
    name: str
    version: str
    algorithm: str
    cv_auc: float | None = None
    test_auc: float | None = None
