"""Transition plan + task lifecycle. Tasks are generated from the discharge
checklist (base items + risk-factor items when a prediction exists) and
assigned to a role by keyword."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.patient import Admission
from app.models.transition import PlanStatus, TaskStatus, TransitionPlan, TransitionTask
from app.services import followup_service
from app.services.checklist_service import generate_checklist

# Keyword → role routing, checked in order; first match wins.
_ROLE_RULES: list[tuple[tuple[str, ...], str]] = [
    (("medication", "medications", "dosing", "nrt prescription"), "pharmacist"),
    (("follow-up", "referral", "case management", "care coordination",
      "community health", "social work", "benefits"), "case_manager"),
    (("discharge summary", "root cause", "care instructions"), "physician"),
]


def role_for_item(text: str) -> str:
    lowered = text.lower()
    for keywords, role in _ROLE_RULES:
        if any(k in lowered for k in keywords):
            return role
    return "nurse"


def _latest_prediction(admission: Admission):
    return admission.predictions[0] if admission.predictions else None


def _checklist_items(admission: Admission) -> list[dict[str, str]]:
    pred = _latest_prediction(admission)
    if pred is None:
        return generate_checklist([], "low")
    factors = [(f.feature_name, f.shap_value) for f in pred.risk_factors]
    return generate_checklist(factors, pred.risk_tier)


def create_plan(db: Session, admission: Admission, hospital_id: uuid.UUID) -> TransitionPlan:
    existing = db.query(TransitionPlan).filter(
        TransitionPlan.admission_id == admission.id
    ).first()
    if existing is not None:
        raise ValueError("A transition plan already exists for this admission")
    plan = TransitionPlan(hospital_id=hospital_id, admission_id=admission.id)
    db.add(plan)
    db.flush()
    for item in _checklist_items(admission):
        source = "default" if item["source"] == "base" else item["source"]
        db.add(TransitionTask(
            hospital_id=hospital_id, plan_id=plan.id,
            role=role_for_item(item["text"]), title=item["text"], source=source,
        ))
    db.flush()
    db.refresh(plan)
    return plan


def refresh_risk_tasks(db: Session, plan: TransitionPlan) -> int:
    """Append checklist items missing from the plan (e.g. after a new
    prediction). Returns the number of tasks added."""
    admission = plan.admission
    existing_titles = {t.title for t in plan.tasks}
    added = 0
    for item in _checklist_items(admission):
        if item["text"] in existing_titles:
            continue
        source = "default" if item["source"] == "base" else item["source"]
        db.add(TransitionTask(
            hospital_id=plan.hospital_id, plan_id=plan.id,
            role=role_for_item(item["text"]), title=item["text"], source=source,
        ))
        added += 1
    db.flush()
    return added


def discharge_plan(db: Session, plan: TransitionPlan, now: datetime) -> TransitionPlan:
    if plan.status in (PlanStatus.DISCHARGED, PlanStatus.CLOSED):
        raise ValueError("Plan already discharged")
    plan.status = PlanStatus.DISCHARGED
    plan.admission.discharged_at = now
    followup_service.schedule_checkins(db, plan, now=now)
    db.flush()
    return plan


def open_task_summary(plan: TransitionPlan) -> tuple[int, list[str]]:
    open_tasks = [t for t in plan.tasks if t.status == TaskStatus.OPEN]
    roles = sorted({t.role for t in open_tasks})
    return len(open_tasks), roles
