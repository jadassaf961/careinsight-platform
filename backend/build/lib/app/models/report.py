"""Report ORM model — PDF discharge memos generated for a prediction."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Report(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    generated_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    pdf_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
