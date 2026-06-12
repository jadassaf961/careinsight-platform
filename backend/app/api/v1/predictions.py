"""Prediction, risk, explanation, and recommendation endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.patient import Admission, Patient
from app.models.prediction import ModelVersion, Prediction, Recommendation, RiskFactor
from app.models.user import RoleName, User
from app.schemas.prediction import (
    PredictionCreate,
    PredictionRead,
    RecommendationRead,
    RiskExplanationRead,
    RiskFactorRead,
    RiskSummaryRead,
)
from app.services.checklist_service import generate_checklist
from app.services.ml_client import MLClient, MLServiceError

router = APIRouter(tags=["predictions"])
logger = get_logger(__name__)


def _humanize(name: str) -> str:
    """Lightweight feature-name humanizer (mirrors src/features/feature_engineering.py)."""
    LABELS = {
        "age": "Patient age", "bmi": "Body mass index", "length_of_stay": "Length of stay",
        "num_previous_admissions": "Prior hospital admissions",
        "medications_count": "Number of medications",
        "last_hemoglobin": "Hemoglobin level", "last_glucose": "Glucose level",
        "last_creatinine": "Kidney function (creatinine)",
        "procedures_count": "Procedures performed",
        "chronic_conditions": "Chronic condition", "admission_type": "Admission type",
        "smoking_status": "Smoking status", "alcohol_use": "Alcohol use",
        "physical_activity": "Physical activity", "insurance_type": "Insurance",
        "followup_compliance": "Follow-up compliance", "social_support": "Social support",
        "mental_health_issue": "Mental health issue", "weight_kg": "Patient weight",
        "height_cm": "Patient height", "gender": "Gender",
    }
    lower = name.lower()
    for key, label in LABELS.items():
        if key in lower:
            return label
    return name.replace("_", " ").title()


def _active_model(db: Session) -> ModelVersion:
    mv = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()
    if mv is None:
        raise HTTPException(status_code=503, detail="No active model version registered")
    return mv


def _resolve_admission(db: Session, admission_id: UUID, hospital_id: UUID) -> Admission:
    adm = db.get(Admission, admission_id)
    if adm is None:
        raise HTTPException(status_code=404, detail="Admission not found")
    patient = db.get(Patient, adm.patient_id)
    if patient is None or patient.hospital_id != hospital_id:
        raise HTTPException(status_code=403, detail="Admission outside your hospital scope")
    return adm


def _latest_admission_for_patient(db: Session, patient_id: UUID, hospital_id: UUID) -> Admission:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    adms = sorted(patient.admissions, key=lambda a: a.admitted_at, reverse=True)
    if not adms:
        raise HTTPException(status_code=404, detail="Patient has no admissions")
    return adms[0]


# ---------------------------------------------------------------------------
# POST /predictions  &  GET /predictions/{id}
# ---------------------------------------------------------------------------

@router.post("/predictions", response_model=PredictionRead,
             status_code=status.HTTP_201_CREATED)
def create_prediction(
    body: PredictionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.ADMIN)),
) -> PredictionRead:
    adm = _resolve_admission(db, body.admission_id, current.hospital_id)
    mv = _active_model(db)
    threshold = body.threshold if body.threshold is not None else 0.5

    try:
        result = MLClient().predict(adm.clinical_features, threshold=threshold)
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    pred = Prediction(
        admission_id=adm.id, model_version_id=mv.id,
        probability=float(result["probability"]),
        risk_tier=result["risk_tier"],
        threshold_used=threshold,
    )
    db.add(pred)
    db.flush()

    # Also fetch and persist explanations so the chart can render immediately
    try:
        expl = MLClient().explain(adm.clinical_features, top_n=10)
        for rank, factor in enumerate(expl["factors"], start=1):
            db.add(RiskFactor(
                prediction_id=pred.id,
                feature_name=factor["feature_name"],
                humanized_label=_humanize(factor["feature_name"]),
                shap_value=float(factor["shap_value"]),
                rank=rank,
            ))
    except MLServiceError as exc:
        logger.warning("Skipped explain (%s); prediction persisted.", exc)

    # Persist checklist recommendations now too
    top_factors = [
        (rf.feature_name, rf.shap_value)
        for rf in db.query(RiskFactor)
        .filter(RiskFactor.prediction_id == pred.id)
        .order_by(RiskFactor.rank).all()
    ]
    for item in generate_checklist(top_factors, pred.risk_tier):
        db.add(Recommendation(
            prediction_id=pred.id, text=item["text"],
            category=item["category"], source=item["source"],
        ))

    db.commit()
    db.refresh(pred)
    return PredictionRead.model_validate(pred)


@router.get("/predictions/{prediction_id}", response_model=PredictionRead)
def get_prediction(
    prediction_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PredictionRead:
    pred = db.get(Prediction, prediction_id)
    if pred is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    # tenant check via admission → patient → hospital
    patient = db.get(Patient, pred.admission.patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=403, detail="Outside hospital scope")
    return PredictionRead.model_validate(pred)


# ---------------------------------------------------------------------------
# Nested under /patients/{id}
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}/risk", response_model=RiskSummaryRead)
def get_patient_risk(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> RiskSummaryRead:
    adm = _latest_admission_for_patient(db, patient_id, current.hospital_id)
    pred = (
        db.query(Prediction)
        .filter(Prediction.admission_id == adm.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    if pred is None:
        raise HTTPException(
            status_code=404,
            detail="No prediction yet for the latest admission. POST /predictions first.",
        )
    mv = pred.model_version
    return RiskSummaryRead(
        prediction_id=pred.id, probability=pred.probability, risk_tier=pred.risk_tier,
        threshold_used=pred.threshold_used, model_name=mv.name,
        model_version=mv.version, generated_at=pred.created_at,
    )


@router.get("/patients/{patient_id}/explanations", response_model=RiskExplanationRead)
def get_patient_explanations(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.ADMIN, RoleName.PHYSICIAN, RoleName.CASE_MANAGER,
    )),
) -> RiskExplanationRead:
    adm = _latest_admission_for_patient(db, patient_id, current.hospital_id)
    pred = (
        db.query(Prediction).filter(Prediction.admission_id == adm.id)
        .order_by(Prediction.created_at.desc()).first()
    )
    if pred is None:
        raise HTTPException(status_code=404, detail="No prediction yet")
    return RiskExplanationRead(
        prediction_id=pred.id,
        factors=[RiskFactorRead.model_validate(f) for f in pred.risk_factors],
    )


@router.get("/patients/{patient_id}/recommendations",
            response_model=list[RecommendationRead])
def get_patient_recommendations(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.PHYSICIAN, RoleName.NURSE, RoleName.CASE_MANAGER,
    )),
) -> list[RecommendationRead]:
    adm = _latest_admission_for_patient(db, patient_id, current.hospital_id)
    pred = (
        db.query(Prediction).filter(Prediction.admission_id == adm.id)
        .order_by(Prediction.created_at.desc()).first()
    )
    if pred is None:
        raise HTTPException(status_code=404, detail="No prediction yet")
    return [RecommendationRead.model_validate(r) for r in pred.recommendations]
