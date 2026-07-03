"""Patient resource endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.hospital import Department
from app.models.patient import Patient
from app.models.user import RoleName, User
from app.schemas.patient import PatientCreate, PatientList, PatientRead

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=PatientList)
def list_patients(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    q: str | None = Query(None, description="Search MRN or name"),
) -> PatientList:
    query = db.query(Patient).filter(
        Patient.hospital_id == current.hospital_id,
        Patient.deleted_at.is_(None),
    )
    if q:
        like = f"%{q.lower()}%"
        from sqlalchemy import func, or_
        query = query.filter(or_(
            func.lower(Patient.mrn).like(like),
            func.lower(Patient.first_name).like(like),
            func.lower(Patient.last_name).like(like),
        ))
    total = query.count()
    items = (
        query.order_by(Patient.last_name, Patient.first_name)
        .offset((page - 1) * page_size).limit(page_size).all()
    )
    return PatientList(
        items=[PatientRead.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    body: PatientCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.ADMIN)),
) -> PatientRead:
    existing = (
        db.query(Patient)
        .filter(Patient.hospital_id == current.hospital_id, Patient.mrn == body.mrn)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Patient with MRN {body.mrn} already exists")
    patient = Patient(hospital_id=current.hospital_id, **body.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return PatientRead.model_validate(patient)


@router.get("/departments")
def list_departments(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[dict]:
    depts = (
        db.query(Department)
        .filter(Department.hospital_id == current.hospital_id)
        .order_by(Department.name)
        .all()
    )
    return [{"id": str(d.id), "name": d.name, "code": d.code} for d in depts]


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PatientRead:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=403, detail="Patient outside your hospital scope")
    return PatientRead.model_validate(patient)
