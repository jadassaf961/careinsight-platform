# CareInsight Investor Demo Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the CareInsight platform for the Symz Capital investor meeting: add Population Risk Intelligence View, ROI Calculator, Model Transparency page, 25-patient demo data with pre-seeded predictions, and a standalone HTML presentation deck.

**Architecture:** Two new FastAPI endpoints in `dashboard.py`; four new Pydantic schemas; new `WardView.tsx` frontend page; upgraded `AdminDashboard.tsx` with ROI Calculator and Model Transparency; updated routing and nav; standalone `docs/presentation/index.html`. Seed data grows 3 → 25 patients with pre-seeded predictions so the ward view populates without the ML service running.

**Tech Stack:** FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2, React 18, TanStack Query v5, TypeScript 5, Tailwind CSS 3, pytest, Vitest.

---

### Task 1: Expand Seed Data (25 patients, 4 departments, pre-seeded predictions)

**Files:**
- Modify: `backend/app/db/seed.py`

> **After this task:** Reset the dev DB before restarting: `Remove-Item backend\dev.db`

- [ ] **Step 1: Replace `backend/app/db/seed.py` entirely**

```python
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
    for i, row in enumerate(_PATIENTS):
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
```

- [ ] **Step 2: Reset the database and verify**

```powershell
Remove-Item backend\dev.db -ErrorAction SilentlyContinue
```

Then restart the backend (`py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`). Login at `http://localhost:5173` as `physician@careinsight.dev` / `Demo123!` and confirm patient list shows 25 entries.

- [ ] **Step 3: Commit**

```bash
git add backend/app/db/seed.py
git commit -m "feat(seed): expand to 25 patients, 4 departments, pre-seeded predictions"
```

---

### Task 2: Add Population + ModelStats Schemas

**Files:**
- Modify: `backend/app/schemas/dashboard.py`

- [ ] **Step 1: Replace `backend/app/schemas/dashboard.py`**

```python
"""Dashboard metric schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_patients: int
    active_admissions: int
    high_risk_count: int
    predictions_last_24h: int


class ReadmissionStats(BaseModel):
    period: str
    total_predictions: int
    high_risk_rate: float
    note: str = "Placeholder — historical readmission outcomes not yet tracked."


class PopulationPatientRow(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    mrn: str
    department: str
    prediction_id: str
    probability: float
    risk_tier: str
    top_factor: str | None = None


class PopulationResponse(BaseModel):
    patients: list[PopulationPatientRow]
    high_count: int
    medium_count: int
    low_count: int
    total: int


class FeatureImportanceItem(BaseModel):
    feature_name: str
    humanized_label: str
    avg_importance: float


class ModelStatsResponse(BaseModel):
    algorithm: str
    version: str
    trained_at: datetime | None = None
    cv_auc: float | None = None
    test_auc: float | None = None
    total_predictions: int
    tier_distribution: dict[str, int]
    top_features: list[FeatureImportanceItem]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/dashboard.py
git commit -m "feat(schema): add PopulationResponse and ModelStatsResponse schemas"
```

---

### Task 3: Write Failing Tests for Both New Endpoints

**Files:**
- Create: `backend/tests/test_dashboard.py`

- [ ] **Step 1: Create `backend/tests/test_dashboard.py`**

```python
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
        high_p, _, high_pred = _make_patient_with_prediction(
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
        p, a, pred = _make_patient_with_prediction(
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
```

