"""Readmission recording + outcome metrics."""
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.patient import Admission
from app.models.user import User
from tests.test_followup_service import NOW, make_discharged_plan


def _readmit(db: Session, plan, days: int) -> Admission:
    adm = plan.admission
    new = Admission(
        patient_id=adm.patient_id, department_id=adm.department_id,
        admission_type="emergency",
        admitted_at=NOW + timedelta(days=days), clinical_features={},
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def test_record_readmission_links_prior_discharge(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    plan = make_discharged_plan(db, hospital)
    new = _readmit(db, plan, days=10)
    auth_client.set_user(physician)
    resp = auth_client.post("/api/v1/outcomes/readmissions", json={"admission_id": str(new.id)})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["prior_admission_id"] == str(plan.admission_id)
    assert body["days_since_discharge"] == 10


def test_readmission_outside_30_days_rejected(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    plan = make_discharged_plan(db, hospital)
    new = _readmit(db, plan, days=45)
    auth_client.set_user(physician)
    resp = auth_client.post("/api/v1/outcomes/readmissions", json={"admission_id": str(new.id)})
    assert resp.status_code == 400


def test_metrics_shape(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    plan = make_discharged_plan(db, hospital)
    new = _readmit(db, plan, days=5)
    auth_client.set_user(physician)
    auth_client.post("/api/v1/outcomes/readmissions", json={"admission_id": str(new.id)})
    m = auth_client.get("/api/v1/outcomes/metrics").json()
    assert m["discharges_tracked"] == 1
    assert m["readmissions_30d"] == 1
    assert m["readmission_rate"] == 1.0
    assert m["escalations_open"] == 0
    assert isinstance(m["monthly"], list)
