"""Post-discharge follow-up engine: scheduling, dispatch, response scoring,
no-response detection. Governing rule: never silently drop a patient.

All time-dependent functions take an explicit `now` so tests never freeze
clocks, and all datetime comparisons happen in SQL (SQLite returns naive
datetimes; comparing them to aware datetimes in Python raises)."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.followup import (
    CheckinResponse,
    CheckinStatus,
    Escalation,
    EscalationPriority,
    FollowUpCheckin,
)
from app.models.hospital import Hospital
from app.models.transition import TransitionPlan
from app.services.messaging.base import MessagingProvider, OutboundMessage, SendError
from app.services.messaging.templates import render_checkin, score_reply


def schedule_checkins(db: Session, plan: TransitionPlan, now: datetime) -> list[FollowUpCheckin]:
    patient = plan.admission.patient
    reachable = bool(patient.phone_number) and not patient.messaging_opted_out
    status = CheckinStatus.SCHEDULED if reachable else CheckinStatus.MANUAL
    checkins = [
        FollowUpCheckin(
            hospital_id=plan.hospital_id, plan_id=plan.id, patient_id=patient.id,
            day_offset=offset, scheduled_at=now + timedelta(days=offset),
            status=status, language=patient.preferred_language,
        )
        for offset in settings.checkin_day_offsets_list
    ]
    db.add_all(checkins)
    db.flush()
    return checkins


def find_due_checkins(db: Session, now: datetime) -> list[FollowUpCheckin]:
    retry_cutoff = now - timedelta(minutes=settings.checkin_retry_minutes)
    q = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.status == CheckinStatus.SCHEDULED,
        FollowUpCheckin.scheduled_at <= now,
        (FollowUpCheckin.last_attempt_at.is_(None))
        | (FollowUpCheckin.last_attempt_at <= retry_cutoff),
    )
    return q.all()


def dispatch_due_checkins(db: Session, provider: MessagingProvider, now: datetime) -> int:
    sent = 0
    for checkin in find_due_checkins(db, now):
        patient = checkin.plan.admission.patient
        hospital = db.get(Hospital, checkin.hospital_id)
        body = render_checkin(
            checkin.language,
            name=patient.first_name,
            hospital=hospital.name if hospital else "your hospital",
            day=checkin.day_offset,
        )
        checkin.attempts += 1
        checkin.last_attempt_at = now
        try:
            provider.send(OutboundMessage(to=patient.phone_number or "", body=body))
        except SendError:
            if checkin.attempts >= settings.checkin_max_attempts:
                checkin.status = CheckinStatus.SEND_FAILED
                db.add(Escalation(
                    hospital_id=checkin.hospital_id, patient_id=patient.id,
                    checkin_id=checkin.id, trigger="send_failed",
                    detail=f"Day-{checkin.day_offset} check-in could not be delivered "
                           f"after {checkin.attempts} attempts — call the patient manually.",
                    priority=EscalationPriority.MEDIUM,
                ))
            continue
        checkin.status = CheckinStatus.SENT
        checkin.sent_at = now
        checkin.sent_body = body
        sent += 1
    db.flush()
    return sent


def record_response(
    db: Session, checkin: FollowUpCheckin, raw_text: str, provider_message_id: str | None,
) -> CheckinResponse:
    if provider_message_id:
        existing = db.query(CheckinResponse).filter(
            CheckinResponse.provider_message_id == provider_message_id
        ).first()
        if existing is not None:
            return existing

    scores = score_reply(raw_text)
    response = CheckinResponse(
        checkin_id=checkin.id, provider_message_id=provider_message_id,
        raw_text=raw_text[:2000], **scores,
    )
    db.add(response)
    checkin.status = CheckinStatus.RESPONDED
    patient = checkin.plan.admission.patient

    if scores["opted_out"]:
        patient.messaging_opted_out = True
        remaining = db.query(FollowUpCheckin).filter(
            FollowUpCheckin.plan_id == checkin.plan_id,
            FollowUpCheckin.status == CheckinStatus.SCHEDULED,
        ).all()
        for r in remaining:
            r.status = CheckinStatus.MANUAL
        db.add(Escalation(
            hospital_id=checkin.hospital_id, patient_id=patient.id, checkin_id=checkin.id,
            trigger="opted_out",
            detail="Patient opted out of messages — switch to phone-call follow-up.",
            priority=EscalationPriority.LOW,
        ))
    elif scores["red_flag"]:
        db.add(Escalation(
            hospital_id=checkin.hospital_id, patient_id=patient.id, checkin_id=checkin.id,
            trigger="red_flag",
            detail=f"Red-flag symptoms reported on day-{checkin.day_offset} check-in: "
                   f'"{raw_text[:200]}"',
            priority=EscalationPriority.HIGH,
        ))
    elif scores["meds_missed"]:
        db.add(Escalation(
            hospital_id=checkin.hospital_id, patient_id=patient.id, checkin_id=checkin.id,
            trigger="meds_missed",
            detail=f"Medication non-adherence reported on day-{checkin.day_offset} "
                   f'check-in: "{raw_text[:200]}"',
            priority=EscalationPriority.MEDIUM,
        ))
    db.flush()
    return response


def mark_no_responses(db: Session, now: datetime) -> int:
    cutoff = now - timedelta(hours=settings.checkin_no_response_hours)
    stale = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.status == CheckinStatus.SENT,
        FollowUpCheckin.sent_at <= cutoff,
    ).all()
    escalated_plans: set = set()
    for checkin in stale:
        checkin.status = CheckinStatus.NO_RESPONSE
    db.flush()  # sessions run with autoflush=False; the count below must see the new statuses
    for checkin in stale:
        if checkin.plan_id in escalated_plans:
            continue
        prior = db.query(FollowUpCheckin).filter(
            FollowUpCheckin.plan_id == checkin.plan_id,
            FollowUpCheckin.day_offset < checkin.day_offset,
            FollowUpCheckin.status == CheckinStatus.NO_RESPONSE,
        ).count()
        if prior >= 1:
            db.add(Escalation(
                hospital_id=checkin.hospital_id, patient_id=checkin.patient_id,
                checkin_id=checkin.id, trigger="no_response",
                detail="Two consecutive check-ins with no reply — patient may be "
                       "unreachable; call to verify.",
                priority=EscalationPriority.MEDIUM,
            ))
            escalated_plans.add(checkin.plan_id)
    db.flush()
    return len(stale)


def run_cycle(db: Session, provider: MessagingProvider, now: datetime) -> None:
    """One scheduler tick: dispatch due check-ins, then flag stale ones."""
    dispatch_due_checkins(db, provider, now)
    mark_no_responses(db, now)
    db.commit()
