"""Hospital + Department ORM models."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class Hospital(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    ehr_vendor: Mapped[str | None] = mapped_column(String(40), nullable=True)

    departments: Mapped[list["Department"]] = relationship(back_populates="hospital")


class Department(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("hospital_id", "code", name="uq_dept_hospital_code"),
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)

    hospital: Mapped[Hospital] = relationship(back_populates="departments")
