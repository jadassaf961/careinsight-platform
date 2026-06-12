"""Report generation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.patient import Admission, Patient
from app.models.prediction import Prediction, Recommendation, RiskFactor
from app.models.report import Report
from app.models.user import RoleName, User
from app.schemas.report import ReportCreate
from app.services.pdf_service import generate_discharge_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/pdf")
def generate_pdf_report(
    body: ReportCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.CASE_MANAGER)),
) -> Response:
    pred = db.get(Prediction, body.prediction_id)
    if pred is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    adm: Admission = pred.admission
    patient: Patient = db.get(Patient, adm.patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=403, detail="Outside hospital scope")

    factors = (
        db.query(RiskFactor).filter(RiskFactor.prediction_id == pred.id)
        .order_by(RiskFactor.rank).all()
    )
    recs = (
        db.query(Recommendation).filter(Recommendation.prediction_id == pred.id).all()
    )

    pdf_bytes = generate_discharge_pdf(
        patient_info={
            "Patient": f"{patient.first_name} {patient.last_name}",
            "MRN": patient.mrn,
            "Date of birth": patient.dob.isoformat(),
            "Sex": patient.sex,
            "Admission type": adm.admission_type,
            "Length of stay": f"{adm.length_of_stay or 0:.0f} days",
        },
        risk_score=pred.probability,
        risk_tier=pred.risk_tier,
        top_factors=[(f.feature_name, f.humanized_label, f.shap_value) for f in factors],
        checklist=[r.text for r in recs],
        model_name=pred.model_version.name,
        threshold=pred.threshold_used,
    )

    db.add(Report(prediction_id=pred.id, generated_by_user_id=current.id))
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; filename=careinsight_{patient.mrn}_{pred.id}.pdf"
            ),
        },
    )
