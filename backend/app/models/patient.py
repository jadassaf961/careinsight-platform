"""Patient + Admission ORM models."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONField, TimestampMixin, UUIDPKMixin, UUIDType


class Patient(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("hospital_id", "mrn", name="uq_patient_hospital_mrn"),
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    mrn: Mapped[str] = mapped_column(String(40), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    admissions: Mapped[list["Admission"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class Admission(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "admissions"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("departments.id"), nullable=False, index=True,
    )
    admission_type: Mapped[str] = mapped_column(String(40), nullable=False)
    admitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    discharged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    length_of_stay: Mapped[float | None] = mapped_column(Float, nullable=True)
    clinical_features: Mapped[dict[str, Any]] = mapped_column(JSONField, nullable=False, default=dict)

    patient: Mapped[Patient] = relationship(back_populates="admissions")
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        back_populates="admission", cascade="all, delete-orphan",
        order_by="Prediction.created_at.desc()",
    )
