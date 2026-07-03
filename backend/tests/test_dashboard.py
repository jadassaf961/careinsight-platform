"""Tests for new dashboard endpoints: population and model-stats."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.hospital import Department
from app.models.patient import Admission, Patient
from app.models.prediction import ModelVersion, Prediction, RiskFactor
from app.models.user import User


def _make_model_version(db: Session) -> ModelVersion:
    mv = ModelVersion(
        name="test_model", version="0.1.0", algorithm="xgboost",
        artifact_uri="test/path", is_active=True,
        cv_auc=0.81, test_auc=0.79,
        trained_at=datetime.now(timezone.utc),
    )
    db.add(mv)
    db.flush()
    return mv


def _make_patient_with_prediction(
    db: Session,
    hospital_id,
    dept_id,
    mv_id,
    mrn: str,
    first: str,
    last: str,
    dob: date,
    probability: float,
    risk_tier: str,
    discharged: bool = False,
) -> tuple[Patient, Admission, Prediction]:
    p = Patient(
        hospital_id=hospital_id, mrn=mrn,
        first_name=first, last_name=last, dob=dob, sex="Female",
    )
    db.add(p)
    db.flush()

    now = datetime.now(timezone.utc)
    a = Admission(
        patient_id=p.id, department_id=dept_id, admission_type="Elective",
        admitted_at=now, clinical_features={},
        discharged_at=now if discharged else None,
    )
    db.add(a)
    db.flush()

    pred = Prediction(
        admission_id=a.id, model_version_id=mv_id,
        probability=probability, risk_tier=risk_tier, threshold_used=0.5,
    )
    db.add(pred)
    db.flush()
    return p, a, pred


class TestPopulationEndpoint:
    def test_returns_patients_ranked_highest_first(
        self, auth_client, db: Session, physician: User, hospital
    ):
        dept = db.query(Department).filter(Department.hospital_id == hospital.id).first()
        mv = _make_model_version(db)

        _make_patient_with_prediction(
            db, hospital.id, dept.id, mv.id,
            "LOW001", "Low", "Risk", date(1990, 1, 1), 0.15, "Low",
        )
        _, _, high_pred = _make_patient_with_prediction(
            db, hospital.id, dept.id, mv.id,
            "HIGH001", "High", "Risk", date(1950, 1, 1), 0.82, "High",
        )
        db.add(RiskFactor(
            prediction_id=high_pred.id, feature_name="age",
            humanized_label="Patient age", shap_value=0.4, rank=1,
        ))
        db.commit()

        auth_client.set_user(physician)
        resp = auth_client.get("/api/v1/dashboard/population")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["high_count"] == 1
        assert data["low_count"] == 1
        assert data["patients"][0]["risk_tier"] == "High"
        assert data["patients"][0]["mrn"] == "HIGH001"
        assert data["patients"][0]["top_factor"] == "Patient age"
        assert data["patients"][1]["risk_tier"] == "Low"

    def test_excludes_discharged_admissions(
        self, auth_client, db: Session, physician: User, hospital
    ):
        dept = db.query(Department).filter(Department.hospital_id == hospital.id).first()
        mv = _make_model_version(db)

        _make_patient_with_prediction(
            db, hospital.id, dept.id, mv.id,
            "DISC001", "Gone", "Home", date(1970, 1, 1), 0.75, "High",
            discharged=True,
        )
        db.commit()

        auth_client.set_user(physician)
        resp = auth_client.get("/api/v1/dashboard/population")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_excludes_other_hospital_patients(
        self, auth_client, db: Session, physician: User, hospital
    ):
        from app.models.hospital import Hospital, Department as Dept

        other_hosp = Hospital(name="Other Hospital", slug="other-hosp")
        db.add(other_hosp)
        db.flush()
        other_dept = Dept(hospital_id=other_hosp.id, name="Med", code="MED")
        db.add(other_dept)
        db.flush()
        mv = _make_model_version(db)

        _make_patient_with_prediction(
            db, other_hosp.id, other_dept.id, mv.id,
            "OTHER001", "Other", "Hospital", date(1960, 1, 1), 0.80, "High",
        )
        db.commit()

        auth_client.set_user(physician)
        resp = auth_client.get("/api/v1/dashboard/population")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_risk_tier(
        self, auth_client, db: Session, physician: User, hospital
    ):
        dept = db.query(Department).filter(Department.hospital_id == hospital.id).first()
        mv = _make_model_version(db)

        _make_patient_with_prediction(
            db, hospital.id, dept.id, mv.id,
            "H001", "Alice", "High", date(1950, 1, 1), 0.80, "High",
        )
        _make_patient_with_prediction(
            db, hospital.id, dept.id, mv.id,
            "L001", "Bob", "Low", date(1990, 1, 1), 0.12, "Low",
        )
        db.commit()

        auth_client.set_user(physician)
        resp = auth_client.get("/api/v1/dashboard/population?risk_tier=High")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2      # total is unfiltered count
        assert len(data["patients"]) == 1
        assert data["patients"][0]["risk_tier"] == "High"


class TestModelStatsEndpoint:
    def test_returns_algorithm_and_auc(
        self, auth_client, db: Session, admin_user: User, hospital
    ):
        dept = db.query(Department).filter(Department.hospital_id == hospital.id).first()
        mv = _make_model_version(db)
        _, _, pred = _make_patient_with_prediction(
            db, hospital.id, dept.id, mv.id,
            "STAT001", "Stats", "Patient", date(1970, 1, 1), 0.70, "High",
        )
        db.add(RiskFactor(
            prediction_id=pred.id, feature_name="age",
            humanized_label="Patient age", shap_value=0.4, rank=1,
        ))
        db.commit()

        auth_client.set_user(admin_user)
        resp = auth_client.get("/api/v1/dashboard/model-stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["algorithm"] == "xgboost"
        assert data["cv_auc"] == pytest.approx(0.81)
        assert data["total_predictions"] == 1
        assert data["tier_distribution"]["High"] == 1
        assert data["tier_distribution"]["Medium"] == 0
        assert data["top_features"][0]["feature_name"] == "age"

    def test_non_admin_cannot_access_model_stats(
        self, auth_client, physician: User
    ):
        auth_client.set_user(physician)
        resp = auth_client.get("/api/v1/dashboard/model-stats")
        assert resp.status_code == 403
