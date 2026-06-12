"""AI Copilot chat schemas."""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    patient_id: UUID
    message: str
    history: list[ChatHistoryItem] = []


class ChatResponse(BaseModel):
    reply: str
    disclaimer: str = (
        "AI decision-support only — not a substitute for clinical judgment."
    )
