"""Scheduling, dispatch, retry, no-response — all with explicit `now` params."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.followup import CheckinStatus, Escalation, FollowUpCheckin
from app.models.hospital import Hospital
from app.services import followup_service, transition_service
from app.services.messaging.base import OutboundMessage, SendError
from tests.test_transition_service import make_admission

NOW = datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)


class FakeProvider:
    name = "fake"

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[OutboundMessage] = []

    def send(self, message: OutboundMessage) -> str:
        if self.fail:
            raise SendError("boom")
        self.sent.append(message)
        return f"fake-{len(self.sent)}"


def make_discharged_plan(db: Session, hospital: Hospital, phone="+96170000001"):
    adm = make_admission(db, hospital, phone=phone)
    plan = transition_service.create_plan(db, adm, hospital.id)
    transition_service.discharge_plan(db, plan, now=NOW)
    db.commit()
    return plan


def test_schedule_checkins_offsets(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    checkins = db.query(FollowUpCheckin).filter_by(plan_id=plan.id).order_by(
        FollowUpCheckin.day_offset).all()
    assert [c.day_offset for c in checkins] == [2, 7, 14, 30]
    assert checkins[0].scheduled_at.replace(tzinfo=timezone.utc) == NOW + timedelta(days=2)
    assert all(c.status == CheckinStatus.SCHEDULED for c in checkins)


def test_schedule_checkins_no_phone_is_manual(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital, phone=None)
    checkins = db.query(FollowUpCheckin).filter_by(plan_id=plan.id).all()
    assert all(c.status == CheckinStatus.MANUAL for c in checkins)


def test_dispatch_sends_due_checkins(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    later = NOW + timedelta(days=2, minutes=5)
    sent = followup_service.dispatch_due_checkins(db, provider, now=later)
    db.commit()
    assert sent == 1
    assert len(provider.sent) == 1
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    assert c.status == CheckinStatus.SENT
    assert c.sent_body and "day 2" in c.sent_body


def test_dispatch_failure_retries_then_escalates(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider(fail=True)
    t = NOW + timedelta(days=2, minutes=5)
    for i in range(3):
        followup_service.dispatch_due_checkins(db, provider, now=t + timedelta(minutes=31 * i))
    db.commit()
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    assert c.status == CheckinStatus.SEND_FAILED
    assert c.attempts == 3
    esc = db.query(Escalation).filter_by(trigger="send_failed").one()
    assert esc.patient_id == plan.admission.patient_id


def test_dispatch_respects_retry_window(db: Session, hospital: Hospital):
    make_discharged_plan(db, hospital)
    provider = FakeProvider(fail=True)
    t = NOW + timedelta(days=2, minutes=5)
    followup_service.dispatch_due_checkins(db, provider, now=t)
    # 1 minute later: inside the 30-min retry window, must not attempt again
    followup_service.dispatch_due_checkins(db, provider, now=t + timedelta(minutes=1))
    db.commit()
    c = db.query(FollowUpCheckin).filter_by(day_offset=2).one()
    assert c.attempts == 1


def test_record_response_scores_and_escalates(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=2, minutes=5))
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    resp = followup_service.record_response(db, c, "severe chest pain", provider_message_id="m1")
    db.commit()
    assert resp.red_flag is True
    assert c.status == CheckinStatus.RESPONDED
    esc = db.query(Escalation).filter_by(trigger="red_flag").one()
    assert esc.priority.value == "high"


def test_record_response_idempotent(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=2, minutes=5))
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    r1 = followup_service.record_response(db, c, "fine", provider_message_id="dup")
    r2 = followup_service.record_response(db, c, "fine", provider_message_id="dup")
    db.commit()
    assert r1.id == r2.id


def test_stop_opts_out_and_converts_remaining(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=2, minutes=5))
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    followup_service.record_response(db, c, "STOP", provider_message_id="m-stop")
    db.commit()
    remaining = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.plan_id == plan.id, FollowUpCheckin.day_offset > 2).all()
    assert all(r.status == CheckinStatus.MANUAL for r in remaining)
    assert plan.admission.patient.messaging_opted_out is True
    assert db.query(Escalation).filter_by(trigger="opted_out").count() == 1


def test_two_consecutive_no_responses_escalate(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    # send day-2 and day-7, answer neither
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=7, minutes=5))
    # both sent; 48h later they are stale
    followup_service.mark_no_responses(db, now=NOW + timedelta(days=9, hours=1))
    db.commit()
    stale = db.query(FollowUpCheckin).filter_by(status=CheckinStatus.NO_RESPONSE).count()
    assert stale == 2
    assert db.query(Escalation).filter_by(trigger="no_response").count() == 1
