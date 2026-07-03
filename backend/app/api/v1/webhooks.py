"""Inbound messaging webhook (Twilio WhatsApp). Unauthenticated but
signature-verified; unknown senders are flagged, never dropped."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.followup import (
    CheckinStatus,
    Escalation,
    EscalationPriority,
    FollowUpCheckin,
)
from app.models.patient import Patient
from app.services import followup_service
from app.services.messaging.twilio_whatsapp import validate_twilio_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _default_hospital_id(db: Session):
    from app.models.hospital import Hospital
    h = db.query(Hospital).first()
    if h is None:
        raise HTTPException(status_code=500, detail="No hospital configured")
    return h.id


@router.post("/messaging")
async def inbound_message(
    request: Request,
    db: Session = Depends(get_db),
    x_twilio_signature: str = Header(default=""),
) -> dict[str, str]:
    form = dict((await request.form()).items())
    if not settings.twilio_auth_token or not validate_twilio_signature(
        str(request.url), form, x_twilio_signature, settings.twilio_auth_token,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    sender = form.get("From", "").removeprefix("whatsapp:")
    body = form.get("Body", "")
    message_sid = form.get("MessageSid") or None

    patient = db.query(Patient).filter(Patient.phone_number == sender).first()
    if patient is None:
        db.add(Escalation(
            hospital_id=_default_hospital_id(db), patient_id=None,
            trigger="unmatched_message",
            detail=f'Inbound message from unrecognized number {sender}: "{body[:200]}"',
            priority=EscalationPriority.LOW,
        ))
        db.commit()
        return {"status": "unmatched"}

    checkin = (
        db.query(FollowUpCheckin)
        .filter(
            FollowUpCheckin.patient_id == patient.id,
            FollowUpCheckin.status == CheckinStatus.SENT,
        )
        .order_by(FollowUpCheckin.sent_at.desc())
        .first()
    )
    if checkin is None:
        db.add(Escalation(
            hospital_id=patient.hospital_id, patient_id=patient.id,
            trigger="unmatched_message",
            detail=f'Reply received but no check-in awaiting response: "{body[:200]}"',
            priority=EscalationPriority.LOW,
        ))
        db.commit()
        return {"status": "no-open-checkin"}

    followup_service.record_response(db, checkin, body, provider_message_id=message_sid)
    db.commit()
    return {"status": "recorded"}
