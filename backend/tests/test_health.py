"""Smoke tests."""


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_loads(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    # spot-check a few critical endpoints
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/patients" in paths
    assert "/api/v1/predictions" in paths
