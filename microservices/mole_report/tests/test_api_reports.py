"""Tests for Reports API endpoints — requires TestClient.

Rutas con prefijo /api/v1/reports (coherente con nginx + proxy Django,
issue 11): el TestClient ejerce el mismo path que producción.
"""

import pytest

pytest.importorskip("fastapi.testclient", reason="Requires FastAPI TestClient")

from unittest.mock import patch

import jwt
from app.config import settings
from app.main import app
from fastapi.testclient import TestClient

P = "/api/v1/reports"


@pytest.fixture
def client(fake_env_vars):
    return TestClient(app)


@pytest.fixture
def valid_token():
    return jwt.encode(
        {"sub": "user-1", "email": "test@test.com", "role": "authenticated"},
        settings.jwt_secret_key,
        algorithm="HS256",
    )


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_generate_no_auth(client):
    resp = client.post(f"{P}/generate", json={"date_range_days": 30})
    assert resp.status_code == 403  # no auth header


def test_get_status_no_auth(client):
    resp = client.get(f"{P}/abc/status")
    assert resp.status_code == 403


def test_get_status_not_found(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value=None,
    ):
        resp = client.get(
            f"{P}/nonexistent/status",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 404


def test_get_status_access_denied(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value={"hashed_user_id": "other-user", "status": "SUCCESS"},
    ):
        resp = client.get(
            f"{P}/some-job/status",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 403


def test_get_download_not_found(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value=None,
    ):
        resp = client.get(
            f"{P}/nonexistent/download",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 404


def test_get_download_not_ready(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value={
            "hashed_user_id": "abc",
            "status": "STARTED",
        },
    ):
        resp = client.get(
            f"{P}/some-job/download",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 400
