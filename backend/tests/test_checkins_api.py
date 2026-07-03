"""Check-in timeline + demo-mode simulated reply endpoint."""
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.user import User
from app.services import followup_service
from tests.test_followup_service import NOW, FakeProvider, make_discharged_plan


def test_checkin_timeline_for_patient(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    plan = make_discharged_plan(db, hospital)
    auth_client.set_user(nurse)
    resp = auth_client.get(f"/api/v1/checkins?patient_id={plan.admission.patient_id}")
    assert resp.status_code == 200
    items = resp.json()
    assert [i["day_offset"] for i in items] == [2, 7, 14, 30]
    assert items[0]["responses"] == []


def test_simulate_reply_records_response(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    plan = make_discharged_plan(db, hospital)
    followup_service.dispatch_due_checkins(db, FakeProvider(), now=NOW + timedelta(days=2, minutes=5))
    db.commit()
    auth_client.set_user(nurse)
    timeline = auth_client.get(f"/api/v1/checkins?patient_id={plan.admission.patient_id}").json()
    sent = next(i for i in timeline if i["status"] == "sent")
    resp = auth_client.post(f"/api/v1/checkins/{sent['id']}/simulate-reply", json={"text": "chest pain"})
    assert resp.status_code == 200
    assert resp.json()["red_flag"] is True
