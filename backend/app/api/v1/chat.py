"""AI Copilot chat endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.patient import Patient
from app.models.prediction import Prediction, RiskFactor
from app.models.user import RoleName, User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_reply

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.CASE_MANAGER)),
) -> ChatResponse:
    patient = db.get(Patient, body.patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")

    latest_pred: Prediction | None = None
    for adm in sorted(patient.admissions, key=lambda a: a.admitted_at, reverse=True):
        if adm.predictions:
            latest_pred = adm.predictions[0]
            break

    context: dict[str, str] = {
        "Patient": f"{patient.first_name} {patient.last_name}",
        "MRN": patient.mrn,
        "Sex": patient.sex,
        "DOB": patient.dob.isoformat(),
    }

    # Enrich with admission clinical features (labs, comorbidities, social factors)
    latest_adm = next(
        iter(sorted(patient.admissions, key=lambda a: a.admitted_at, reverse=True)),
        None,
    )
    if latest_adm:
        context["Admission type"] = latest_adm.admission_type
        if latest_adm.length_of_stay:
            context["Length of stay (days)"] = str(round(latest_adm.length_of_stay, 1))
        _CF_LABELS: dict[str, str] = {
            "age": "Age",
            "bmi": "BMI",
            "medications_count": "Number of active medications",
            "num_previous_admissions": "Prior admissions (lifetime)",
            "last_hemoglobin": "Hemoglobin (g/dL)",
            "last_glucose": "Fasting glucose (mg/dL)",
            "last_creatinine": "Creatinine (mg/dL)",
            "chronic_conditions": "Chronic conditions",
            "smoking_status": "Smoking status",
            "alcohol_use": "Alcohol use",
            "physical_activity": "Physical activity level",
            "followup_compliance": "Follow-up compliance history",
            "social_support": "Social support",
            "mental_health_issue": "Mental health flag",
            "insurance_type": "Insurance type",
            "procedures_count": "Procedures this admission",
        }
        cf = latest_adm.clinical_features or {}
        for key, label in _CF_LABELS.items():
            if key in cf and cf[key] is not None:
                context[label] = str(cf[key])

    if latest_pred is not None:
        context["Predicted readmission probability"] = f"{latest_pred.probability * 100:.0f}%"
        context["Risk tier"] = latest_pred.risk_tier
        top_factors = (
            db.query(RiskFactor)
            .filter(RiskFactor.prediction_id == latest_pred.id)
            .order_by(RiskFactor.rank).limit(6).all()
        )
        for f in top_factors:
            direction = "↑ increases risk" if f.shap_value > 0 else "↓ protective"
            context[f.humanized_label] = f"{direction} (SHAP {f.shap_value:+.3f})"

        # Include pre-generated care recommendations so AI knows what is already planned
        recs = latest_pred.recommendations
        if recs:
            context["Pre-generated care recommendations"] = " | ".join(
                r.text for r in recs[:6]
            )

    reply = generate_reply(
        patient_context=context,
        message=body.message,
        history=[h.model_dump() for h in body.history],
    )
    return ChatResponse(reply=reply)
