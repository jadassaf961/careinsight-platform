"""Auth-related Pydantic schemas."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class UserMe(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    hospital_id: UUID

    model_config = {"from_attributes": True}
