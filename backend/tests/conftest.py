"""Pytest fixtures — uses an in-memory SQLite for fast unit testing."""
from __future__ import annotations

import os
from collections.abc import Iterator

# Force test-only settings BEFORE importing the app modules.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SEED_DEMO_DATA", "false")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401 - ensure model registration
from app.api.deps import get_current_user
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.hospital import Department, Hospital
from app.models.user import Role, RoleName, User


# SQLite engine that all tests share (note: SQLite ignores PG JSONB and partial
# indexes via SQLAlchemy compilation differences — for tests, this is fine
# because we are exercising business logic, not migrations).
TEST_ENGINE = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(bind=TEST_ENGINE, autoflush=False, future=True)


@pytest.fixture(autouse=True)
def _reset_db() -> Iterator[None]:
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield


def _override_get_db() -> Iterator[Session]:
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def db() -> Iterator[Session]:
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def hospital(db: Session) -> Hospital:
    h = Hospital(name="Test Hospital", slug="test-hospital")
    db.add(h)
    db.flush()
    db.add(Department(hospital_id=h.id, name="Med", code="MED"))
    db.commit()
    db.refresh(h)
    return h


def _make_user(db: Session, hospital: Hospital, role_name: RoleName) -> User:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        db.flush()
    user = User(
        hospital_id=hospital.id, role_id=role.id,
        email=f"{role_name.value}@test.local", full_name=f"Test {role_name.value}",
        password_hash=hash_password("Demo123!"), is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def physician(db: Session, hospital: Hospital) -> User:
    return _make_user(db, hospital, RoleName.PHYSICIAN)


@pytest.fixture
def admin_user(db: Session, hospital: Hospital) -> User:
    return _make_user(db, hospital, RoleName.ADMIN)


@pytest.fixture
def nurse(db: Session, hospital: Hospital) -> User:
    return _make_user(db, hospital, RoleName.NURSE)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """Returns a TestClient with the auth dependency overridden to bypass JWT."""

    def _override(user_holder):
        def _resolver():
            return user_holder["user"]
        return _resolver

    # Test cases call set_user(user) on this client.
    holder: dict = {"user": None}

    def set_user(u: User) -> None:
        holder["user"] = u

    app.dependency_overrides[get_current_user] = lambda: holder["user"]
    client.set_user = set_user  # type: ignore[attr-defined]
    yield client
    app.dependency_overrides.pop(get_current_user, None)
