"""Epic adapter stub.

Future implementation: Epic AppOrchard / FHIR R4 over SMART-on-FHIR;
support Hyperspace clinical-context launch and Chart Search.
"""
from __future__ import annotations

from app.integrations.ehr.base import AdmissionDTO, AssessmentDTO, EHRAdapter, PatientDTO


class EpicAdapter(EHRAdapter):
    vendor = "epic"

    def fetch_patient(self, mrn: str) -> PatientDTO:
        raise NotImplementedError("Epic adapter not yet implemented")

    def fetch_admissions(self, mrn: str) -> list[AdmissionDTO]:
        raise NotImplementedError("Epic adapter not yet implemented")

    def push_assessment(self, assessment: AssessmentDTO) -> None:
        raise NotImplementedError("Epic adapter not yet implemented")
