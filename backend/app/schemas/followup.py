"""Check-in, escalation, outcomes Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResponseRead(BaseModel):
    id: UUID
    raw_text: str
    red_flag: bool
    meds_missed: bool
    opted_out: bool
    concern_score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckinRead(BaseModel):
    id: UUID
    patient_id: UUID
    day_offset: int
    scheduled_at: datetime
    status: str
    sent_at: datetime | None
    sent_body: str | None
    language: str
    responses: list[ResponseRead]

    model_config = {"from_attributes": True}


class SimulateReply(BaseModel):
    text: str


class EscalationRead(BaseModel):
    id: UUID
    patient_id: UUID | None
    patient_name: str | None
    trigger: str
    detail: str
    priority: str
    status: str
    resolution_notes: str | None
    created_at: datetime


class EscalationUpdate(BaseModel):
    status: str  # open | in_progress | resolved
    resolution_notes: str | None = None


class ReadmissionCreate(BaseModel):
    admission_id: UUID


class ReadmissionRead(BaseModel):
    id: UUID
    patient_id: UUID
    prior_admission_id: UUID
    readmission_admission_id: UUID
    days_since_discharge: int

    model_config = {"from_attributes": True}


class OutcomeMetrics(BaseModel):
    discharges_tracked: int
    readmissions_30d: int
    readmission_rate: float | None
    checkin_response_rate: float | None
    escalations_open: int
    escalations_resolved: int
    monthly: list[dict]  # [{"month": "2026-07", "discharges": n, "readmissions": n}]
