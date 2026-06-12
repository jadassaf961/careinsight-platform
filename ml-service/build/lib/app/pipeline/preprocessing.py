"""Single-patient preprocessing — feeds a feature dict through the same
clipping/imputation/one-hot logic the training pipeline uses.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from app.pipeline.schema import (
    CATEGORICAL_COLUMNS,
    CATEGORY_VALUES,
    NUMERIC_COLUMNS,
    NUMERIC_RANGES,
    feature_names,
)


def preprocess_single(features: dict[str, Any]) -> np.ndarray:
    """Convert a raw feature dict into a (1, n_features) numpy array aligned to
    :func:`feature_names`. Mirrors the prototype's
    `src/data/preprocessing.preprocess_single_patient`.
    """
    num_vals: dict[str, float] = {}
    for col in NUMERIC_COLUMNS:
        lo, hi = NUMERIC_RANGES[col]
        raw = features.get(col)
        try:
            val = float(raw) if raw not in (None, "") else (lo + hi) / 2.0
        except (TypeError, ValueError):
            val = (lo + hi) / 2.0
        num_vals[col] = float(np.clip(val, lo, hi))

    cat_lookup: dict[str, float] = {}
    for col in CATEGORICAL_COLUMNS:
        chosen = str(features.get(col, "Unknown"))
        for v in CATEGORY_VALUES.get(col, [chosen]):
            cat_lookup[f"{col}_{v}"] = 1.0 if v == chosen else 0.0
        cat_lookup[f"{col}_{chosen}"] = 1.0

    vec: list[float] = []
    for feat in feature_names():
        if feat in num_vals:
            vec.append(num_vals[feat])
        elif feat in cat_lookup:
            vec.append(cat_lookup[feat])
        else:
            vec.append(0.0)
    return np.array(vec, dtype=float).reshape(1, -1)
