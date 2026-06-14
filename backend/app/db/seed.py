"""Development seed script — 25 patients across 4 departments with pre-seeded predictions."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.hospital import Department, Hospital
from app.models.patient import Admission, Patient
from app.models.prediction import ModelVersion, Prediction, Recommendation, RiskFactor
from app.models.user import Role, RoleName, User
from app.services.checklist_service import generate_checklist

logger = get_logger(__name__)


_DEMO_USERS = [
    (RoleName.ADMIN, "admin@careinsight.dev", "Demo Admin"),
    (RoleName.PHYSICIAN, "physician@careinsight.dev", "Dr. Demo Physician"),
    (RoleName.RESIDENT, "resident@careinsight.dev", "Dr. Demo Resident"),
    (RoleName.NURSE, "nurse@careinsight.dev", "Nurse Demo"),
    (RoleName.CASE_MANAGER, "casemanager@careinsight.dev", "Demo Case Manager"),
    (RoleName.ANALYST, "analyst@careinsight.dev", "Demo Analyst"),
]

_DEPARTMENTS = [
    {"name": "Internal Medicine", "code": "IM"},
    {"name": "Cardiology", "code": "CARD"},
    {"name": "Endocrinology", "code": "ENDO"},
    {"name": "General Surgery", "code": "GS"},
]

# Each entry: (mrn, first, last, dob, sex, dept_code, adm_type, los_days,
#              clinical_features, probability, risk_tier,
#              [(feature_name, humanized_label, shap_value), ...] top-3 factors)
_PATIENTS: list[tuple] = [
    # ── HIGH RISK ────────────────────────────────────────────────────────────
    ("MRN0001", "Alex", "Rivera", date(1958, 3, 12), "Male", "IM", "Emergency", 6,
     {"age": 68, "weight_kg": 78, "height_cm": 172, "bmi": 26.4,
      "num_previous_admissions": 3, "medications_count": 9,
      "last_hemoglobin": 12.1, "last_glucose": 198, "last_creatinine": 1.6,
      "length_of_stay": 6, "procedures_count": 2,
      "gender": "Male", "chronic_conditions": "Heart Disease",
      "admission_type": "Emergency", "smoking_status": "Former",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Public", "followup_compliance": "Poor",
      "social_support": "Weak", "mental_health_issue": "No"},
     0.83, "High",
     [("chronic_conditions_Heart Disease", "Chronic condition: Heart Disease", 0.44),
      ("followup_compliance_Poor", "Follow-up compliance: Poor", 0.38),
      ("num_previous_admissions", "Prior hospital admissions", 0.31)]),

    ("MRN0003", "Marcus", "Patel", date(1945, 1, 7), "Male", "IM", "Urgent", 11,
     {"age": 81, "weight_kg": 70, "height_cm": 168, "bmi": 24.8,
      "num_previous_admissions": 5, "medications_count": 14,
      "last_hemoglobin": 10.4, "last_glucose": 220, "last_creatinine": 2.1,
      "length_of_stay": 11, "procedures_count": 3,
      "gender": "Male", "chronic_conditions": "Diabetes",
      "admission_type": "Urgent", "smoking_status": "Current",
      "alcohol_use": "High", "physical_activity": "Low",
      "insurance_type": "Public", "followup_compliance": "Poor",
      "social_support": "Weak", "mental_health_issue": "Yes"},
     0.89, "High",
     [("age", "Patient age", 0.51),
      ("num_previous_admissions", "Prior hospital admissions", 0.47),
      ("last_creatinine", "Kidney function (creatinine)", 0.38)]),

    ("MRN-NW01", "George", "Mansour", date(1952, 6, 18), "Male", "CARD", "Emergency", 8,
     {"age": 74, "weight_kg": 82, "height_cm": 175, "bmi": 26.8,
      "num_previous_admissions": 4, "medications_count": 12,
      "last_hemoglobin": 11.2, "last_glucose": 165, "last_creatinine": 1.8,
      "length_of_stay": 8, "procedures_count": 2,
      "gender": "Male", "chronic_conditions": "Heart Disease",
      "admission_type": "Emergency", "smoking_status": "Former",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Private", "followup_compliance": "Poor",
      "social_support": "Weak", "mental_health_issue": "No"},
     0.86, "High",
     [("chronic_conditions_Heart Disease", "Chronic condition: Heart Disease", 0.48),
      ("age", "Patient age", 0.43),
      ("followup_compliance_Poor", "Follow-up compliance: Poor", 0.36)]),

    ("MRN-NW02", "Layla", "Hassan", date(1957, 11, 3), "Female", "CARD", "Emergency", 7,
     {"age": 69, "weight_kg": 64, "height_cm": 160, "bmi": 25.0,
      "num_previous_admissions": 3, "medications_count": 10,
      "last_hemoglobin": 11.8, "last_glucose": 145, "last_creatinine": 1.4,
      "length_of_stay": 7, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "COPD",
      "admission_type": "Emergency", "smoking_status": "Current",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Public", "followup_compliance": "Poor",
      "social_support": "Weak", "mental_health_issue": "Yes"},
     0.78, "High",
     [("chronic_conditions_COPD", "Chronic condition: COPD", 0.42),
      ("smoking_status_Current", "Smoking status: Current", 0.38),
      ("mental_health_issue_Yes", "Mental health issue", 0.30)]),

    ("MRN-NW03", "Joseph", "Khalil", date(1949, 4, 22), "Male", "IM", "Urgent", 9,
     {"age": 77, "weight_kg": 88, "height_cm": 173, "bmi": 29.4,
      "num_previous_admissions": 3, "medications_count": 11,
      "last_hemoglobin": 12.0, "last_glucose": 188, "last_creatinine": 1.5,
      "length_of_stay": 9, "procedures_count": 2,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Urgent", "smoking_status": "Former",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Private", "followup_compliance": "Poor",
      "social_support": "Weak", "mental_health_issue": "No"},
     0.72, "High",
     [("age", "Patient age", 0.40),
      ("bmi", "Body mass index", 0.34),
      ("followup_compliance_Poor", "Follow-up compliance: Poor", 0.32)]),

    ("MRN-NW04", "Miriam", "Raad", date(1944, 8, 15), "Female", "ENDO", "Emergency", 10,
     {"age": 82, "weight_kg": 60, "height_cm": 155, "bmi": 25.0,
      "num_previous_admissions": 6, "medications_count": 16,
      "last_hemoglobin": 10.1, "last_glucose": 280, "last_creatinine": 2.4,
      "length_of_stay": 10, "procedures_count": 3,
      "gender": "Female", "chronic_conditions": "Diabetes",
      "admission_type": "Emergency", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Public", "followup_compliance": "Poor",
      "social_support": "Weak", "mental_health_issue": "No"},
     0.87, "High",
     [("last_glucose", "Glucose level", 0.52),
      ("last_creatinine", "Kidney function (creatinine)", 0.45),
      ("num_previous_admissions", "Prior hospital admissions", 0.41)]),

    # ── MEDIUM RISK ──────────────────────────────────────────────────────────
    ("MRN0002", "Sara", "Khalil", date(1972, 9, 24), "Female", "IM", "Elective", 2,
     {"age": 53, "weight_kg": 64, "height_cm": 165, "bmi": 23.5,
      "num_previous_admissions": 0, "medications_count": 3,
      "last_hemoglobin": 13.5, "last_glucose": 105, "last_creatinine": 0.9,
      "length_of_stay": 2, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.42, "Medium",
     [("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.28),
      ("medications_count", "Number of medications", 0.18),
      ("age", "Patient age", 0.14)]),

    ("MRN-NW05", "Rami", "Gemayel", date(1968, 2, 14), "Male", "CARD", "Elective", 3,
     {"age": 58, "weight_kg": 85, "height_cm": 178, "bmi": 26.8,
      "num_previous_admissions": 1, "medications_count": 6,
      "last_hemoglobin": 13.8, "last_glucose": 118, "last_creatinine": 1.0,
      "length_of_stay": 3, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Former",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.48, "Medium",
     [("smoking_status_Former", "Smoking status: Former", 0.26),
      ("bmi", "Body mass index", 0.20),
      ("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.18)]),

    ("MRN-NW06", "Nadia", "Haddad", date(1964, 5, 30), "Female", "IM", "Urgent", 4,
     {"age": 62, "weight_kg": 70, "height_cm": 162, "bmi": 26.7,
      "num_previous_admissions": 2, "medications_count": 7,
      "last_hemoglobin": 12.4, "last_glucose": 155, "last_creatinine": 1.1,
      "length_of_stay": 4, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Diabetes",
      "admission_type": "Urgent", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.55, "Medium",
     [("chronic_conditions_Diabetes", "Chronic condition: Diabetes", 0.32),
      ("last_glucose", "Glucose level", 0.27),
      ("physical_activity_Low", "Physical activity: Low", 0.20)]),

    ("MRN-NW07", "Karim", "Saad", date(1971, 7, 8), "Male", "GS", "Elective", 3,
     {"age": 55, "weight_kg": 90, "height_cm": 180, "bmi": 27.8,
      "num_previous_admissions": 1, "medications_count": 4,
      "last_hemoglobin": 14.0, "last_glucose": 112, "last_creatinine": 1.0,
      "length_of_stay": 3, "procedures_count": 2,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Current",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.43, "Medium",
     [("smoking_status_Current", "Smoking status: Current", 0.30),
      ("bmi", "Body mass index", 0.22),
      ("procedures_count", "Procedures performed", 0.15)]),

    ("MRN-NW08", "May", "Farhat", date(1966, 10, 19), "Female", "ENDO", "Urgent", 5,
     {"age": 60, "weight_kg": 72, "height_cm": 161, "bmi": 27.8,
      "num_previous_admissions": 2, "medications_count": 8,
      "last_hemoglobin": 12.6, "last_glucose": 168, "last_creatinine": 1.1,
      "length_of_stay": 5, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Diabetes",
      "admission_type": "Urgent", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Public", "followup_compliance": "Poor",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.59, "Medium",
     [("followup_compliance_Poor", "Follow-up compliance: Poor", 0.34),
      ("chronic_conditions_Diabetes", "Chronic condition: Diabetes", 0.29),
      ("last_glucose", "Glucose level", 0.24)]),

    ("MRN-NW09", "Pierre", "Tabet", date(1976, 3, 5), "Male", "CARD", "Elective", 2,
     {"age": 50, "weight_kg": 80, "height_cm": 175, "bmi": 26.1,
      "num_previous_admissions": 1, "medications_count": 5,
      "last_hemoglobin": 14.2, "last_glucose": 108, "last_creatinine": 0.9,
      "length_of_stay": 2, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Heart Disease",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.52, "Medium",
     [("chronic_conditions_Heart Disease", "Chronic condition: Heart Disease", 0.35),
      ("age", "Patient age", 0.18),
      ("medications_count", "Number of medications", 0.14)]),

    ("MRN-NW10", "Lina", "Khoury", date(1975, 12, 1), "Female", "GS", "Elective", 2,
     {"age": 51, "weight_kg": 67, "height_cm": 163, "bmi": 25.2,
      "num_previous_admissions": 1, "medications_count": 4,
      "last_hemoglobin": 13.1, "last_glucose": 102, "last_creatinine": 0.8,
      "length_of_stay": 2, "procedures_count": 2,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.47, "Medium",
     [("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.26),
      ("procedures_count", "Procedures performed", 0.20),
      ("age", "Patient age", 0.14)]),

    ("MRN-NW11", "Fadi", "Abi Nader", date(1962, 9, 14), "Male", "IM", "Emergency", 6,
     {"age": 64, "weight_kg": 76, "height_cm": 170, "bmi": 26.3,
      "num_previous_admissions": 2, "medications_count": 9,
      "last_hemoglobin": 12.2, "last_glucose": 130, "last_creatinine": 1.2,
      "length_of_stay": 6, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "COPD",
      "admission_type": "Emergency", "smoking_status": "Current",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Public", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.61, "Medium",
     [("smoking_status_Current", "Smoking status: Current", 0.38),
      ("chronic_conditions_COPD", "Chronic condition: COPD", 0.33),
      ("physical_activity_Low", "Physical activity: Low", 0.24)]),

    ("MRN-NW12", "Rita", "Ghanem", date(1969, 4, 28), "Female", "ENDO", "Elective", 3,
     {"age": 57, "weight_kg": 65, "height_cm": 158, "bmi": 26.0,
      "num_previous_admissions": 1, "medications_count": 6,
      "last_hemoglobin": 12.8, "last_glucose": 148, "last_creatinine": 0.9,
      "length_of_stay": 3, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Diabetes",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.44, "Medium",
     [("chronic_conditions_Diabetes", "Chronic condition: Diabetes", 0.30),
      ("last_glucose", "Glucose level", 0.22),
      ("age", "Patient age", 0.14)]),

    ("MRN-NW13", "Sami", "Mrad", date(1960, 1, 11), "Male", "CARD", "Urgent", 4,
     {"age": 66, "weight_kg": 83, "height_cm": 174, "bmi": 27.4,
      "num_previous_admissions": 2, "medications_count": 8,
      "last_hemoglobin": 13.0, "last_glucose": 125, "last_creatinine": 1.2,
      "length_of_stay": 4, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Urgent", "smoking_status": "Former",
      "alcohol_use": "Moderate", "physical_activity": "Low",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.58, "Medium",
     [("age", "Patient age", 0.28),
      ("physical_activity_Low", "Physical activity: Low", 0.24),
      ("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.20)]),

    ("MRN-NW14", "Diana", "Wehbe", date(1981, 6, 22), "Female", "GS", "Elective", 2,
     {"age": 45, "weight_kg": 63, "height_cm": 164, "bmi": 23.4,
      "num_previous_admissions": 1, "medications_count": 3,
      "last_hemoglobin": 13.5, "last_glucose": 98, "last_creatinine": 0.8,
      "length_of_stay": 2, "procedures_count": 2,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.40, "Medium",
     [("procedures_count", "Procedures performed", 0.24),
      ("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.18),
      ("age", "Patient age", 0.12)]),

    ("MRN-NW15", "Tony", "Azzi", date(1973, 8, 7), "Male", "IM", "Elective", 3,
     {"age": 53, "weight_kg": 79, "height_cm": 172, "bmi": 26.7,
      "num_previous_admissions": 1, "medications_count": 5,
      "last_hemoglobin": 13.7, "last_glucose": 110, "last_creatinine": 1.0,
      "length_of_stay": 3, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Former",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.51, "Medium",
     [("smoking_status_Former", "Smoking status: Former", 0.24),
      ("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.20),
      ("bmi", "Body mass index", 0.14)]),

    # ── LOW RISK ─────────────────────────────────────────────────────────────
    ("MRN-NW16", "Maya", "Bou Diab", date(1994, 2, 14), "Female", "GS", "Elective", 1,
     {"age": 32, "weight_kg": 58, "height_cm": 162, "bmi": 22.1,
      "num_previous_admissions": 0, "medications_count": 1,
      "last_hemoglobin": 14.2, "last_glucose": 90, "last_creatinine": 0.7,
      "length_of_stay": 1, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "High",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.12, "Low",
     [("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.08),
      ("age", "Patient age", 0.05),
      ("length_of_stay", "Length of stay", 0.04)]),

    ("MRN-NW17", "Charbel", "Nasr", date(1998, 9, 3), "Male", "GS", "Elective", 1,
     {"age": 28, "weight_kg": 72, "height_cm": 179, "bmi": 22.5,
      "num_previous_admissions": 0, "medications_count": 0,
      "last_hemoglobin": 15.1, "last_glucose": 88, "last_creatinine": 0.8,
      "length_of_stay": 1, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "High",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.10, "Low",
     [("age", "Patient age", 0.06),
      ("length_of_stay", "Length of stay", 0.04),
      ("procedures_count", "Procedures performed", 0.03)]),

    ("MRN-NW18", "Ana", "Atallah", date(1988, 7, 19), "Female", "ENDO", "Elective", 2,
     {"age": 38, "weight_kg": 61, "height_cm": 160, "bmi": 23.8,
      "num_previous_admissions": 0, "medications_count": 2,
      "last_hemoglobin": 13.6, "last_glucose": 105, "last_creatinine": 0.7,
      "length_of_stay": 2, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "High",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.18, "Low",
     [("medications_count", "Number of medications", 0.10),
      ("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.09),
      ("age", "Patient age", 0.06)]),

    ("MRN-NW19", "Omar", "Deeb", date(1985, 11, 25), "Male", "IM", "Elective", 2,
     {"age": 41, "weight_kg": 77, "height_cm": 174, "bmi": 25.4,
      "num_previous_admissions": 0, "medications_count": 2,
      "last_hemoglobin": 14.4, "last_glucose": 96, "last_creatinine": 0.9,
      "length_of_stay": 2, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "Medium",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.22, "Low",
     [("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.12),
      ("bmi", "Body mass index", 0.09),
      ("age", "Patient age", 0.07)]),

    ("MRN-NW20", "Sandra", "Khoury", date(1991, 4, 10), "Female", "GS", "Elective", 1,
     {"age": 35, "weight_kg": 60, "height_cm": 163, "bmi": 22.6,
      "num_previous_admissions": 0, "medications_count": 1,
      "last_hemoglobin": 13.8, "last_glucose": 92, "last_creatinine": 0.7,
      "length_of_stay": 1, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "High",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.14, "Low",
     [("procedures_count", "Procedures performed", 0.08),
      ("age", "Patient age", 0.06),
      ("length_of_stay", "Length of stay", 0.04)]),

    ("MRN-NW21", "Marc", "Chaoul", date(1982, 12, 20), "Male", "CARD", "Elective", 2,
     {"age": 44, "weight_kg": 78, "height_cm": 176, "bmi": 25.2,
      "num_previous_admissions": 0, "medications_count": 2,
      "last_hemoglobin": 14.8, "last_glucose": 95, "last_creatinine": 0.9,
      "length_of_stay": 2, "procedures_count": 1,
      "gender": "Male", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "High",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.26, "Low",
     [("chronic_conditions_Hypertension", "Chronic condition: Hypertension", 0.14),
      ("age", "Patient age", 0.10),
      ("medications_count", "Number of medications", 0.06)]),

    ("MRN-NW22", "Joelle", "Moawad", date(1996, 5, 8), "Female", "GS", "Elective", 1,
     {"age": 30, "weight_kg": 55, "height_cm": 158, "bmi": 22.0,
      "num_previous_admissions": 0, "medications_count": 1,
      "last_hemoglobin": 13.2, "last_glucose": 88, "last_creatinine": 0.7,
      "length_of_stay": 1, "procedures_count": 1,
      "gender": "Female", "chronic_conditions": "Hypertension",
      "admission_type": "Elective", "smoking_status": "Never",
      "alcohol_use": "Moderate", "physical_activity": "High",
      "insurance_type": "Private", "followup_compliance": "Good",
      "social_support": "Strong", "mental_health_issue": "No"},
     0.11, "Low",
     [("age", "Patient age", 0.06),
      ("length_of_stay", "Length of stay", 0.04),
      ("procedures_count", "Procedures performed", 0.03)]),
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

    dept_map: dict[str, Department] = {}
    for d in _DEPARTMENTS:
        dept = Department(hospital_id=hospital.id, name=d["name"], code=d["code"])
        db.add(dept)
        dept_map[d["code"]] = dept
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

    mv = ModelVersion(
        name="readmission_classifier", version="0.1.0", algorithm="xgboost",
        artifact_uri="registry/placeholder", is_active=True,
        trained_at=datetime.now(timezone.utc),
        cv_auc=0.812, test_auc=0.794,
    )
    db.add(mv)
    db.flush()

    now = datetime.now(timezone.utc)
    for row in _PATIENTS:
        (mrn, first, last, dob, sex, dept_code,
         adm_type, los, features, prob, tier, factors) = row

        patient = Patient(
            hospital_id=hospital.id, mrn=mrn,
            first_name=first, last_name=last, dob=dob, sex=sex,
        )
        db.add(patient)
        db.flush()

        adm = Admission(
            patient_id=patient.id,
            department_id=dept_map[dept_code].id,
            admission_type=adm_type,
            admitted_at=now - timedelta(days=los + 1),
            length_of_stay=float(los),
            clinical_features=features,
        )
        db.add(adm)
        db.flush()

        pred = Prediction(
            admission_id=adm.id,
            model_version_id=mv.id,
            probability=prob,
            risk_tier=tier,
            threshold_used=0.5,
        )
        db.add(pred)
        db.flush()

        for rank, (feat_name, label, shap_val) in enumerate(factors, start=1):
            db.add(RiskFactor(
                prediction_id=pred.id,
                feature_name=feat_name,
                humanized_label=label,
                shap_value=shap_val,
                rank=rank,
            ))

        top_factors = [(f[0], f[2]) for f in factors]
        for item in generate_checklist(top_factors, tier):
            db.add(Recommendation(
                prediction_id=pred.id,
                text=item["text"],
                category=item["category"],
                source=item["source"],
            ))

    db.commit()
    logger.info("Seed complete. %d patients seeded. Demo password: %s",
                len(_PATIENTS), settings.seed_password)


def main() -> None:
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
