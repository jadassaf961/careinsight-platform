"""Readmission outcome recording + metrics for the admin/investor dashboard."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.followup import (
    CheckinStatus,
    Escalation,
    EscalationStatus,
    FollowUpCheckin,
    ReadmissionEvent,
)
from app.models.patient import Admission
from app.models.transition import PlanStatus, TransitionPlan
from app.models.user import RoleName, User
from app.schemas.followup import OutcomeMetrics, ReadmissionCreate, ReadmissionRead

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("/readmissions", response_model=ReadmissionRead, status_code=status.HTTP_201_CREATED)
def record_readmission(
    body: ReadmissionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.PHYSICIAN, RoleName.ADMIN, RoleName.CASE_MANAGER)),
) -> ReadmissionRead:
    adm = db.get(Admission, body.admission_id)
    if adm is None or adm.patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Admission not found")
    prior = (
        db.query(Admission)
        .filter(
            Admission.patient_id == adm.patient_id,
            Admission.id != adm.id,
            Admission.discharged_at.isnot(None),
            Admission.discharged_at <= adm.admitted_at,
            Admission.discharged_at >= adm.admitted_at - timedelta(days=30),
        )
        .order_by(Admission.discharged_at.desc())
        .first()
    )
    if prior is None:
        raise HTTPException(
            status_code=400,
            detail="No discharge within 30 days before this admission",
        )
    days = (adm.admitted_at - prior.discharged_at).days
    event = ReadmissionEvent(
        hospital_id=current.hospital_id, patient_id=adm.patient_id,
        prior_admission_id=prior.id, readmission_admission_id=adm.id,
        days_since_discharge=days,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return ReadmissionRead.model_validate(event)


@router.get("/metrics", response_model=OutcomeMetrics)
def metrics(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> OutcomeMetrics:
    hid = current.hospital_id
    discharged_plans = db.query(TransitionPlan).filter(
        TransitionPlan.hospital_id == hid,
        TransitionPlan.status.in_([PlanStatus.DISCHARGED, PlanStatus.CLOSED]),
    ).all()
    readmissions = db.query(ReadmissionEvent).filter(
        ReadmissionEvent.hospital_id == hid).all()

    checkins = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.hospital_id == hid,
        FollowUpCheckin.status.in_([
            CheckinStatus.SENT, CheckinStatus.RESPONDED, CheckinStatus.NO_RESPONSE]),
    ).all()
    responded = sum(1 for c in checkins if c.status == CheckinStatus.RESPONDED)

    monthly: dict[str, dict[str, int]] = defaultdict(lambda: {"discharges": 0, "readmissions": 0})
    for plan in discharged_plans:
        if plan.admission.discharged_at:
            key = plan.admission.discharged_at.strftime("%Y-%m")
            monthly[key]["discharges"] += 1
    for ev in readmissions:
        key = ev.created_at.strftime("%Y-%m")
        monthly[key]["readmissions"] += 1

    n_discharges = len(discharged_plans)
    return OutcomeMetrics(
        discharges_tracked=n_discharges,
        readmissions_30d=len(readmissions),
        readmission_rate=(len(readmissions) / n_discharges) if n_discharges else None,
        checkin_response_rate=(responded / len(checkins)) if checkins else None,
        escalations_open=db.query(Escalation).filter(
            Escalation.hospital_id == hid,
            Escalation.status != EscalationStatus.RESOLVED).count(),
        escalations_resolved=db.query(Escalation).filter(
            Escalation.hospital_id == hid,
            Escalation.status == EscalationStatus.RESOLVED).count(),
        monthly=[{"month": k, **v} for k, v in sorted(monthly.items())],
    )
