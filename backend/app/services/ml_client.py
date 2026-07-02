"""HTTP client wrapping the ml-service API."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MLServiceError(RuntimeError):
    pass


class MLClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self.base_url = (base_url or settings.ml_service_url).rstrip("/")
        self.timeout = timeout

    def _post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=json)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("ML service call failed: %s", exc)
            raise MLServiceError(f"ML service unreachable: {exc}") from exc

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("ML service call failed: %s", exc)
            raise MLServiceError(f"ML service unreachable: {exc}") from exc

    def predict(self, clinical_features: dict[str, Any], threshold: float = 0.5) -> dict[str, Any]:
        return self._post("/predict", {"features": clinical_features, "threshold": threshold})

    def explain(self, clinical_features: dict[str, Any], top_n: int = 10) -> dict[str, Any]:
        return self._post("/explain", {"features": clinical_features, "top_n": top_n})

    def model_version(self) -> dict[str, Any]:
        return self._get("/model/version")

    def retrain_upload(self, csv_content: bytes, filename: str = "upload.csv") -> dict[str, Any]:
        url = f"{self.base_url}/retrain/upload"
        try:
            with httpx.Client(timeout=180.0) as client:
                resp = client.post(url, files={"file": (filename, csv_content, "text/csv")})
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("ML service retrain failed: %s", exc)
            raise MLServiceError(f"ML service retrain failed: {exc}") from exc
