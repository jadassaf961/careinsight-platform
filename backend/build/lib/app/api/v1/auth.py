"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.name.value, "hospital_id": str(user.hospital_id)},
    )
    return TokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_ttl_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(current: User = Depends(get_current_user)) -> TokenResponse:
    token = create_access_token(
        subject=current.id,
        extra_claims={
            "role": current.role.name.value,
            "hospital_id": str(current.hospital_id),
        },
    )
    return TokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_ttl_minutes * 60,
    )


@router.get("/me", response_model=UserMe)
def me(current: User = Depends(get_current_user)) -> UserMe:
    return UserMe(
        id=current.id,
        email=current.email,
        full_name=current.full_name,
        role=current.role.name.value,
        hospital_id=current.hospital_id,
    )
