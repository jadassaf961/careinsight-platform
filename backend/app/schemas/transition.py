"""Transition plan/task/board Pydantic schemas."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class PlanCreate(BaseModel):
    admission_id: UUID
    target_discharge_date: date | None = None


class TaskRead(BaseModel):
    id: UUID
    role: str
    title: str
    status: str
    due_date: date | None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    status: str  # open | done | skipped


class PlanRead(BaseModel):
    id: UUID
    admission_id: UUID
    status: str
    target_discharge_date: date | None
    created_at: datetime
    tasks: list[TaskRead]

    model_config = {"from_attributes": True}


class BoardRow(BaseModel):
    patient_id: UUID
    admission_id: UUID
    first_name: str
    last_name: str
    mrn: str
    department: str
    probability: float | None
    risk_tier: str | None
    plan_id: UUID | None
    plan_status: str | None
    target_discharge_date: date | None
    open_tasks: int
    open_task_roles: list[str]


class BoardResponse(BaseModel):
    rows: list[BoardRow]
