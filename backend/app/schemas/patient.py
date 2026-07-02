"""Patient & admission Pydantic schemas."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    mrn: str = Field(..., max_length=40)
    first_name: str = Field(..., max_length=120)
    last_name: str = Field(..., max_length=120)
    dob: date
    sex: str = Field(..., max_length=20)
    phone_number: str | None = Field(None, max_length=40)
    preferred_language: str = Field("en", max_length=8)


class PatientRead(BaseModel):
    id: UUID
    hospital_id: UUID
    mrn: str
    first_name: str
    last_name: str
    dob: date
    sex: str
    phone_number: str | None
    preferred_language: str
    messaging_opted_out: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientList(BaseModel):
    items: list[PatientRead]
    total: int
    page: int
    page_size: int


class AdmissionCreate(BaseModel):
    department_id: UUID
    admission_type: str
    admitted_at: datetime
    discharged_at: datetime | None = None
    length_of_stay: float | None = None
    clinical_features: dict[str, Any] = Field(default_factory=dict)


class AdmissionRead(BaseModel):
    id: UUID
    patient_id: UUID
    department_id: UUID
    admission_type: str
    admitted_at: datetime
    discharged_at: datetime | None
    length_of_stay: float | None
    clinical_features: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
