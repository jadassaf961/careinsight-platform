"""Intervention schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.intervention import InterventionStatus


class InterventionCreate(BaseModel):
    admission_id: UUID
    recommendation_id: UUID | None = None
    status: InterventionStatus
    notes: str | None = None
    recorded_at: datetime


class InterventionRead(BaseModel):
    id: UUID
    admission_id: UUID
    recommendation_id: UUID | None
    recorded_by_user_id: UUID
    status: InterventionStatus
    notes: str | None
    recorded_at: datetime

    model_config = {"from_attributes": True}
