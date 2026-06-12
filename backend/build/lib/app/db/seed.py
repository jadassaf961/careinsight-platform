"""Development seed script.

Creates one hospital, one department, one user per role, and a placeholder
active model version row. Intended for local development only.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.hospital import Department, Hospital
from app.models.patient import Admission, Patient
from app.models.prediction import ModelVersion
from app.models.user import Role, RoleName, User

logger = get_logger(__name__)


_DEMO_USERS = [
    (RoleName.ADMIN, "admin@careinsight.dev", "Demo Admin"),
    (RoleName.PHYSICIAN, "physician@careinsight.dev", "Dr. Demo Physician"),
    (RoleName.RESIDENT, "resident@careinsight.dev", "Dr. Demo Resident"),
    (RoleName.NURSE, "nurse@careinsight.dev", "Nurse Demo"),
    (RoleName.CASE_MANAGER, "casemanager@careinsight.dev", "Demo Case Manager"),
    (RoleName.ANALYST, "analyst@careinsight.dev", "Demo Analyst"),
]


_DEMO_PATIENTS = [
    {
        "mrn": "MRN0001",
        "first_name": "Alex",
        "last_name": "Rivera",
        "dob": date(1958, 3, 12),
        "sex": "Male",
        "admission": {
            "admission_type": "Emergency",
            "length_of_stay": 6.0,
            "clinical_features": {
                "age": 68, "weight_kg": 78, "height_cm": 172, "bmi": 26.4,
                "num_previous_admissions": 3, "medications_count": 9,
                "last_hemoglobin": 12.1, "last_glucose": 198, "last_creatinine": 1.6,
                "length_of_stay": 6, "procedures_count": 2,
                "gender": "Male", "chronic_conditions": "Heart Disease",
                "admission_type": "Emergency", "smoking_status": "Former",
                "alcohol_use": "Moderate", "physical_activity": "Low",
                "insurance_type": "Public", "followup_compliance": "Poor",
                "social_support": "Weak", "mental_health_issue": "No",
            },
        },
    },
    {
        "mrn": "MRN0002",
        "first_name": "Sara",
        "last_name": "Khalil",
        "dob": date(1972, 9, 24),
        "sex": "Female",
        "admission": {
            "admission_type": "Elective",
            "length_of_stay": 2.0,
            "clinical_features": {
                "age": 53, "weight_kg": 64, "height_cm": 165, "bmi": 23.5,
                "num_previous_admissions": 0, "medications_count": 3,
                "last_hemoglobin": 13.5, "last_glucose": 105, "last_creatinine": 0.9,
                "length_of_stay": 2, "procedures_count": 1,
                "gender": "Female", "chronic_conditions": "Hypertension",
                "admission_type": "Elective", "smoking_status": "Never",
                "alcohol_use": "Moderate", "physical_activity": "Medium",
                "insurance_type": "Private", "followup_compliance": "Good",
                "social_support": "Strong", "mental_health_issue": "No",
            },
        },
    },
    {
        "mrn": "MRN0003",
        "first_name": "Marcus",
        "last_name": "Patel",
        "dob": date(1945, 1, 7),
        "sex": "Male",
        "admission": {
            "admission_type": "Urgent",
            "length_of_stay": 11.0,
            "clinical_features": {
                "age": 81, "weight_kg": 70, "height_cm": 168, "bmi": 24.8,
                "num_previous_admissions": 5, "medications_count": 14,
                "last_hemoglobin": 10.4, "last_glucose": 220, "last_creatinine": 2.1,
                "length_of_stay": 11, "procedures_count": 3,
                "gender": "Male", "chronic_conditions": "Diabetes",
                "admission_type": "Urgent", "smoking_status": "Current",
                "alcohol_use": "High", "physical_activity": "Low",
                "insurance_type": "Public", "followup_compliance": "Poor",
                "social_support": "Weak", "mental_health_issue": "Yes",
            },
        },
    },
]


def seed_all(db: Session) -> None:
    if db.query(Hospital).first():
        logger.info("Seed data already present, skipping.")
        return

    logger.info("Seeding demo data…")
    hospital = Hospital(
        name="CareInsight Demo Hospital", slug="careinsight-demo", ehr_vendor="fhir",
    )
    db.add(hospital)
    db.flush()

    dept = Department(hospital_id=hospital.id, name="Internal Medicine", code="IM")
    db.add(dept)
    db.flush()

    roles: dict[RoleName, Role] = {}
    for r in RoleName:
        role = Role(name=r, description=f"{r.value} role")
        db.add(role)
        roles[r] = role
    db.flush()

    pw = hash_password(settings.seed_password)
    for role_name, email, full_name in _DEMO_USERS:
        db.add(User(
            hospital_id=hospital.id, role_id=roles[role_name].id,
            email=email, full_name=full_name, password_hash=pw, is_active=True,
        ))

    # Placeholder active model version — the ml-service will overwrite on first /retrain
    db.add(ModelVersion(
        name="readmission_classifier", version="0.1.0", algorithm="placeholder",
        artifact_uri="registry/placeholder", is_active=True,
        trained_at=datetime.now(timezone.utc),
    ))
    db.flush()

    for p in _DEMO_PATIENTS:
        patient = Patient(
            hospital_id=hospital.id, mrn=p["mrn"],
            first_name=p["first_name"], last_name=p["last_name"],
            dob=p["dob"], sex=p["sex"],
        )
        db.add(patient)
        db.flush()
        adm = p["admission"]
        db.add(Admission(
            patient_id=patient.id, department_id=dept.id,
            admission_type=adm["admission_type"],
            admitted_at=datetime.now(timezone.utc) - timedelta(days=2),
            length_of_stay=adm["length_of_stay"],
            clinical_features=adm["clinical_features"],
        ))

    db.commit()
    logger.info("Seed complete. Demo password: %s", settings.seed_password)


def main() -> None:
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
