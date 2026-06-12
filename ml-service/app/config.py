"""ML-service configuration."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_registry_dir: Path = Path("app/registry")
    model_name: str = "readmission_classifier"
    model_version: str = "0.1.0"
    default_threshold: float = 0.5


settings = Settings()
