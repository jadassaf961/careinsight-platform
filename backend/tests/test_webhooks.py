"""Inbound messaging webhook: matching, idempotency, unknown senders, signatures."""
from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.followup import CheckinResponse, Escalation
from app.models.hospital import Hospital
from app.services import followup_service
from tests.test_followup_service import NOW, FakeProvider, make_discharged_plan

WEBHOOK_PATH = "/api/v1/webhooks/messaging"


def _sign(params: dict[str, str]) -> str:
    url = f"http://testserver{WEBHOOK_PATH}"
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(settings.twilio_auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _post(client: TestClient, params: dict[str, str], sig: str | None = None):
    return client.post(
        WEBHOOK_PATH, data=params,
        headers={"X-Twilio-Signature": sig if sig is not None else _sign(params)},
    )


def _setup(db, hospital):
    settings.twilio_auth_token = "test-token"  # noqa: S105 - test only
    plan = make_discharged_plan(db, hospital, phone="+96170000001")
    followup_service.dispatch_due_checkins(db, FakeProvider(), now=NOW + timedelta(days=2, minutes=5))
    db.commit()
    return plan


def test_inbound_reply_matched_to_latest_sent_checkin(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    resp = _post(client, {"From": "whatsapp:+96170000001", "Body": "chest pain", "MessageSid": "SM1"})
    assert resp.status_code == 200
    saved = db.query(CheckinResponse).one()
    assert saved.red_flag is True


def test_duplicate_message_sid_idempotent(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    p = {"From": "whatsapp:+96170000001", "Body": "fine", "MessageSid": "SMdup"}
    _post(client, p)
    _post(client, p)
    assert db.query(CheckinResponse).count() == 1


def test_unknown_sender_flagged_not_dropped(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    resp = _post(client, {"From": "whatsapp:+96170009999", "Body": "hello", "MessageSid": "SM2"})
    assert resp.status_code == 200
    esc = db.query(Escalation).filter_by(trigger="unmatched_message").one()
    assert "+96170009999" in esc.detail


def test_bad_signature_rejected(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    resp = _post(client, {"From": "whatsapp:+96170000001", "Body": "hi", "MessageSid": "SM3"},
                 sig="bogus")
    assert resp.status_code == 403
