"""Admission endpoints — nested under /patients/{patient_id}/admissions."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.patient import Admission, Patient
from app.models.user import RoleName, User
from app.schemas.patient import AdmissionCreate, AdmissionRead

router = APIRouter(prefix="/patients/{patient_id}/admissions", tags=["admissions"])


@router.post("", response_model=AdmissionRead, status_code=status.HTTP_201_CREATED)
def create_admission(
    patient_id: UUID,
    body: AdmissionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.ADMIN)),
) -> AdmissionRead:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    adm = Admission(patient_id=patient_id, **body.model_dump())
    db.add(adm)
    db.commit()
    db.refresh(adm)
    return AdmissionRead.model_validate(adm)


@router.get("", response_model=list[AdmissionRead])
def list_admissions(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.ADMIN, RoleName.PHYSICIAN, RoleName.RESIDENT,
        RoleName.NURSE, RoleName.CASE_MANAGER,
    )),
) -> list[AdmissionRead]:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    return [
        AdmissionRead.model_validate(a)
        for a in sorted(patient.admissions, key=lambda a: a.admitted_at, reverse=True)
    ]
