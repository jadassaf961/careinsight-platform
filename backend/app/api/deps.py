"""FastAPI dependencies: current user resolution and RBAC enforcement."""
from __future__ import annotations

from typing import Iterable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import RoleName, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    user = db.get(User, UUID(sub))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(*allowed: RoleName):
    """Dependency factory enforcing the caller has one of *allowed* roles."""
    allowed_names = {r.value for r in allowed}

    def _enforce(user: User = Depends(get_current_user)) -> User:
        if user.role.name.value not in allowed_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {sorted(allowed_names)}",
            )
        return user

    return _enforce


def require_any_clinical_role():
    return require_role(
        RoleName.ADMIN, RoleName.PHYSICIAN, RoleName.RESIDENT,
        RoleName.NURSE, RoleName.CASE_MANAGER, RoleName.PHARMACIST,
    )
