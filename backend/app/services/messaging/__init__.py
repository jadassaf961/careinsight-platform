"""Provider factory — selected by MESSAGING_PROVIDER env var."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.services.messaging.base import MessagingProvider, OutboundMessage, SendError  # noqa: F401
from app.services.messaging.simulated import SimulatedProvider
from app.services.messaging.twilio_whatsapp import TwilioWhatsAppProvider


@lru_cache
def get_provider() -> MessagingProvider:
    if settings.messaging_provider == "twilio":
        return TwilioWhatsAppProvider()
    return SimulatedProvider()
