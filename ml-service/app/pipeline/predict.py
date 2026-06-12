"""Inference helpers — risk tier label."""
from __future__ import annotations


def risk_tier(prob: float, threshold: float) -> str:
    return "High" if prob >= threshold else "Low"
