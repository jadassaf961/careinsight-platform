"""Escalation queue API — list, RBAC on resolve, resolution flow."""
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.user import User
from app.services import followup_service
from tests.test_followup_service import NOW, FakeProvider, make_discharged_plan


def _escalate(db, hospital) -> None:
    plan = make_discharged_plan(db, hospital)
    followup_service.dispatch_due_checkins(db, FakeProvider(), now=NOW + timedelta(days=2, minutes=5))
    from app.models.followup import FollowUpCheckin
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    followup_service.record_response(db, c, "severe chest pain", provider_message_id="e1")
    db.commit()


def test_queue_lists_open_escalations(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    _escalate(db, hospital)
    auth_client.set_user(nurse)
    resp = auth_client.get("/api/v1/escalations?status=open")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["trigger"] == "red_flag"
    assert items[0]["priority"] == "high"
    assert items[0]["patient_name"]


def test_resolve_escalation_requires_case_manager(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    _escalate(db, hospital)
    auth_client.set_user(nurse)
    esc_id = auth_client.get("/api/v1/escalations?status=open").json()[0]["id"]
    resp = auth_client.patch(f"/api/v1/escalations/{esc_id}", json={
        "status": "resolved", "resolution_notes": "called patient"})
    assert resp.status_code == 403  # nurses can view, not resolve


def test_resolve_escalation_as_case_manager(auth_client: TestClient, db: Session, hospital: Hospital):
    from app.models.user import RoleName
    from tests.conftest import _make_user
    cm = _make_user(db, hospital, RoleName.CASE_MANAGER)
    _escalate(db, hospital)
    auth_client.set_user(cm)
    esc_id = auth_client.get("/api/v1/escalations?status=open").json()[0]["id"]
    resp = auth_client.patch(f"/api/v1/escalations/{esc_id}", json={
        "status": "resolved", "resolution_notes": "called patient, meds adjusted"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"
    assert auth_client.get("/api/v1/escalations?status=open").json() == []
