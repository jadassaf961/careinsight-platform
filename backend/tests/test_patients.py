"""Patient resource tests."""
from __future__ import annotations

from datetime import date


class TestCreatePatient:
    def test_physician_can_create(self, auth_client, physician):
        auth_client.set_user(physician)
        resp = auth_client.post("/api/v1/patients", json={
            "mrn": "MRN-TEST-001", "first_name": "Test", "last_name": "Patient",
            "dob": "1980-01-01", "sex": "Female",
        })
        assert resp.status_code == 201
        assert resp.json()["mrn"] == "MRN-TEST-001"

    def test_nurse_cannot_create(self, auth_client, nurse):
        auth_client.set_user(nurse)
        resp = auth_client.post("/api/v1/patients", json={
            "mrn": "MRN-TEST-002", "first_name": "Test", "last_name": "Patient",
            "dob": "1980-01-01", "sex": "Female",
        })
        assert resp.status_code == 403

    def test_duplicate_mrn_returns_409(self, auth_client, physician):
        auth_client.set_user(physician)
        body = {"mrn": "MRN-DUP", "first_name": "X", "last_name": "Y",
                "dob": "1980-01-01", "sex": "Female"}
        assert auth_client.post("/api/v1/patients", json=body).status_code == 201
        assert auth_client.post("/api/v1/patients", json=body).status_code == 409


class TestListPatients:
    def test_empty_returns_zero_total(self, auth_client, physician):
        auth_client.set_user(physician)
        resp = auth_client.get("/api/v1/patients")
        assert resp.status_code == 200
        assert resp.json() == {"items": [], "total": 0, "page": 1, "page_size": 25}

    def test_search_by_mrn(self, auth_client, physician):
        auth_client.set_user(physician)
        auth_client.post("/api/v1/patients", json={
            "mrn": "MRN-FIND-1", "first_name": "Aaa", "last_name": "Bbb",
            "dob": "1980-01-01", "sex": "Female",
        })
        resp = auth_client.get("/api/v1/patients?q=find-1")
        assert resp.json()["total"] == 1
