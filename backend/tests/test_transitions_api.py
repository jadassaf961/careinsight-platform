"""Transitions API + config/role prerequisites."""
from __future__ import annotations

from app.core.config import Settings
from app.models.user import RoleName


def test_pharmacist_role_exists():
    assert RoleName.PHARMACIST.value == "pharmacist"


def test_settings_have_messaging_defaults():
    s = Settings(_env_file=None)
    assert s.messaging_provider == "simulated"
    assert s.checkin_day_offsets_list == [2, 7, 14, 30]
    assert s.checkin_no_response_hours == 48
    assert s.checkin_max_attempts == 3


from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models.hospital import Hospital  # noqa: E402
from app.models.user import User  # noqa: E402
from tests.test_transition_service import make_admission  # noqa: E402


def _mk_plan(auth_client: TestClient, admission_id: str):
    return auth_client.post("/api/v1/transitions/plans", json={"admission_id": admission_id})


def test_create_plan_and_list_tasks(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    resp = _mk_plan(auth_client, str(adm.id))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "planning"
    assert len(body["tasks"]) >= 5
    assert {"role", "title", "status", "source"} <= set(body["tasks"][0])


def test_create_plan_duplicate_409(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    assert _mk_plan(auth_client, str(adm.id)).status_code == 201
    assert _mk_plan(auth_client, str(adm.id)).status_code == 409


def test_tenancy_cross_hospital_404(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    from app.models.hospital import Department
    other = Hospital(name="Other", slug="other")
    db.add(other)
    db.flush()
    db.add(Department(hospital_id=other.id, name="Med", code="MED"))
    db.commit()
    adm = make_admission(db, other)  # belongs to the other hospital
    auth_client.set_user(physician)  # physician is in `hospital`
    assert _mk_plan(auth_client, str(adm.id)).status_code == 404


def test_complete_task(auth_client: TestClient, db: Session, hospital: Hospital, physician: User, nurse: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    plan = _mk_plan(auth_client, str(adm.id)).json()
    auth_client.set_user(nurse)
    task_id = plan["tasks"][0]["id"]
    resp = auth_client.patch(f"/api/v1/transitions/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_board_lists_active_admissions(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    _mk_plan(auth_client, str(adm.id))
    resp = auth_client.get("/api/v1/transitions/board")
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    row = next(r for r in rows if r["admission_id"] == str(adm.id))
    assert row["plan_status"] == "planning"
    assert row["open_tasks"] >= 5
    assert "case_manager" in row["open_task_roles"]


def test_discharge_endpoint_schedules_checkins(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    from app.models.followup import FollowUpCheckin
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    plan = _mk_plan(auth_client, str(adm.id)).json()
    resp = auth_client.post(f"/api/v1/transitions/plans/{plan['id']}/discharge")
    assert resp.status_code == 200
    assert resp.json()["status"] == "discharged"
    assert db.query(FollowUpCheckin).count() == 4


def test_my_tasks(auth_client: TestClient, db: Session, hospital: Hospital, physician: User, nurse: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    _mk_plan(auth_client, str(adm.id))
    auth_client.set_user(nurse)
    resp = auth_client.get("/api/v1/transitions/tasks/mine")
    assert resp.status_code == 200
    tasks = resp.json()
    assert all(t["role"] == "nurse" and t["status"] == "open" for t in tasks)
    assert len(tasks) >= 1
