"""Messaging provider interface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SendError(Exception):
    """Raised when a provider fails to deliver a message."""


@dataclass
class OutboundMessage:
    to: str
    body: str


class MessagingProvider(Protocol):
    name: str

    def send(self, message: OutboundMessage) -> str:
        """Send and return the provider's message id. Raises SendError."""
        ...
