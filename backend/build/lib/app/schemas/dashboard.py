"""Dashboard metric schemas."""
from __future__ import annotations

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
