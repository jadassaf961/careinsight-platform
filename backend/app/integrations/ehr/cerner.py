"""Cerner / Oracle Health adapter stub.

Future implementation: Cerner Ignite / FHIR R4 via Code Cloud.
"""
from __future__ import annotations

from app.integrations.ehr.base import AdmissionDTO, AssessmentDTO, EHRAdapter, PatientDTO


class CernerAdapter(EHRAdapter):
    vendor = "cerner"

    def fetch_patient(self, mrn: str) -> PatientDTO:
        raise NotImplementedError("Cerner adapter not yet implemented")

    def fetch_admissions(self, mrn: str) -> list[AdmissionDTO]:
        raise NotImplementedError("Cerner adapter not yet implemented")

    def push_assessment(self, assessment: AssessmentDTO) -> None:
        raise NotImplementedError("Cerner adapter not yet implemented")
