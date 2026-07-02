"""Application configuration sourced from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Database — defaults to SQLite for zero-install local dev.
    # In production override with postgresql+psycopg://... via env.
    database_url: str = "sqlite:///./dev.db"

    # Auth
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15

    # CORS
    cors_origins: str = "http://localhost:5173"

    # ML service
    ml_service_url: str = "http://localhost:8001"

    # AI Copilot
    gemini_api_key: str = ""

    # Dev seeding
    seed_demo_data: bool = True
    seed_password: str = "Demo123!"

    # App
    app_name: str = "CareInsight Platform API"
    api_v1_prefix: str = "/api/v1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
