"""Dashboard metric schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_patients: int
    active_admissions: int
    high_risk_count: int
    predictions_last_24h: int


class ReadmissionStats(BaseModel):
    period: str
    total_predictions: int
    high_risk_rate: float
    note: str = "Placeholder — historical readmission outcomes not yet tracked."


class PopulationPatientRow(BaseModel):
    patient_id: UUID
    first_name: str
    last_name: str
    mrn: str
    department: str
    prediction_id: UUID
    probability: float
    risk_tier: str
    top_factor: str | None = None


class PopulationResponse(BaseModel):
    patients: list[PopulationPatientRow]
    high_count: int
    medium_count: int
    low_count: int
    total: int
    departments: list[str]


class FeatureImportanceItem(BaseModel):
    feature_name: str
    humanized_label: str
    avg_importance: float


class ModelStatsResponse(BaseModel):
    algorithm: str
    version: str
    trained_at: datetime | None = None
    cv_auc: float | None = None
    test_auc: float | None = None
    total_predictions: int
    tier_distribution: dict[str, int]
    top_features: list[FeatureImportanceItem]
