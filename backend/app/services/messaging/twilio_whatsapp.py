"""Twilio WhatsApp provider via plain REST (no SDK dependency)."""
from __future__ import annotations

import base64
import hashlib
import hmac

import httpx

from app.core.config import settings
from app.services.messaging.base import OutboundMessage, SendError

TWILIO_API = "https://api.twilio.com/2010-04-01"


class TwilioWhatsAppProvider:
    name = "twilio"

    def send(self, message: OutboundMessage) -> str:
        url = f"{TWILIO_API}/Accounts/{settings.twilio_account_sid}/Messages.json"
        try:
            resp = httpx.post(
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={
                    "From": f"whatsapp:{settings.twilio_whatsapp_from}",
                    "To": f"whatsapp:{message.to}",
                    "Body": message.body,
                },
                timeout=15,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise SendError(str(exc)) from exc
        return resp.json()["sid"]


def validate_twilio_signature(url: str, params: dict[str, str], signature: str, auth_token: str) -> bool:
    """Twilio request validation: HMAC-SHA1 over url + concatenated sorted
    form params, base64-encoded, compared to X-Twilio-Signature."""
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)
