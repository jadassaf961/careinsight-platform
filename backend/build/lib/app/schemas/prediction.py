"""Prediction, risk factor, recommendation Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PredictionCreate(BaseModel):
    admission_id: UUID
    threshold: float | None = None


class PredictionRead(BaseModel):
    id: UUID
    admission_id: UUID
    model_version_id: UUID
    probability: float
    risk_tier: str
    threshold_used: float
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskSummaryRead(BaseModel):
    prediction_id: UUID
    probability: float
    risk_tier: str
    threshold_used: float
    model_name: str
    model_version: str
    generated_at: datetime


class RiskFactorRead(BaseModel):
    feature_name: str
    humanized_label: str
    shap_value: float
    rank: int

    model_config = {"from_attributes": True}


class RiskExplanationRead(BaseModel):
    prediction_id: UUID
    factors: list[RiskFactorRead]


class RecommendationRead(BaseModel):
    text: str
    category: str | None = None
    source: str

    model_config = {"from_attributes": True}
