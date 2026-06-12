"""Lazy model loader — resolves the most recent joblib artifact from the registry."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.config import settings
from app.pipeline.schema import feature_names


_state: dict[str, Any] = {"loaded": False, "model": None, "algorithm": None, "feature_names": None}


def load_model() -> dict[str, Any] | None:
    if _state["loaded"]:
        return _state if _state["model"] is not None else None

    registry: Path = settings.model_registry_dir
    if registry.exists():
        candidates = sorted(registry.glob("*.joblib"))
        if candidates:
            blob = joblib.load(candidates[-1])
            _state.update({
                "loaded": True, "model": blob["model"],
                "algorithm": blob.get("algorithm", "unknown"),
                "feature_names": blob.get("feature_names", feature_names()),
            })
            return _state

    _state.update({"loaded": True, "model": None, "algorithm": "unloaded",
                   "feature_names": feature_names()})
    return None


def set_model(model: Any, algorithm: str) -> None:
    _state.update({
        "loaded": True, "model": model, "algorithm": algorithm,
        "feature_names": feature_names(),
    })


def get_state() -> dict[str, Any]:
    if not _state["loaded"]:
        load_model()
    return _state
