"""In-memory provider — used for demos and local dev. Outbound bodies are
persisted on the checkin row (sent_body), so the UI reads them from the DB."""
from __future__ import annotations

import uuid

from app.services.messaging.base import OutboundMessage


class SimulatedProvider:
    name = "simulated"

    def send(self, message: OutboundMessage) -> str:  # noqa: ARG002 - body persisted by caller
        return f"sim-{uuid.uuid4()}"
