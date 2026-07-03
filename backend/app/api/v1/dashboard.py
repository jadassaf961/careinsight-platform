"""Dashboard metrics endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.hospital import Department
from app.models.patient import Admission, Patient
from app.models.prediction import ModelVersion, Prediction, RiskFactor
from app.models.user import RoleName, User
from app.schemas.dashboard import (
    DashboardMetrics,
    FeatureImportanceItem,
    ModelStatsResponse,
    PopulationPatientRow,
    PopulationResponse,
    ReadmissionStats,
)

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


@router.get("/population", response_model=PopulationResponse)
def population(
    department: str | None = Query(None, description="Filter by department name"),
    risk_tier: str | None = Query(None, description="Filter by risk tier: High | Medium | Low"),
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PopulationResponse:
    """Return all currently admitted patients ranked by readmission risk, highest first."""
    # Issue 1 fix: use ROW_NUMBER() window function to pick the single latest prediction
    # per admission, breaking created_at ties deterministically (SQLite 3.25+ supports this).
    rn_subq = (
        db.query(
            Prediction.id.label("pred_id"),
            Prediction.admission_id.label("adm_id"),
            func.row_number().over(
                partition_by=Prediction.admission_id,
                order_by=Prediction.created_at.desc(),
            ).label("rn"),
        )
        .join(Admission, Admission.id == Prediction.admission_id)
        .join(Patient, Patient.id == Admission.patient_id)
        .filter(
            Patient.hospital_id == current.hospital_id,
            Patient.deleted_at.is_(None),
            Admission.discharged_at.is_(None),
        )
        .subquery()
    )

    latest_pred_sq = (
        db.query(rn_subq.c.pred_id, rn_subq.c.adm_id)
        .filter(rn_subq.c.rn == 1)
        .subquery()
    )

    # Issue 2 fix: aggregate rank-1 factors to guarantee one row per prediction
    top_factor_sq = (
        db.query(
            RiskFactor.prediction_id,
            func.min(RiskFactor.humanized_label).label("top_factor"),
        )
        .filter(RiskFactor.rank == 1)
        .group_by(RiskFactor.prediction_id)
        .subquery()
    )

    base_q = (
        db.query(
            Patient.id.label("patient_id"),
            Patient.first_name,
            Patient.last_name,
            Patient.mrn,
            Department.name.label("department"),
            Prediction.id.label("prediction_id"),
            Prediction.probability,
            Prediction.risk_tier,
            top_factor_sq.c.top_factor,
        )
        .join(Admission, Admission.patient_id == Patient.id)
        .join(Department, Department.id == Admission.department_id)
        .join(latest_pred_sq, latest_pred_sq.c.adm_id == Admission.id)
        .join(Prediction, Prediction.id == latest_pred_sq.c.pred_id)
        .outerjoin(top_factor_sq, top_factor_sq.c.prediction_id == Prediction.id)
        .filter(
            Patient.hospital_id == current.hospital_id,
            Patient.deleted_at.is_(None),
            Admission.discharged_at.is_(None),
        )
    )

    # Unfiltered counts for summary cards
    all_rows = base_q.all()
    high_count = sum(1 for r in all_rows if r.risk_tier == "High")
    medium_count = sum(1 for r in all_rows if r.risk_tier == "Medium")
    low_count = sum(1 for r in all_rows if r.risk_tier == "Low")
    total = len(all_rows)
    departments = sorted({r.department for r in all_rows})

    # Apply optional filters for displayed rows
    if department:
        all_rows = [r for r in all_rows if r.department == department]
    if risk_tier:
        all_rows = [r for r in all_rows if r.risk_tier == risk_tier]

    # Sort by probability descending
    all_rows.sort(key=lambda r: r.probability, reverse=True)

    return PopulationResponse(
        patients=[
            PopulationPatientRow(
                patient_id=str(r.patient_id),
                first_name=r.first_name,
                last_name=r.last_name,
                mrn=r.mrn,
                department=r.department,
                prediction_id=str(r.prediction_id),
                probability=r.probability,
                risk_tier=r.risk_tier,
                top_factor=r.top_factor,
            )
            for r in all_rows
        ],
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        total=total,
        departments=departments,
    )


@router.get("/model-stats", response_model=ModelStatsResponse)
def model_stats(
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST)),
) -> ModelStatsResponse:
    """Return active model metadata and global feature importances for this hospital."""
    mv = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()

    tier_rows = (
        db.query(Prediction.risk_tier, func.count(Prediction.id))
        .join(Admission, Admission.id == Prediction.admission_id)
        .join(Patient, Patient.id == Admission.patient_id)
        .filter(Patient.hospital_id == current.hospital_id)
        .group_by(Prediction.risk_tier)
        .all()
    )
    tier_distribution: dict[str, int] = {"High": 0, "Medium": 0, "Low": 0}
    for tier, count in tier_rows:
        tier_distribution[tier] = int(count)

    feature_rows = (
        db.query(
            RiskFactor.feature_name,
            RiskFactor.humanized_label,
            func.avg(func.abs(RiskFactor.shap_value)).label("avg_importance"),
        )
        .join(Prediction, Prediction.id == RiskFactor.prediction_id)
        .join(Admission, Admission.id == Prediction.admission_id)
        .join(Patient, Patient.id == Admission.patient_id)
        .filter(Patient.hospital_id == current.hospital_id)
        .group_by(RiskFactor.feature_name, RiskFactor.humanized_label)
        .order_by(func.avg(func.abs(RiskFactor.shap_value)).desc())
        .limit(10)
        .all()
    )

    total_predictions = (
        db.query(func.count(Prediction.id))
        .join(Admission, Admission.id == Prediction.admission_id)
        .join(Patient, Patient.id == Admission.patient_id)
        .filter(Patient.hospital_id == current.hospital_id)
        .scalar() or 0
    )

    return ModelStatsResponse(
        algorithm=mv.algorithm if mv else "unknown",
        version=mv.version if mv else "—",
        trained_at=mv.trained_at if mv else None,
        cv_auc=mv.cv_auc if mv else None,
        test_auc=mv.test_auc if mv else None,
        total_predictions=int(total_predictions),
        tier_distribution=tier_distribution,
        top_features=[
            FeatureImportanceItem(
                feature_name=r.feature_name,
                humanized_label=r.humanized_label,
                avg_importance=round(float(r.avg_importance), 4),
            )
            for r in feature_rows
        ],
    )
