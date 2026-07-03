"""Escalation queue for case managers."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.followup import Escalation, EscalationPriority, EscalationStatus
from app.models.patient import Patient
from app.models.user import RoleName, User
from app.schemas.followup import EscalationRead, EscalationUpdate

router = APIRouter(prefix="/escalations", tags=["escalations"])

_PRIORITY_ORDER = {
    EscalationPriority.HIGH: 0,
    EscalationPriority.MEDIUM: 1,
    EscalationPriority.LOW: 2,
}


def _to_read(db: Session, e: Escalation) -> EscalationRead:
    name = None
    if e.patient_id:
        p = db.get(Patient, e.patient_id)
        if p:
            name = f"{p.last_name}, {p.first_name}"
    return EscalationRead(
        id=e.id, patient_id=e.patient_id, patient_name=name, trigger=e.trigger,
        detail=e.detail, priority=e.priority.value, status=e.status.value,
        resolution_notes=e.resolution_notes, created_at=e.created_at,
    )


@router.get("", response_model=list[EscalationRead])
def list_escalations(
    status: str | None = None,
    patient_id: UUID | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[EscalationRead]:
    q = db.query(Escalation).filter(Escalation.hospital_id == current.hospital_id)
    if status:
        q = q.filter(Escalation.status == EscalationStatus(status))
    if patient_id:
        q = q.filter(Escalation.patient_id == patient_id)
    items = q.all()
    items.sort(key=lambda e: (_PRIORITY_ORDER[e.priority], e.created_at))
    return [_to_read(db, e) for e in items]


@router.patch("/{escalation_id}", response_model=EscalationRead)
def update_escalation(
    escalation_id: UUID,
    body: EscalationUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.CASE_MANAGER, RoleName.ADMIN)),
) -> EscalationRead:
    e = db.get(Escalation, escalation_id)
    if e is None or e.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Escalation not found")
    try:
        e.status = EscalationStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid status") from exc
    if body.resolution_notes is not None:
        e.resolution_notes = body.resolution_notes
    if e.status == EscalationStatus.RESOLVED:
        e.resolved_at = datetime.now(timezone.utc)
        e.assigned_user_id = current.id
    db.commit()
    db.refresh(e)
    return _to_read(db, e)
