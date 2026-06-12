"""SHAP explanation — ported from src/models/explainability.py.

Safely unwraps CalibratedClassifierCV and Pipeline layers to reach the base
estimator, then picks the appropriate SHAP explainer.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.pipeline import Pipeline


def compute_shap(model: Any, algorithm: str, X: np.ndarray) -> np.ndarray:
    """Compute SHAP values for a (1, n_features) sample.

    Returns a 1-D array of length n_features. Lazily imports `shap` so
    the module can load even when `shap` isn't installed for unit tests.
    """
    import shap  # local import — heavy dep

    clf = model
    X_in = X

    if hasattr(clf, "calibrated_classifiers_"):
        try:
            clf = clf.calibrated_classifiers_[0].estimator
        except AttributeError:
            clf = clf.calibrated_classifiers_[0].base_estimator

    if isinstance(clf, Pipeline):
        pre = Pipeline(clf.steps[:-1])
        X_in = pre.transform(X)
        clf = clf.steps[-1][1]

    if algorithm in ("xgboost", "random_forest"):
        explainer = shap.TreeExplainer(clf)
        sv = explainer.shap_values(X_in)
    else:
        explainer = shap.LinearExplainer(clf, X_in, feature_perturbation="interventional")
        sv = explainer.shap_values(X_in)

    arr = np.array(sv)
    if isinstance(sv, list):
        arr = np.array(sv[1])
    elif arr.ndim == 3:
        arr = arr[:, :, 1]
    return arr[0]  # first (only) sample
