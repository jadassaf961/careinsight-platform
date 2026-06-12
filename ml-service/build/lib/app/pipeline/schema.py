"""Clinical schema constants (ported from configs/config.yaml of the prototype)."""
from __future__ import annotations

NUMERIC_COLUMNS: list[str] = [
    "age", "weight_kg", "height_cm", "bmi", "num_previous_admissions",
    "medications_count", "last_hemoglobin", "last_glucose", "last_creatinine",
    "length_of_stay", "procedures_count",
]

CATEGORICAL_COLUMNS: list[str] = [
    "gender", "chronic_conditions", "admission_type", "smoking_status",
    "alcohol_use", "physical_activity", "insurance_type",
    "followup_compliance", "social_support", "mental_health_issue",
]

CATEGORY_VALUES: dict[str, list[str]] = {
    "gender": ["Female", "Male"],
    "chronic_conditions": ["COPD", "Diabetes", "Heart Disease", "Hypertension"],
    "admission_type": ["Elective", "Emergency", "Urgent"],
    "smoking_status": ["Current", "Former", "Never"],
    "alcohol_use": ["High", "Moderate"],
    "physical_activity": ["High", "Low", "Medium"],
    "insurance_type": ["Private", "Public", "Uninsured"],
    "followup_compliance": ["Good", "Poor"],
    "social_support": ["Strong", "Weak"],
    "mental_health_issue": ["No", "Yes"],
}

NUMERIC_RANGES: dict[str, tuple[float, float]] = {
    "age": (0, 120), "weight_kg": (20, 300), "height_cm": (100, 230),
    "bmi": (10, 70), "num_previous_admissions": (0, 30), "medications_count": (0, 40),
    "last_hemoglobin": (4, 22), "last_glucose": (40, 600), "last_creatinine": (0.2, 15),
    "length_of_stay": (0, 120), "procedures_count": (0, 20),
}

TARGET_COLUMN = "readmission_risk"
POSITIVE_CLASS = "High"


def feature_names() -> list[str]:
    """Return the canonical training feature order (numeric + one-hot expansion)."""
    names = list(NUMERIC_COLUMNS)
    for col in CATEGORICAL_COLUMNS:
        for v in CATEGORY_VALUES.get(col, []):
            names.append(f"{col}_{v}")
    return names
