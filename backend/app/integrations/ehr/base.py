"""Abstract EHR adapter — extension point for vendor integrations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass
class PatientDTO:
    mrn: str
    first_name: str
    last_name: str
    dob: date
    sex: str


@dataclass
class AdmissionDTO:
    mrn: str
    admission_type: str
    admitted_at: datetime
    discharged_at: datetime | None
    clinical_features: dict[str, Any]


@dataclass
class AssessmentDTO:
    mrn: str
    probability: float
    risk_tier: str
    model_version: str
    generated_at: datetime


class EHRAdapter(ABC):
    """Vendor-agnostic EHR interface."""

    vendor: str = "abstract"

    @abstractmethod
    def fetch_patient(self, mrn: str) -> PatientDTO: ...

    @abstractmethod
    def fetch_admissions(self, mrn: str) -> list[AdmissionDTO]: ...

    @abstractmethod
    def push_assessment(self, assessment: AssessmentDTO) -> None: ...


class EHRAdapterFactory:
    """Resolve an :class:`EHRAdapter` by vendor key (from `hospitals.ehr_vendor`)."""

    @staticmethod
    def for_vendor(vendor: str | None) -> EHRAdapter | None:
        if not vendor:
            return None
        from app.integrations.ehr.cerner import CernerAdapter
        from app.integrations.ehr.epic import EpicAdapter
        from app.integrations.ehr.fhir import FHIRAdapter
        from app.integrations.ehr.meditech import MeditechAdapter
        mapping = {
            "fhir": FHIRAdapter,
            "epic": EpicAdapter,
            "cerner": CernerAdapter,
            "meditech": MeditechAdapter,
        }
        cls = mapping.get(vendor.lower())
        return cls() if cls else None
