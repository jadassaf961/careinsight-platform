"""Check-in timeline + demo-mode simulated replies."""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role
from app.core.config import settings
from app.db.session import get_db
from app.models.followup import CheckinStatus, FollowUpCheckin
from app.models.patient import Patient
from app.models.user import User
from app.schemas.followup import CheckinRead, ResponseRead, SimulateReply
from app.services import followup_service

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.get("", response_model=list[CheckinRead])
def timeline(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[CheckinRead]:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    checkins = (
        db.query(FollowUpCheckin)
        .filter(FollowUpCheckin.patient_id == patient_id)
        .order_by(FollowUpCheckin.day_offset)
        .all()
    )
    return [CheckinRead.model_validate(c) for c in checkins]


@router.post("/{checkin_id}/simulate-reply", response_model=ResponseRead)
def simulate_reply(
    checkin_id: UUID,
    body: SimulateReply,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> ResponseRead:
    if settings.messaging_provider != "simulated":
        raise HTTPException(status_code=403, detail="Only available in demo mode")
    checkin = db.get(FollowUpCheckin, checkin_id)
    if checkin is None or checkin.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Check-in not found")
    if checkin.status != CheckinStatus.SENT:
        raise HTTPException(status_code=409, detail="Check-in has not been sent")
    response = followup_service.record_response(
        db, checkin, body.text, provider_message_id=f"sim-reply-{uuid4()}")
    db.commit()
    db.refresh(response)
    return ResponseRead.model_validate(response)
