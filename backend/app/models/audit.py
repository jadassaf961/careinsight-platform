"""AuditLog ORM model — one row per authenticated request."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, JSONField, TimestampMixin, UUIDPKMixin, UUIDType


class AuditLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_resource", "resource_type", "resource_id"),
        Index("ix_audit_created_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True, index=True,
    )
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    request_ip: Mapped[str | None] = mapped_column(String(60), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONField, nullable=True)
