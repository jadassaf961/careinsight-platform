"""Auth + RBAC tests."""
from __future__ import annotations

from app.core.security import create_access_token, decode_token, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        h = hash_password("Demo123!")
        assert verify_password("Demo123!", h)
        assert not verify_password("wrong", h)


class TestJWT:
    def test_encode_decode_roundtrip(self):
        token = create_access_token(subject="abc", extra_claims={"role": "physician"})
        payload = decode_token(token)
        assert payload["sub"] == "abc"
        assert payload["role"] == "physician"


class TestLoginEndpoint:
    def test_invalid_credentials_returns_401(self, client, physician):
        resp = client.post("/api/v1/auth/login",
                           json={"email": physician.email, "password": "wrong"})
        assert resp.status_code == 401

    def test_valid_credentials_returns_token(self, client, physician):
        resp = client.post("/api/v1/auth/login",
                           json={"email": physician.email, "password": "Demo123!"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert "access_token" in body


class TestRBAC:
    def test_admin_only_endpoint_rejects_nurse(self, auth_client, nurse):
        auth_client.set_user(nurse)
        resp = auth_client.get("/api/v1/admin/audit-logs")
        assert resp.status_code == 403

    def test_admin_only_endpoint_allows_admin(self, auth_client, admin_user):
        auth_client.set_user(admin_user)
        resp = auth_client.get("/api/v1/admin/audit-logs")
        assert resp.status_code == 200
