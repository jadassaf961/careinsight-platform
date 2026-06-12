"""Meditech Expanse adapter stub.

Future implementation: HL7 v2 ADT feeds + Meditech Greenfield FHIR R4.
"""
from __future__ import annotations

from app.integrations.ehr.base import AdmissionDTO, AssessmentDTO, EHRAdapter, PatientDTO


class MeditechAdapter(EHRAdapter):
    vendor = "meditech"

    def fetch_patient(self, mrn: str) -> PatientDTO:
        raise NotImplementedError("Meditech adapter not yet implemented")

    def fetch_admissions(self, mrn: str) -> list[AdmissionDTO]:
        raise NotImplementedError("Meditech adapter not yet implemented")

    def push_assessment(self, assessment: AssessmentDTO) -> None:
        raise NotImplementedError("Meditech adapter not yet implemented")
