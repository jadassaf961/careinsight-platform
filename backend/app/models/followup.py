"""Follow-up engine ORM models: check-ins, responses, escalations, outcomes."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class CheckinStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    RESPONDED = "responded"
    NO_RESPONSE = "no_response"
    SEND_FAILED = "send_failed"
    MANUAL = "manual"
    SKIPPED = "skipped"


class EscalationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EscalationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class FollowUpCheckin(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "followup_checkins"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("transition_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    day_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[CheckinStatus] = mapped_column(
        Enum(CheckinStatus, name="checkin_status"),
        default=CheckinStatus.SCHEDULED, nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_body: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)

    plan: Mapped["TransitionPlan"] = relationship()  # noqa: F821
    responses: Mapped[list["CheckinResponse"]] = relationship(
        back_populates="checkin", cascade="all, delete-orphan",
    )


class CheckinResponse(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "checkin_responses"

    checkin_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("followup_checkins.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # provider message id for webhook idempotency (unique when present)
    provider_message_id: Mapped[str | None] = mapped_column(
        String(80), nullable=True, unique=True,
    )
    raw_text: Mapped[str] = mapped_column(String(2000), nullable=False)
    red_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meds_missed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    concern_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    checkin: Mapped[FollowUpCheckin] = relationship(back_populates="responses")


class Escalation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "escalations"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # nullable: unmatched inbound messages have no patient
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    checkin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("followup_checkins.id", ondelete="SET NULL"), nullable=True,
    )
    # red_flag | meds_missed | no_response | send_failed | opted_out | unmatched_message
    trigger: Mapped[str] = mapped_column(String(60), nullable=False)
    detail: Mapped[str] = mapped_column(String(1000), nullable=False)
    priority: Mapped[EscalationPriority] = mapped_column(
        Enum(EscalationPriority, name="escalation_priority"), nullable=False,
    )
    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus, name="escalation_status"),
        default=EscalationStatus.OPEN, nullable=False,
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadmissionEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "readmission_events"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    prior_admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"), nullable=False,
    )
    readmission_admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    days_since_discharge: Mapped[int] = mapped_column(Integer, nullable=False)
