"""Dashboard metrics endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.patient import Admission, Patient
from app.models.prediction import Prediction
from app.models.user import RoleName, User
from app.schemas.dashboard import DashboardMetrics, ReadmissionStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def metrics(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> DashboardMetrics:
    total = db.query(func.count(Patient.id)).filter(
        Patient.hospital_id == current.hospital_id,
        Patient.deleted_at.is_(None),
    ).scalar() or 0

    active = db.query(func.count(Admission.id)).join(Patient).filter(
        Patient.hospital_id == current.hospital_id,
        Admission.discharged_at.is_(None),
    ).scalar() or 0

    high_risk = db.query(func.count(Prediction.id)).join(Admission).join(Patient).filter(
        Patient.hospital_id == current.hospital_id,
        Prediction.risk_tier == "High",
    ).scalar() or 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    last_24h = db.query(func.count(Prediction.id)).join(Admission).join(Patient).filter(
        Patient.hospital_id == current.hospital_id,
        Prediction.created_at >= cutoff,
    ).scalar() or 0

    return DashboardMetrics(
        total_patients=int(total), active_admissions=int(active),
        high_risk_count=int(high_risk), predictions_last_24h=int(last_24h),
    )


@router.get("/readmissions", response_model=ReadmissionStats)
def readmissions(
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST)),
) -> ReadmissionStats:
    total = db.query(func.count(Prediction.id)).join(Admission).join(Patient).filter(
        Patient.hospital_id == current.hospital_id,
    ).scalar() or 0
    high = db.query(func.count(Prediction.id)).join(Admission).join(Patient).filter(
        Patient.hospital_id == current.hospital_id, Prediction.risk_tier == "High",
    ).scalar() or 0
    rate = (high / total) if total else 0.0
    return ReadmissionStats(
        period="all_time", total_predictions=int(total), high_risk_rate=round(rate, 4),
    )
