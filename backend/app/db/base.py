"""SQLAlchemy declarative base + UUID/timestamp mixins.

Uses cross-dialect types (`sa.Uuid`, `sa.JSON`) so the same models work against
PostgreSQL in production and SQLite in tests.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, JSON, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Cross-dialect type aliases: native UUID/JSONB on Postgres, fallback on SQLite.
UUIDType = sa.Uuid(as_uuid=True)
JSONField = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
