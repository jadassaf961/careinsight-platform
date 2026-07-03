"""Transition plans, tasks, discharge board."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.hospital import Department
from app.models.patient import Admission, Patient
from app.models.transition import TaskStatus, TransitionPlan, TransitionTask
from app.models.user import RoleName, User
from app.schemas.transition import (
    BoardResponse,
    BoardRow,
    PlanCreate,
    PlanRead,
    TaskRead,
    TaskStatusUpdate,
)
from app.services import transition_service

router = APIRouter(prefix="/transitions", tags=["transitions"])


def _get_plan_scoped(db: Session, plan_id: UUID, current: User) -> TransitionPlan:
    plan = db.get(TransitionPlan, plan_id)
    if plan is None or plan.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    body: PlanCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.PHYSICIAN, RoleName.ADMIN, RoleName.CASE_MANAGER)),
) -> PlanRead:
    adm = db.get(Admission, body.admission_id)
    if adm is None or adm.patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Admission not found")
    try:
        plan = transition_service.create_plan(db, adm, current.hospital_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if body.target_discharge_date:
        plan.target_discharge_date = body.target_discharge_date
    db.commit()
    db.refresh(plan)
    return PlanRead.model_validate(plan)


@router.get("/plans/by-patient/{patient_id}", response_model=PlanRead)
def latest_plan_for_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PlanRead:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    plan = (
        db.query(TransitionPlan)
        .join(Admission, TransitionPlan.admission_id == Admission.id)
        .filter(Admission.patient_id == patient_id)
        .order_by(TransitionPlan.created_at.desc())
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="No transition plan for patient")
    return PlanRead.model_validate(plan)


@router.post("/plans/{plan_id}/discharge", response_model=PlanRead)
def discharge(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.ADMIN)),
) -> PlanRead:
    plan = _get_plan_scoped(db, plan_id, current)
    try:
        transition_service.discharge_plan(db, plan, now=datetime.now(timezone.utc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(plan)
    return PlanRead.model_validate(plan)


@router.post("/plans/{plan_id}/refresh-tasks", response_model=PlanRead)
def refresh_tasks(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PlanRead:
    plan = _get_plan_scoped(db, plan_id, current)
    transition_service.refresh_risk_tasks(db, plan)
    db.commit()
    db.refresh(plan)
    return PlanRead.model_validate(plan)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    body: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> TaskRead:
    task = db.get(TransitionTask, task_id)
    if task is None or task.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        task.status = TaskStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid status") from exc
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)


@router.get("/tasks/mine", response_model=list[TaskRead])
def my_tasks(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[TaskRead]:
    tasks = (
        db.query(TransitionTask)
        .filter(
            TransitionTask.hospital_id == current.hospital_id,
            TransitionTask.role == current.role.name.value,
            TransitionTask.status == TaskStatus.OPEN,
        )
        .order_by(TransitionTask.created_at)
        .all()
    )
    return [TaskRead.model_validate(t) for t in tasks]


@router.get("/board", response_model=BoardResponse)
def board(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> BoardResponse:
    admissions = (
        db.query(Admission)
        .join(Patient, Admission.patient_id == Patient.id)
        .filter(
            Patient.hospital_id == current.hospital_id,
            Admission.discharged_at.is_(None),
        )
        .all()
    )
    rows: list[BoardRow] = []
    for adm in admissions:
        pred = adm.predictions[0] if adm.predictions else None
        plan = db.query(TransitionPlan).filter(
            TransitionPlan.admission_id == adm.id).first()
        open_count, roles = (0, [])
        if plan is not None:
            open_count, roles = transition_service.open_task_summary(plan)
        dept = db.get(Department, adm.department_id)
        rows.append(BoardRow(
            patient_id=adm.patient_id, admission_id=adm.id,
            first_name=adm.patient.first_name, last_name=adm.patient.last_name,
            mrn=adm.patient.mrn, department=dept.name if dept else "—",
            probability=pred.probability if pred else None,
            risk_tier=pred.risk_tier if pred else None,
            plan_id=plan.id if plan else None,
            plan_status=plan.status.value if plan else None,
            target_discharge_date=plan.target_discharge_date if plan else None,
            open_tasks=open_count, open_task_roles=roles,
        ))
    rows.sort(key=lambda r: (r.probability or 0), reverse=True)
    return BoardResponse(rows=rows)
