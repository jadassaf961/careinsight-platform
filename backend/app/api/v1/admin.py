"""Admin-only endpoints: CSV bulk import + audit log query."""
from __future__ import annotations

import csv
import io
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.hospital import Department
from app.models.patient import Admission, Patient
from app.models.user import RoleName, User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/import/csv")
def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.ADMIN)),
) -> dict:
    """Bulk-import patients + initial admission from a CSV matching the
    reference clinical schema (see [configs/config.yaml](configs/config.yaml)).

    Each row creates a Patient (using `patient_id` column as MRN) plus an
    Admission populated from clinical columns. Predictions are NOT generated
    here — call POST /predictions per admission afterwards.
    """
    dept = (
        db.query(Department).filter(Department.hospital_id == current.hospital_id)
        .first()
    )
    if dept is None:
        raise HTTPException(status_code=400,
                            detail="No department configured for this hospital")

    content = file.file.read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))

    created = 0
    skipped = 0
    errors: list[str] = []
    for row in reader:
        mrn = row.get("patient_id") or row.get("mrn")
        if not mrn:
            skipped += 1
            errors.append("Row missing patient_id/mrn")
            continue
        try:
            existing = (
                db.query(Patient).filter(
                    Patient.hospital_id == current.hospital_id, Patient.mrn == mrn,
                ).first()
            )
            if existing is not None:
                skipped += 1
                continue

            dob = date.today().replace(year=date.today().year - int(float(row.get("age", 50))))
            patient = Patient(
                hospital_id=current.hospital_id, mrn=str(mrn),
                first_name=row.get("first_name", "Unknown"),
                last_name=row.get("last_name", "Unknown"),
                dob=dob, sex=row.get("gender", "Unknown"),
            )
            db.add(patient)
            db.flush()

            features = {k: v for k, v in row.items() if k not in ("patient_id", "mrn")}
            db.add(Admission(
                patient_id=patient.id, department_id=dept.id,
                admission_type=row.get("admission_type", "Unknown"),
                admitted_at=datetime.now(timezone.utc),
                length_of_stay=float(row.get("length_of_stay", 0) or 0),
                clinical_features=features,
            ))
            created += 1
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            errors.append(f"MRN={mrn}: {exc}")

    db.commit()
    return {
        "created_patients": created,
        "skipped_rows": skipped,
        "errors": errors[:10],
    }


@router.get("/audit-logs")
def list_audit_logs(
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.ADMIN)),
    user_id: UUID | None = None,
    resource_type: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    rows = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id), "user_id": str(r.user_id) if r.user_id else None,
            "action": r.action, "resource_type": r.resource_type,
            "resource_id": r.resource_id, "request_ip": r.request_ip,
            "payload": r.payload, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
