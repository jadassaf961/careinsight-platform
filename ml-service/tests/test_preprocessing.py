"""Single-patient preprocessing tests."""
from __future__ import annotations

import numpy as np

from app.pipeline.preprocessing import preprocess_single
from app.pipeline.schema import feature_names


class TestPreprocessSingle:
    def test_returns_correct_shape(self):
        X = preprocess_single({"age": 65, "bmi": 24.5})
        assert X.shape == (1, len(feature_names()))

    def test_missing_numeric_uses_midpoint(self):
        X = preprocess_single({})
        names = feature_names()
        i_age = names.index("age")
        assert X[0, i_age] == 60  # midpoint of (0, 120)

    def test_categorical_one_hot_set(self):
        X = preprocess_single({"gender": "Female"})
        names = feature_names()
        female_idx = names.index("gender_Female")
        male_idx = names.index("gender_Male")
        assert X[0, female_idx] == 1.0
        assert X[0, male_idx] == 0.0

    def test_out_of_range_clipped(self):
        X = preprocess_single({"age": 999})
        names = feature_names()
        assert X[0, names.index("age")] == 120

    def test_non_numeric_string_uses_midpoint(self):
        X = preprocess_single({"age": "not-a-number"})
        names = feature_names()
        assert X[0, names.index("age")] == 60


class TestPredictEndpoint:
    def test_predict_returns_probability(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.post("/predict", json={
            "features": {
                "age": 75, "num_previous_admissions": 5,
                "medications_count": 12, "admission_type": "Emergency",
                "followup_compliance": "Poor",
            },
            "threshold": 0.5,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert 0.0 <= body["probability"] <= 1.0
        assert body["risk_tier"] in {"High", "Low"}


class TestExplainEndpoint:
    def test_explain_returns_factors(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.post("/explain", json={
            "features": {
                "age": 75, "num_previous_admissions": 5,
                "admission_type": "Emergency",
            },
            "top_n": 5,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["factors"]) <= 5
        assert all("feature_name" in f for f in body["factors"])
