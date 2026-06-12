"""Intervention ORM model — clinician-recorded actions on an admission."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class InterventionStatus(str, enum.Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    DECLINED = "declined"
    NOT_APPLICABLE = "not_applicable"


class Intervention(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "interventions"

    admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("recommendations.id"), nullable=True,
    )
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False, index=True,
    )
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, name="intervention_status"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