- [ ] **Step 2: Run tests — expect failures (endpoints don't exist yet)**

```powershell
cd backend; py -m pytest tests/test_dashboard.py -v
```

Expected: `FAILED` — `404 Not Found` on both endpoints.

- [ ] **Step 3: Commit the test file**

```bash
git add backend/tests/test_dashboard.py
git commit -m "test(dashboard): add failing tests for population and model-stats endpoints"
```

---

### Task 4: Implement Population Risk Endpoint

**Files:**
- Modify: `backend/app/api/v1/dashboard.py`

- [ ] **Step 1: Replace `backend/app/api/v1/dashboard.py`**

```python
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
    # Subquery: latest prediction timestamp per active admission in this hospital
    latest_pred_sq = (
        db.query(
            Prediction.admission_id,
            func.max(Prediction.created_at).label("latest_at"),
        )
        .join(Admission, Admission.id == Prediction.admission_id)
        .join(Patient, Patient.id == Admission.patient_id)
        .filter(
            Patient.hospital_id == current.hospital_id,
            Patient.deleted_at.is_(None),
            Admission.discharged_at.is_(None),
        )
        .group_by(Prediction.admission_id)
        .subquery()
    )

    # Subquery: top risk factor (rank=1) per prediction
    top_factor_sq = (
        db.query(
            RiskFactor.prediction_id,
            RiskFactor.humanized_label.label("top_factor"),
        )
        .filter(RiskFactor.rank == 1)
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
        .join(latest_pred_sq, latest_pred_sq.c.admission_id == Admission.id)
        .join(
            Prediction,
            (Prediction.admission_id == Admission.id)
            & (Prediction.created_at == latest_pred_sq.c.latest_at),
        )
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
```

- [ ] **Step 2: Run tests — all should pass now**

```powershell
cd backend; py -m pytest tests/test_dashboard.py -v
```

Expected output:
```
PASSED tests/test_dashboard.py::TestPopulationEndpoint::test_returns_patients_ranked_highest_first
PASSED tests/test_dashboard.py::TestPopulationEndpoint::test_excludes_discharged_admissions
PASSED tests/test_dashboard.py::TestPopulationEndpoint::test_excludes_other_hospital_patients
PASSED tests/test_dashboard.py::TestPopulationEndpoint::test_filter_by_risk_tier
PASSED tests/test_dashboard.py::TestModelStatsEndpoint::test_returns_algorithm_and_auc
PASSED tests/test_dashboard.py::TestModelStatsEndpoint::test_non_admin_cannot_access_model_stats
```

- [ ] **Step 3: Run full backend test suite**

```powershell
cd backend; py -m pytest -v
```

Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/dashboard.py
git commit -m "feat(api): add /dashboard/population and /dashboard/model-stats endpoints"
```

---

### Task 5: Add Frontend Types to api.ts

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Append new interfaces to the end of `frontend/src/lib/api.ts`**

```typescript
export interface PopulationPatientRow {
  patient_id: string;
  first_name: string;
  last_name: string;
  mrn: string;
  department: string;
  prediction_id: string;
  probability: number;
  risk_tier: string;
  top_factor: string | null;
}

export interface PopulationResponse {
  patients: PopulationPatientRow[];
  high_count: number;
  medium_count: number;
  low_count: number;
  total: number;
}

export interface FeatureImportanceItem {
  feature_name: string;
  humanized_label: string;
  avg_importance: number;
}

export interface ModelStatsResponse {
  algorithm: string;
  version: string;
  trained_at: string | null;
  cv_auc: number | null;
  test_auc: number | null;
  total_predictions: number;
  tier_distribution: { High: number; Medium: number; Low: number };
  top_features: FeatureImportanceItem[];
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```powershell
cd frontend; npm run lint
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(types): add PopulationResponse and ModelStatsResponse API types"
```

---

### Task 6: Ward View Page

**Files:**
- Create: `frontend/src/pages/WardView.tsx`

- [ ] **Step 1: Create `frontend/src/pages/WardView.tsx`**

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, PopulationResponse } from "@/lib/api";

const TIER_BADGE: Record<string, string> = {
  High: "bg-red-100 text-red-800 border border-red-200",
  Medium: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  Low: "bg-green-100 text-green-800 border border-green-200",
};

export function WardView() {
  const navigate = useNavigate();
  const [deptFilter, setDeptFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("");

  const params = new URLSearchParams();
  if (deptFilter) params.set("department", deptFilter);
  if (tierFilter) params.set("risk_tier", tierFilter);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["population", deptFilter, tierFilter],
    queryFn: () =>
      api.get<PopulationResponse>(`/dashboard/population?${params.toString()}`),
  });

  const allDepartments = [
    ...new Set(
      data?.patients
        ? [...data.patients.map((p) => p.department)]
        : []
    ),
  ].sort();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Ward Risk View</h1>
        <p className="text-sm text-slate-500 mt-1">
          All admitted patients ranked by 30-day readmission risk — highest risk first.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card border-l-4 border-red-500">
          <div className="text-xs uppercase tracking-wide text-slate-500">High Risk</div>
          <div className="text-3xl font-bold text-red-600 mt-1">
            {data?.high_count ?? "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Require immediate attention</div>
        </div>
        <div className="card border-l-4 border-yellow-400">
          <div className="text-xs uppercase tracking-wide text-slate-500">Medium Risk</div>
          <div className="text-3xl font-bold text-yellow-600 mt-1">
            {data?.medium_count ?? "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Monitor before discharge</div>
        </div>
        <div className="card border-l-4 border-green-500">
          <div className="text-xs uppercase tracking-wide text-slate-500">Low Risk</div>
          <div className="text-3xl font-bold text-green-600 mt-1">
            {data?.low_count ?? "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">Standard discharge protocol</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-white"
          value={deptFilter}
          onChange={(e) => setDeptFilter(e.target.value)}
        >
          <option value="">All departments</option>
          {allDepartments.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-white"
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
        >
          <option value="">All risk tiers</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        {(deptFilter || tierFilter) && (
          <button
            className="text-sm text-slate-500 underline"
            onClick={() => {
              setDeptFilter("");
              setTierFilter("");
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Patient</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">MRN</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Department</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Risk Score</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Tier</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Top Risk Factor</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-400">
                  Loading patients…
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-red-500">
                  Failed to load ward data.
                </td>
              </tr>
            )}
            {!isLoading && !isError && data?.patients.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-400">
                  No patients match the current filters.
                </td>
              </tr>
            )}
            {data?.patients.map((p) => (
              <tr
                key={p.patient_id}
                className="hover:bg-slate-50 cursor-pointer"
                onClick={() => navigate(`/patients/${p.patient_id}`)}
              >
                <td className="px-4 py-3 font-medium">
                  {p.first_name} {p.last_name}
                </td>
                <td className="px-4 py-3 text-slate-500 font-mono text-xs">{p.mrn}</td>
                <td className="px-4 py-3 text-slate-600">{p.department}</td>
                <td className="px-4 py-3 font-mono font-semibold">
                  {(p.probability * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      TIER_BADGE[p.risk_tier] ?? ""
                    }`}
                  >
                    {p.risk_tier}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {p.top_factor ?? "—"}
                </td>
                <td className="px-4 py-3">
                  <span className="text-brand-700 hover:underline text-xs">
                    View chart →
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && (
          <div className="px-4 py-2 border-t bg-slate-50 text-xs text-slate-400">
            {data.total} admitted patients with predictions
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/WardView.tsx
git commit -m "feat(ui): add WardView page with population risk table and filters"
```

---

### Task 7: Update Admin Dashboard (ROI Calculator + Model Transparency)

**Files:**
- Modify: `frontend/src/pages/AdminDashboard.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/AdminDashboard.tsx`**

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ModelStatsResponse } from "@/lib/api";

export function AdminDashboard() {
  const stats = useQuery({
    queryKey: ["readmissions"],
    queryFn: () =>
      api.get<{ period: string; total_predictions: number; high_risk_rate: number; note: string }>(
        "/dashboard/readmissions"
      ),
  });
  const modelStats = useQuery({
    queryKey: ["model-stats"],
    queryFn: () => api.get<ModelStatsResponse>("/dashboard/model-stats"),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Administrator dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">Total predictions</div>
          <div className="text-3xl font-bold mt-1">
            {stats.data?.total_predictions ?? "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">High-risk rate</div>
          <div className="text-3xl font-bold mt-1 text-risk-high">
            {stats.data ? `${(stats.data.high_risk_rate * 100).toFixed(1)}%` : "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">Period</div>
          <div className="text-3xl font-bold mt-1">{stats.data?.period ?? "—"}</div>
        </div>
      </div>

      <RoiCalculator />
      <ModelTransparency data={modelStats.data} isLoading={modelStats.isLoading} />

      {stats.data?.note && (
        <p className="text-xs text-slate-500 italic mt-4">{stats.data.note}</p>
      )}
    </div>
  );
}

function RoiCalculator() {
  const [beds, setBeds] = useState(300);
  const [monthlyAdmissions, setMonthlyAdmissions] = useState(250);
  const [readmissionRate, setReadmissionRate] = useState(13);
  const [costPerReadmission, setCostPerReadmission] = useState(5000);

  const annualReadmissions = Math.round((monthlyAdmissions * 12 * readmissionRate) / 100);
  const highRiskCount = Math.round(annualReadmissions * 0.3); // ~30% flagged as high risk
  const preventedLow = Math.round(highRiskCount * 0.15);
  const preventedHigh = Math.round(highRiskCount * 0.20);
  const savingsLow = preventedLow * costPerReadmission;
  const savingsHigh = preventedHigh * costPerReadmission;

  return (
    <div className="card mb-6">
      <h2 className="font-semibold text-lg mb-1">ROI Impact Calculator</h2>
      <p className="text-xs text-slate-400 mb-4">
        Projected savings based on published literature on clinical decision support tools
        (15–20% reduction in high-risk readmissions).
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Total beds</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={beds}
            onChange={(e) => setBeds(Number(e.target.value))}
            min={50}
            max={2000}
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Monthly admissions</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={monthlyAdmissions}
            onChange={(e) => setMonthlyAdmissions(Number(e.target.value))}
            min={10}
            max={5000}
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Readmission rate (%)</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={readmissionRate}
            onChange={(e) => setReadmissionRate(Number(e.target.value))}
            min={1}
            max={40}
          />
        </label>
        <label className="block">
          <span className="text-xs text-slate-500 uppercase tracking-wide">Cost per readmission ($)</span>
          <input
            type="number"
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            value={costPerReadmission}
            onChange={(e) => setCostPerReadmission(Number(e.target.value))}
            min={500}
            max={50000}
          />
        </label>
      </div>

      <div className="bg-slate-50 rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Annual readmissions</div>
          <div className="text-2xl font-bold mt-1">{annualReadmissions.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            High-risk patients flagged / year
          </div>
          <div className="text-2xl font-bold mt-1 text-yellow-600">
            ~{highRiskCount.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Estimated annual savings
          </div>
          <div className="text-2xl font-bold mt-1 text-green-600">
            ${savingsLow.toLocaleString()} – ${savingsHigh.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelTransparency({
  data,
  isLoading,
}: {
  data: ModelStatsResponse | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="card mb-6">
        <h2 className="font-semibold text-lg mb-4">Model Transparency</h2>
        <p className="text-sm text-slate-400">Loading…</p>
      </div>
    );
  }
  if (!data) return null;

  const maxImportance = Math.max(...data.top_features.map((f) => f.avg_importance), 0.001);
  const totalTier = Object.values(data.tier_distribution).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="card mb-6">
      <h2 className="font-semibold text-lg mb-1">Model Transparency</h2>
      <p className="text-xs text-slate-400 mb-4">
        Active prediction model performance and global feature influence across all patients.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Algorithm</div>
          <div className="font-semibold mt-1 capitalize">{data.algorithm.replace(/_/g, " ")}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Version</div>
          <div className="font-semibold mt-1">{data.version}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">CV AUC</div>
          <div className="font-semibold mt-1 text-brand-700">
            {data.cv_auc != null ? data.cv_auc.toFixed(3) : "—"}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Test AUC</div>
          <div className="font-semibold mt-1 text-brand-700">
            {data.test_auc != null ? data.test_auc.toFixed(3) : "—"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top features */}
        <div>
          <h3 className="text-sm font-medium text-slate-600 mb-3">
            Top influencing factors (global avg |SHAP|)
          </h3>
          <div className="space-y-2">
            {data.top_features.map((f) => (
              <div key={f.feature_name}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-slate-600">{f.humanized_label}</span>
                  <span className="text-slate-400">{f.avg_importance.toFixed(3)}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-brand-600"
                    style={{ width: `${(f.avg_importance / maxImportance) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk tier distribution */}
        <div>
          <h3 className="text-sm font-medium text-slate-600 mb-3">
            Risk tier distribution ({data.total_predictions} predictions)
          </h3>
          <div className="space-y-3">
            {(["High", "Medium", "Low"] as const).map((tier) => {
              const count = data.tier_distribution[tier];
              const pct = Math.round((count / totalTier) * 100);
              const colors: Record<string, string> = {
                High: "bg-red-500",
                Medium: "bg-yellow-400",
                Low: "bg-green-500",
              };
              return (
                <div key={tier}>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span className="text-slate-600">{tier} Risk</span>
                    <span className="text-slate-400">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className={`h-2 rounded-full ${colors[tier]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript**

```powershell
cd frontend; npm run lint
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/AdminDashboard.tsx
git commit -m "feat(ui): add ROI calculator and model transparency to admin dashboard"
```

---

### Task 8: Update Routing and Navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/AppShell.tsx`

- [ ] **Step 1: Add WardView route to `frontend/src/App.tsx`**

Add the import after the existing imports:
```typescript
import { WardView } from "@/pages/WardView";
```

Add the route inside the `<Route element={<RequireAuth>...}>` block, after the `/dashboard/admin` route:
```tsx
<Route path="/ward" element={<WardView />} />
```

The `<Route element={...}>` block should now look like:
```tsx
<Route
  element={
    <RequireAuth>
      <AppShell />
    </RequireAuth>
  }
>
  <Route path="/patients" element={<PatientSearch />} />
  <Route path="/patients/:id" element={<PatientChart />} />
  <Route path="/dashboard/clinician" element={<ClinicianDashboard />} />
  <Route path="/dashboard/case-manager" element={<CaseManagerDashboard />} />
  <Route path="/dashboard/admin" element={<AdminDashboard />} />
  <Route path="/ward" element={<WardView />} />
  <Route index element={<Navigate to="/ward" replace />} />
</Route>
```

Note: Also change the default redirect from `/patients` to `/ward` so the ward view is the landing page.

- [ ] **Step 2: Add Ward View nav link to `frontend/src/components/AppShell.tsx`**

Replace the `links` array with:
```typescript
const links = [
  { to: "/ward", label: "Ward Risk View", roles: ["admin", "physician", "resident", "nurse", "case_manager", "analyst"] },
  { to: "/patients", label: "Patients", roles: ["admin", "physician", "resident", "nurse", "case_manager"] },
  { to: "/dashboard/clinician", label: "Clinician dashboard", roles: ["physician", "resident", "nurse"] },
  { to: "/dashboard/case-manager", label: "Case manager", roles: ["case_manager"] },
  { to: "/dashboard/admin", label: "Admin", roles: ["admin", "analyst"] },
];
```

- [ ] **Step 3: Verify TypeScript**

```powershell
cd frontend; npm run lint
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/AppShell.tsx
git commit -m "feat(routing): add /ward route and nav link, set as default landing page"
```

---

### Task 9: HTML Presentation Deck

**Files:**
- Create: `docs/presentation/index.html`

- [ ] **Step 1: Create `docs/presentation/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>CareInsight — Investor Presentation</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --brand: #1e3a5f;
    --brand-light: #2d5a8e;
    --accent: #0ea5e9;
    --accent-light: #e0f2fe;
    --danger: #dc2626;
    --success: #16a34a;
    --warn: #d97706;
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #1e293b;
    --muted: #64748b;
    --border: #e2e8f0;
  }

  html, body { width: 100%; height: 100%; overflow: hidden; background: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--text); }

  .deck { width: 100%; height: 100%; position: relative; }
  .slide { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 5vw; opacity: 0; pointer-events: none; transition: opacity 0.4s ease; }
  .slide.active { opacity: 1; pointer-events: auto; }

  /* Slide backgrounds */
  .slide-cover { background: linear-gradient(135deg, var(--brand) 0%, #0c2340 100%); color: white; }
  .slide-light { background: var(--bg); }
  .slide-dark { background: var(--brand); color: white; }

  /* Typography */
  .tag { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; color: var(--accent); margin-bottom: 0.75rem; }
  .slide-cover .tag { color: #7dd3fc; }
  h1 { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.1; margin-bottom: 0.5rem; }
  h2 { font-size: clamp(1.5rem, 3.5vw, 2.5rem); font-weight: 700; line-height: 1.2; margin-bottom: 1rem; }
  h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; }
  p.lead { font-size: clamp(1rem, 2vw, 1.3rem); color: var(--muted); max-width: 700px; text-align: center; line-height: 1.6; margin-top: 0.5rem; }
  .slide-cover p.lead { color: #bfdbfe; }
  .slide-dark p.lead { color: #93c5fd; }

  /* Cards */
  .card { background: var(--card); border-radius: 12px; padding: 1.5rem; border: 1px solid var(--border); }
  .card-grid { display: grid; gap: 1rem; width: 100%; max-width: 900px; }
  .card-grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
  .card-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }

  /* Stat highlight */
  .stat-big { font-size: clamp(2rem, 4vw, 3rem); font-weight: 800; color: var(--brand); }
  .stat-label { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }
  .stat-danger { color: var(--danger); }
  .stat-success { color: var(--success); }
  .stat-accent { color: var(--accent); }

  /* Pill badge */
  .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  .badge-red { background: #fee2e2; color: var(--danger); }
  .badge-green { background: #dcfce7; color: var(--success); }
  .badge-blue { background: var(--accent-light); color: #0369a1; }

  /* Step flow */
  .flow { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; justify-content: center; }
  .flow-step { background: white; border: 2px solid var(--accent); border-radius: 10px; padding: 0.75rem 1.25rem; font-size: 0.9rem; font-weight: 600; text-align: center; min-width: 140px; }
  .flow-arrow { color: var(--accent); font-size: 1.5rem; font-weight: 700; }

  /* Use of funds */
  .fund-bar { height: 12px; border-radius: 6px; margin-bottom: 0.5rem; }
  .fund-row { margin-bottom: 1rem; }
  .fund-label { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.3rem; }

  /* Team */
  .team-card { text-align: center; }
  .avatar { width: 64px; height: 64px; border-radius: 50%; background: var(--accent-light); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 700; color: var(--brand); margin: 0 auto 0.75rem; }

  /* Progress */
  .progress { position: fixed; bottom: 1.5rem; left: 50%; transform: translateX(-50%); display: flex; gap: 0.5rem; z-index: 10; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.3); transition: background 0.3s; cursor: pointer; }
  .dot.active { background: var(--accent); }

  /* Nav arrows */
  .nav { position: fixed; bottom: 1.5rem; width: 100%; display: flex; justify-content: space-between; padding: 0 2rem; z-index: 10; pointer-events: none; }
  .nav-btn { pointer-events: auto; background: rgba(255,255,255,0.15); color: white; border: none; border-radius: 8px; padding: 0.5rem 1.2rem; font-size: 1rem; cursor: pointer; backdrop-filter: blur(4px); transition: background 0.2s; }
  .nav-btn:hover { background: rgba(255,255,255,0.25); }

  .slide-num { position: fixed; top: 1rem; right: 1.5rem; color: rgba(255,255,255,0.4); font-size: 0.8rem; z-index: 10; }

  ul.feature-list { list-style: none; width: 100%; max-width: 700px; }
  ul.feature-list li { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); font-size: 0.95rem; }
  ul.feature-list li:last-child { border-bottom: none; }
  .icon { font-size: 1.2rem; flex-shrink: 0; }

  table.pricing { width: 100%; max-width: 700px; border-collapse: collapse; }
  table.pricing th { background: var(--brand); color: white; padding: 0.75rem 1rem; text-align: left; font-size: 0.85rem; }
  table.pricing td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); font-size: 0.9rem; background: white; }
  table.pricing tr:last-child td { border-bottom: none; }

  @media (max-width: 600px) {
    .card-grid.cols-2, .card-grid.cols-3 { grid-template-columns: 1fr; }
    .flow { flex-direction: column; }
    .flow-arrow { transform: rotate(90deg); }
  }
</style>
</head>
<body>
<div class="deck" id="deck">

  <!-- SLIDE 1: Cover -->
  <div class="slide slide-cover active">
    <div class="tag">Investor Presentation · 2026</div>
    <h1>CareInsight</h1>
    <p class="lead">MENA's readmission intelligence platform — predict who will return before they leave.</p>
    <div style="margin-top:2rem; display:flex; gap:1rem; flex-wrap:wrap; justify-content:center;">
      <span class="badge badge-blue">AI-Powered Prediction</span>
      <span class="badge badge-blue">SHAP Explanations</span>
      <span class="badge badge-blue">Clinical Decision Support</span>
    </div>
  </div>

  <!-- SLIDE 2: Problem -->
  <div class="slide slide-light">
    <div class="tag">The Problem</div>
    <h2 style="text-align:center;">Hospitals are flying blind at discharge</h2>
    <div class="card-grid cols-3" style="margin-top:2rem;">
      <div class="card" style="text-align:center;">
        <div class="stat-big stat-danger">13%</div>
        <div class="stat-label">30-day readmission rate in Lebanese private hospitals</div>
      </div>
      <div class="card" style="text-align:center;">
        <div class="stat-big stat-danger">$5K–8K</div>
        <div class="stat-label">Average cost per avoidable readmission</div>
      </div>
      <div class="card" style="text-align:center;">
        <div class="stat-big stat-danger">0</div>
        <div class="stat-label">MENA hospitals with a clinical readmission prediction tool</div>
      </div>
    </div>
    <p class="lead" style="margin-top:1.5rem;">Clinicians rely on intuition. Case managers don't know which patients need intervention. The right call could prevent the readmission entirely.</p>
  </div>

  <!-- SLIDE 3: Solution -->
  <div class="slide slide-dark">
    <div class="tag">The Solution</div>
    <h2 style="text-align:center; color:white;">CareInsight flags the right patients, before discharge</h2>
    <div class="flow" style="margin-top:2rem;">
      <div class="flow-step">Admission data<br/><small style="font-weight:400;color:var(--muted);">labs, vitals, history</small></div>
      <div class="flow-arrow">→</div>
      <div class="flow-step">ML Risk Score<br/><small style="font-weight:400;color:var(--muted);">XGBoost + SHAP</small></div>
      <div class="flow-arrow">→</div>
      <div class="flow-step">AI Copilot<br/><small style="font-weight:400;color:var(--muted);">clinical explanation</small></div>
      <div class="flow-arrow">→</div>
      <div class="flow-step">Intervention<br/><small style="font-weight:400;color:var(--muted);">discharge checklist</small></div>
    </div>
    <p class="lead" style="margin-top:1.5rem;">Not a replacement for Epic. The intelligence layer that hospitals without Epic have never had.</p>
  </div>

  <!-- SLIDE 4: Product -->
  <div class="slide slide-light">
    <div class="tag">The Product</div>
    <h2 style="text-align:center;">Built for clinical teams, not IT departments</h2>
    <ul class="feature-list" style="margin-top:1.5rem;">
      <li><span class="icon">🏥</span><div><strong>Ward Risk View</strong> — Every admitted patient ranked by readmission risk. The morning view your case managers need.</div></li>
      <li><span class="icon">🔍</span><div><strong>SHAP Explanations</strong> — Not just a score. "This patient is high risk because of poor follow-up compliance and 3 prior admissions."</div></li>
      <li><span class="icon">🤖</span><div><strong>AI Clinical Copilot</strong> — Ask why in plain language. Get clinical context. Powered by Gemini 2.5 Flash.</div></li>
      <li><span class="icon">✅</span><div><strong>Smart Discharge Checklist</strong> — Auto-generated, patient-specific interventions. Tracked per clinician.</div></li>
      <li><span class="icon">📊</span><div><strong>Model Transparency</strong> — Algorithm, AUC, feature importances. Built for clinical governance teams.</div></li>
    </ul>
  </div>

  <!-- SLIDE 5: Market -->
  <div class="slide slide-light">
    <div class="tag">Market Opportunity</div>
    <h2 style="text-align:center;">Lebanon is the beachhead. MENA is the prize.</h2>
    <div class="card-grid cols-3" style="margin-top:2rem;">
      <div class="card" style="text-align:center;">
        <div class="stat-big">150+</div>
        <div class="stat-label">Private hospitals in Lebanon</div>
        <div class="badge badge-blue" style="margin-top:0.5rem;">Beachhead market</div>
      </div>
      <div class="card" style="text-align:center;">
        <div class="stat-big">2,000+</div>
        <div class="stat-label">Hospitals in Saudi Arabia</div>
        <div class="badge badge-green" style="margin-top:0.5rem;">Year 3 target</div>
      </div>
      <div class="card" style="text-align:center;">
        <div class="stat-big">$50M+</div>
        <div class="stat-label">Realistic ARR potential at 5% MENA penetration</div>
        <div class="badge badge-red" style="margin-top:0.5rem;">Long-term vision</div>
      </div>
    </div>
    <p class="lead" style="margin-top:1.5rem;">Epic costs $50–100M to implement. It will never reach 95% of MENA hospitals. We serve the gap.</p>
  </div>

  <!-- SLIDE 6: Traction -->
  <div class="slide slide-dark">
    <div class="tag">Traction &amp; Validation</div>
    <h2 style="text-align:center; color:white;">Validated by experts. Backed by academia. Next: clinical.</h2>
    <div class="card-grid cols-3" style="margin-top:2rem;">
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:0.5rem;">🏆</div>
        <h3>2nd Place</h3>
        <p style="font-size:0.85rem;color:var(--muted);">Symz Capital AI Competition — judged by investors and healthcare faculty</p>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:0.5rem;">🎓</div>
        <h3>LAU Backed</h3>
        <p style="font-size:0.85rem;color:var(--muted);">Faculty advisor from Lebanese American University connected us to our first hospital prospect</p>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem;margin-bottom:0.5rem;">🏥</div>
        <h3>Rizk Hospital</h3>
        <p style="font-size:0.85rem;color:var(--muted);">Pilot meeting scheduled with one of Lebanon's top private hospitals</p>
      </div>
    </div>
  </div>

  <!-- SLIDE 7: Business Model -->
  <div class="slide slide-light">
    <div class="tag">Business Model</div>
    <h2 style="text-align:center;">Simple SaaS. Pilot → License → Expand.</h2>
    <table class="pricing" style="margin-top:2rem;">
      <thead>
        <tr>
          <th>Stage</th>
          <th>Price</th>
          <th>What's included</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Pilot (3 months)</strong></td>
          <td><strong>$15,000 flat</strong></td>
          <td>Deployment, model training on hospital data, onboarding</td>
        </tr>
        <tr>
          <td>Annual license (small)</td>
          <td>$800/mo per 100 beds</td>
          <td>50–200 bed hospital: ~$9,600/year</td>
        </tr>
        <tr>
          <td>Annual license (Rizk scale)</td>
          <td>~$2,400/month</td>
          <td>300+ beds: ~$28,800/year</td>
        </tr>
        <tr>
          <td style="color:var(--success);font-weight:600;">Year 1 target (3 hospitals)</td>
          <td style="color:var(--success);font-weight:600;">~$72K ARR</td>
          <td>Rizk + 2 Lebanese hospitals post-pilot</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- SLIDE 8: The Ask -->
  <div class="slide slide-light">
    <div class="tag">The Ask</div>
    <h2 style="text-align:center;">$150,000 seed to reach first revenue</h2>
    <div class="card-grid cols-3" style="margin-top:2rem; max-width:900px;">
      <div class="card">
        <div class="stat-big stat-accent">$40K</div>
        <h3 style="margin-top:0.5rem;">Rizk Hospital Pilot</h3>
        <p style="font-size:0.85rem;color:var(--muted);">Model training on real patient data + implementation + clinical onboarding</p>
      </div>
      <div class="card">
        <div class="stat-big stat-accent">$30K</div>
        <h3 style="margin-top:0.5rem;">FHIR Integration</h3>
        <p style="font-size:0.85rem;color:var(--muted);">Connect to any hospital's EHR system — makes us enterprise-ready</p>
      </div>
      <div class="card">
        <div class="stat-big stat-accent">$80K</div>
        <h3 style="margin-top:0.5rem;">12 Months Runway</h3>
        <p style="font-size:0.85rem;color:var(--muted);">Founder runway + part-time developer + clinical advisor</p>
      </div>
    </div>
    <p class="lead" style="margin-top:1.5rem;">At the end of 12 months: a validated model on real Lebanese patient data, a reference customer, and outcome data that proves ROI.</p>
  </div>

  <!-- SLIDE 9: Team -->
  <div class="slide slide-dark">
    <div class="tag">Team</div>
    <h2 style="text-align:center; color:white;">Technical founder, clinical network, academic backing</h2>
    <div class="card-grid cols-3" style="margin-top:2rem;">
      <div class="card team-card">
        <div class="avatar">JA</div>
        <h3>Jad Assaf</h3>
        <p style="font-size:0.8rem;color:var(--muted);">Founder &amp; Technical Lead · Full-stack + ML · Built entire platform</p>
      </div>
      <div class="card team-card">
        <div class="avatar">🎓</div>
        <h3>LAU Advisor</h3>
        <p style="font-size:0.8rem;color:var(--muted);">Faculty advisor providing clinical guidance and hospital introductions</p>
      </div>
      <div class="card team-card">
        <div class="avatar">+</div>
        <h3>Hiring with investment</h3>
        <p style="font-size:0.8rem;color:var(--muted);">Second engineer + clinical co-founder / advisor from the hospital world</p>
      </div>
    </div>
  </div>

  <!-- SLIDE 10: Close -->
  <div class="slide slide-cover">
    <div class="tag">Thank you</div>
    <h1>Let's build this together</h1>
    <p class="lead">Rizk Hospital pilot meeting is our next milestone. With your support, it becomes our first signed customer and the proof point we need to expand across Lebanon and into the Gulf.</p>
    <div style="margin-top:2rem; padding:1.5rem 2rem; background:rgba(255,255,255,0.1); border-radius:12px; text-align:center;">
      <div style="font-size:0.8rem;color:#7dd3fc;margin-bottom:0.5rem;">Contact</div>
      <div style="font-weight:600; font-size:1.1rem; color:white;">jadassaf6000@gmail.com</div>
    </div>
  </div>

</div><!-- /deck -->

<!-- Navigation -->
<div class="progress" id="progress"></div>
<div class="nav">
  <button class="nav-btn" id="prev">← Prev</button>
  <button class="nav-btn" id="next">Next →</button>
</div>
<div class="slide-num" id="slide-num"></div>

<script>
  const slides = document.querySelectorAll('.slide');
  const dots = document.getElementById('progress');
  const slideNum = document.getElementById('slide-num');
  let current = 0;

  // Build dots
  slides.forEach((_, i) => {
    const d = document.createElement('div');
    d.className = 'dot' + (i === 0 ? ' active' : '');
    d.addEventListener('click', () => goTo(i));
    dots.appendChild(d);
  });

  function goTo(n) {
    slides[current].classList.remove('active');
    dots.children[current].classList.remove('active');
    current = Math.max(0, Math.min(n, slides.length - 1));
    slides[current].classList.add('active');
    dots.children[current].classList.add('active');
    slideNum.textContent = `${current + 1} / ${slides.length}`;
  }

  document.getElementById('prev').addEventListener('click', () => goTo(current - 1));
  document.getElementById('next').addEventListener('click', () => goTo(current + 1));

  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') goTo(current + 1);
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') goTo(current - 1);
    if (e.key === 'Home') goTo(0);
    if (e.key === 'End') goTo(slides.length - 1);
  });

  goTo(0);
</script>
</body>
</html>
```

- [ ] **Step 2: Open and verify the deck**

Open `docs/presentation/index.html` in a browser. Use arrow keys to navigate. Verify all 10 slides render cleanly and the progress dots work.

- [ ] **Step 3: Commit**

```bash
git add docs/presentation/index.html
git commit -m "feat(presentation): add 10-slide investor HTML deck with keyboard navigation"
```

---

## Self-Review

**Spec coverage check:**
- ✅ 25 patients, 4 departments, pre-seeded predictions → Task 1
- ✅ Population Risk Intelligence View (backend + frontend) → Tasks 2, 3, 4, 6
- ✅ ROI Impact Calculator (frontend only, no backend) → Task 7
- ✅ Model Transparency page (backend + frontend) → Tasks 2, 4, 7
- ✅ Ward View as default landing page → Task 8
- ✅ HTML presentation deck → Task 9
- ✅ Tests for both new endpoints → Task 3

**Placeholder scan:** None found — all steps contain complete code.

**Type consistency:**
- `PopulationPatientRow.patient_id` is `str` in schema (UUID serialized) and `string` in TypeScript ✅
- `ModelStatsResponse.tier_distribution` is `dict[str, int]` in Python and `{ High: number; Medium: number; Low: number }` in TypeScript ✅
- `func.abs()` used in SQLAlchemy model-stats query — SQLite supports `ABS()` natively ✅
- `Prediction.created_at` join used in population subquery — column exists on `TimestampMixin` ✅
