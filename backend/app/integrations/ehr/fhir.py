"""FHIR R4 adapter (interface only — not yet implemented)."""
from __future__ import annotations

from app.integrations.ehr.base import AdmissionDTO, AssessmentDTO, EHRAdapter, PatientDTO


class FHIRAdapter(EHRAdapter):
    """Maps to FHIR R4 Patient/Encounter/Observation/Condition resources.

    Future implementation: SMART-on-FHIR OAuth client; map our schema to
    `Patient.identifier` (MRN), `Encounter` (admission), and write back
    `RiskAssessment` resources.
    """

    vendor = "fhir"

    def fetch_patient(self, mrn: str) -> PatientDTO:
        raise NotImplementedError("FHIR adapter not yet implemented")

    def fetch_admissions(self, mrn: str) -> list[AdmissionDTO]:
        raise NotImplementedError("FHIR adapter not yet implemented")

    def push_assessment(self, assessment: AssessmentDTO) -> None:
        raise NotImplementedError("FHIR adapter not yet implemented")
