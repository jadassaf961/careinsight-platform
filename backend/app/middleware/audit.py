"""Audit middleware — records one row per authenticated request."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.audit import AuditLog

logger = get_logger(__name__)

_SKIP_PATHS = {"/docs", "/openapi.json", "/redoc", "/health"}
_LOGIN_PATH = f"{settings.api_v1_prefix}/auth/login"


def _extract_user_id(request: Request) -> UUID | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    sub = payload.get("sub")
    return UUID(sub) if sub else None


def _extract_resource(path: str) -> tuple[str | None, str | None]:
    parts = [p for p in path.split("/") if p]
    if len(parts) < 3:
        return None, None
    resource_type = parts[2] if len(parts) > 2 else None  # /api/v1/<resource>/...
    resource_id = parts[3] if len(parts) > 3 else None
    return resource_type, resource_id


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if request.url.path in _SKIP_PATHS or request.url.path == _LOGIN_PATH:
            return response
        if response.status_code >= 400 and response.status_code != 401:
            return response

        user_id = _extract_user_id(request)
        resource_type, resource_id = _extract_resource(request.url.path)
        client_host = request.client.host if request.client else None

        db: Session = SessionLocal()
        try:
            db.add(AuditLog(
                user_id=user_id,
                action=request.method,
                resource_type=resource_type,
                resource_id=resource_id,
                request_ip=client_host,
                payload={"path": request.url.path, "status": response.status_code},
            ))
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Audit write failed: %s", exc)
            db.rollback()
        finally:
            db.close()
        return response
