"""Inference helpers — risk tier label."""
from __future__ import annotations


def risk_tier(prob: float, threshold: float) -> str:
    if prob >= threshold:
        return "High"
    elif prob >= threshold - 0.15:
        return "Medium"
    return "Low"
