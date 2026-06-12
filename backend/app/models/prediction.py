"""ModelVersion, Prediction, RiskFactor, Recommendation ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class ModelVersion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "model_versions"
    # Partial unique index on (is_active=true) lives in the Alembic migration —
    # SQLite doesn't support `postgresql_where`, so we don't declare it here.
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(40), nullable=False)
    trained_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cv_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    artifact_uri: Mapped[str] = mapped_column(String(400), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Prediction(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "predictions"

    admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("model_versions.id"), nullable=False, index=True,
    )
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)

    admission = relationship("Admission", back_populates="predictions")
    model_version: Mapped[ModelVersion] = relationship()
    risk_factors: Mapped[list["RiskFactor"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan",
        order_by="RiskFactor.rank",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan",
    )


class RiskFactor(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "risk_factors"
    __table_args__ = (
        Index("ix_risk_factor_prediction_rank", "prediction_id", "rank"),
    )

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    feature_name: Mapped[str] = mapped_column(String(120), nullable=False)
    humanized_label: Mapped[str] = mapped_column(String(255), nullable=False)
    shap_value: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    prediction: Mapped[Prediction] = relationship(back_populates="risk_factors")


class Recommendation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False)  # base | factor | risk_tier

    prediction: Mapped[Prediction] = relationship(back_populates="recommendations")
