"""Checklist generation — ported from src/utils/helpers.generate_checklist."""
from __future__ import annotations

from typing import Iterable

BASE_CHECKLIST: list[str] = [
    "Schedule follow-up appointment within 7 days of discharge",
    "Confirm patient has correct medications and understands dosing",
    "Provide written discharge summary in patient's preferred language",
    "Screen for social determinants: housing, food access, transport",
    "Ensure patient has a primary care provider and contact information",
]

FACTOR_ACTIONS: dict[str, str] = {
    "diabetes":   "Confirm HbA1c plan and enrol in diabetes self-management education",
    "heart":      "Arrange cardiology follow-up within 7 days post-discharge",
    "renal":      "Nephrology referral; monitor BUN/creatinine after discharge",
    "creatinine": "Nephrology referral; monitor renal function post-discharge",
    "hemoglobin": "Check for anaemia; haematology referral if Hb < 10 g/dL",
    "glucose":    "Review glycaemic control; endocrinology referral if indicated",
    "bmi":        "Nutrition assessment and dietitian referral",
    "smoking":    "Smoking cessation counselling and NRT prescription",
    "alcohol":    "Alcohol dependency screening (AUDIT); addiction services referral",
    "mental":     "Mental health screening; psychiatry referral if indicated",
    "followup":   "Reinforce follow-up importance; consider community health worker",
    "social":     "Social work referral for support network assessment",
    "physical":   "Physiotherapy assessment; activity prescription on discharge",
    "admission":  "Emergency admission — ensure root cause addressed before discharge",
    "previous":   "High utiliser — case management referral and care coordination plan",
    "chronic":    "Chronic disease management plan; specialist follow-up arranged",
    "procedure":  "Post-procedure care instructions provided; wound care follow-up",
    "age":        "Assess fall risk; arrange geriatric support if indicated",
    "los":        "Coordinate complex transition plan (extended LOS detected)",
    "med":        "Perform full medication reconciliation before discharge",
    "insurance":  "Connect with social worker for benefits navigation",
}


def generate_checklist(
    top_factors: Iterable[tuple[str, float]],
    risk_tier: str,
) -> list[dict[str, str]]:
    """Build a structured discharge checklist.

    Returns a list of dicts with ``text``, ``category``, and ``source`` —
    ready to persist as `Recommendation` rows.
    """
    items: list[dict[str, str]] = [
        {"text": t, "category": "base", "source": "base"} for t in BASE_CHECKLIST
    ]

    if risk_tier.lower() == "high":
        items.insert(0, {
            "text": "HIGH RISK — flag for immediate care coordination team review",
            "category": "priority", "source": "risk_tier",
        })
        items.insert(1, {
            "text": "Schedule 48-hour post-discharge phone check-in",
            "category": "priority", "source": "risk_tier",
        })

    seen: set[str] = {i["text"] for i in items}
    extra_count = 0
    for feat, _ in list(top_factors)[:8]:
        fl = feat.lower()
        for key, action in FACTOR_ACTIONS.items():
            if key in fl and action not in seen:
                items.append({"text": action, "category": "factor-specific", "source": "factor"})
                seen.add(action)
                extra_count += 1
                if extra_count >= 5:
                    return items
                break
    return items
