"""Transition models + transition_service unit tests."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.followup import (
    CheckinStatus,
    Escalation,
    EscalationPriority,
    EscalationStatus,
    FollowUpCheckin,
    ReadmissionEvent,
)
from app.models.hospital import Department, Hospital
from app.models.patient import Admission, Patient
from app.models.transition import PlanStatus, TaskStatus, TransitionPlan, TransitionTask


def make_admission(db: Session, hospital: Hospital, phone: str | None = "+96170000001") -> Admission:
    dept = db.query(Department).filter(Department.hospital_id == hospital.id).first()
    p = Patient(
        hospital_id=hospital.id, mrn=f"MRN-{datetime.now().timestamp()}",
        first_name="Test", last_name="Patient", dob=datetime(1960, 1, 1).date(),
        sex="F", phone_number=phone,
    )
    db.add(p)
    db.flush()
    adm = Admission(
        patient_id=p.id, department_id=dept.id, admission_type="emergency",
        admitted_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        clinical_features={},
    )
    db.add(adm)
    db.commit()
    db.refresh(adm)
    return adm


def test_models_round_trip(db: Session, hospital: Hospital):
    adm = make_admission(db, hospital)
    plan = TransitionPlan(hospital_id=hospital.id, admission_id=adm.id)
    db.add(plan)
    db.flush()
    db.add(TransitionTask(
        hospital_id=hospital.id, plan_id=plan.id, role="nurse",
        title="Educate patient", source="default",
    ))
    db.add(FollowUpCheckin(
        hospital_id=hospital.id, plan_id=plan.id, patient_id=adm.patient_id,
        day_offset=2, scheduled_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc),
    ))
    db.add(Escalation(
        hospital_id=hospital.id, patient_id=adm.patient_id,
        trigger="red_flag", detail="chest pain", priority=EscalationPriority.HIGH,
    ))
    db.commit()

    saved = db.query(TransitionPlan).one()
    assert saved.status == PlanStatus.PLANNING
    assert saved.tasks[0].status == TaskStatus.OPEN
    assert db.query(FollowUpCheckin).one().status == CheckinStatus.SCHEDULED
    assert db.query(Escalation).one().status == EscalationStatus.OPEN
    assert db.query(ReadmissionEvent).count() == 0


def test_role_for_item_mapping():
    from app.services import transition_service

    assert transition_service.role_for_item("Perform full medication reconciliation before discharge") == "pharmacist"
    assert transition_service.role_for_item("Schedule follow-up appointment within 7 days of discharge") == "case_manager"
    assert transition_service.role_for_item("Nephrology referral; monitor renal function post-discharge") == "case_manager"
    assert transition_service.role_for_item("Provide written discharge summary in patient's preferred language") == "physician"
    assert transition_service.role_for_item("Screen for social determinants: housing, food access, transport") == "nurse"


def test_create_plan_generates_default_tasks(db: Session, hospital: Hospital):
    from app.services import transition_service

    adm = make_admission(db, hospital)
    plan = transition_service.create_plan(db, adm, hospital.id)
    db.commit()
    assert plan.status == PlanStatus.PLANNING
    titles = [t.title for t in plan.tasks]
    assert "Confirm patient has correct medications and understands dosing" in titles
    assert all(t.source == "default" for t in plan.tasks)
    assert {t.role for t in plan.tasks} <= {"physician", "nurse", "case_manager", "pharmacist"}


def test_create_plan_twice_rejected(db: Session, hospital: Hospital):
    import pytest

    from app.services import transition_service

    adm = make_admission(db, hospital)
    transition_service.create_plan(db, adm, hospital.id)
    db.commit()
    with pytest.raises(ValueError):
        transition_service.create_plan(db, adm, hospital.id)


def test_discharge_plan_sets_status_and_discharged_at(db: Session, hospital: Hospital):
    from app.services import transition_service

    adm = make_admission(db, hospital)
    plan = transition_service.create_plan(db, adm, hospital.id)
    db.commit()
    now = datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)
    transition_service.discharge_plan(db, plan, now=now)
    db.commit()
    assert plan.status == PlanStatus.DISCHARGED
    assert db.get(Admission, adm.id).discharged_at is not None
    # check-ins were scheduled (detail asserted in followup tests)
    assert db.query(FollowUpCheckin).filter(FollowUpCheckin.plan_id == plan.id).count() == 4
