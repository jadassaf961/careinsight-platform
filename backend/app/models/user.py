"""User + Role ORM models."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    PHYSICIAN = "physician"
    RESIDENT = "resident"
    NURSE = "nurse"
    CASE_MANAGER = "case_manager"
    ANALYST = "analyst"


class Role(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(
        Enum(RoleName, name="role_name"), nullable=False, unique=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role: Mapped[Role] = relationship()
