"""Training pipeline — XGBoost / RF / LR with CV-AUC selection + isotonic calibration.

Ported from the prototype's `src/models/train.py`. Operates on a clinical CSV
matching the reference schema (see app/pipeline/schema.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from app.pipeline.schema import (
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    NUMERIC_RANGES,
    POSITIVE_CLASS,
    TARGET_COLUMN,
    feature_names,
)


_RANDOM_SEED = 42
_CV_FOLDS = 5


@dataclass
class TrainResult:
    algorithm: str
    cv_auc: float
    test_auc: float
    model_path: Path


def _build_models(scale_pos_weight: float) -> dict[str, Any]:
    return {
        "logistic_regression": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=5000, class_weight="balanced", C=1.0,
                solver="lbfgs", random_state=_RANDOM_SEED,
            )),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=400, max_depth=12, min_samples_leaf=4,
            class_weight="balanced_subsample", random_state=_RANDOM_SEED, n_jobs=-1,
        ),
        "xgboost": xgb.XGBClassifier(
            n_estimators=500, max_depth=6, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85,
            scale_pos_weight=scale_pos_weight, min_child_weight=2,
            reg_lambda=1.0, reg_alpha=0.0, eval_metric="logloss",
            random_state=_RANDOM_SEED, n_jobs=-1, verbosity=0,
        ),
    }


def _strict_preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    df = df.copy()
    target = (df[TARGET_COLUMN].astype(str) == POSITIVE_CLASS).astype(int).values
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            lo, hi = NUMERIC_RANGES[col]
            df[col] = pd.to_numeric(df[col], errors="coerce").clip(lo, hi)
            med = df[col].median()
            if pd.isna(med):
                med = (lo + hi) / 2.0
            df[col] = df[col].fillna(med)
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(
                {"nan": "Unknown", "NaN": "Unknown", "None": "Unknown"}
            ).fillna("Unknown")
    df = pd.get_dummies(df, columns=[c for c in CATEGORICAL_COLUMNS if c in df.columns],
                        drop_first=False, dtype=float)

    # Ensure all canonical feature columns are present
    for feat in feature_names():
        if feat not in df.columns:
            df[feat] = 0.0
    X = df[feature_names()].astype(float)
    return X, target


def train_from_csv(csv_path: Path, registry_dir: Path) -> TrainResult:
    """Train the readmission classifier from a CSV and persist the best model
    to disk. Returns metadata about the chosen model.
    """
    registry_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path)
    X, y = _strict_preprocess(df)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=_RANDOM_SEED,
    )
    scale_pos_weight = max((y_tr == 0).sum() / max((y_tr == 1).sum(), 1), 1.0)

    models = _build_models(scale_pos_weight)
    cv = StratifiedKFold(n_splits=_CV_FOLDS, shuffle=True, random_state=_RANDOM_SEED)

    cv_scores: dict[str, float] = {}
    fitted: dict[str, Any] = {}
    for name, m in models.items():
        cv_aucs = cross_val_score(clone(m), X_tr.values, y_tr,
                                  cv=cv, scoring="roc_auc", n_jobs=-1)
        m.fit(X_tr.values, y_tr)
        fitted[name] = m
        cv_scores[name] = float(np.mean(cv_aucs))

    best_name = max(cv_scores, key=cv_scores.get)  # type: ignore[arg-type]
    best = CalibratedClassifierCV(clone(models[best_name]), method="isotonic", cv=_CV_FOLDS)
    best.fit(X_tr.values, y_tr)
    test_auc = float(roc_auc_score(y_te, best.predict_proba(X_te.values)[:, 1]))

    artifact_path = registry_dir / f"{best_name}_v0_1_0.joblib"
    joblib.dump(
        {"model": best, "algorithm": best_name, "feature_names": feature_names()},
        artifact_path,
    )
    return TrainResult(
        algorithm=best_name, cv_auc=cv_scores[best_name],
        test_auc=test_auc, model_path=artifact_path,
    )
