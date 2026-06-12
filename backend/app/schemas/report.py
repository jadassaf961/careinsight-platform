"""Report Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportCreate(BaseModel):
    prediction_id: UUID


class ReportRead(BaseModel):
    id: UUID
    prediction_id: UUID
    generated_by_user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
