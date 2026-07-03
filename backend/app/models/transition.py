"""TransitionPlan + TransitionTask ORM models — the discharge workflow."""
from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class PlanStatus(str, enum.Enum):
    PLANNING = "planning"
    READY = "ready"
    DISCHARGED = "discharged"
    CLOSED = "closed"


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"
    SKIPPED = "skipped"


class TransitionPlan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "transition_plans"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status"),
        default=PlanStatus.PLANNING, nullable=False,
    )
    target_discharge_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    admission = relationship("Admission")
    tasks: Mapped[list["TransitionTask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan",
        order_by="TransitionTask.created_at",
    )


class TransitionTask(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "transition_tasks"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("transition_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False)  # RoleName value
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.OPEN, nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # what generated this task: "default" | "risk_tier" | a risk-factor label
    source: Mapped[str] = mapped_column(String(255), nullable=False)

    plan: Mapped[TransitionPlan] = relationship(back_populates="tasks")
