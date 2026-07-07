"""Tests for Reports API endpoints — requires TestClient."""

import pytest

pytest.importorskip("fastapi.testclient", reason="Requires FastAPI TestClient")

from fastapi.testclient import TestClient  # noqa: E402
from unittest.mock import patch  # noqa: E402
import jwt  # noqa: E402

from app.main import app  # noqa: E402
from app.config import settings  # noqa: E402


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
    resp = client.post("/generate", json={"date_range_days": 30})
    assert resp.status_code == 403  # no auth header


def test_get_status_no_auth(client):
    resp = client.get("/abc/status")
    assert resp.status_code == 403


def test_get_status_not_found(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value=None,
    ):
        resp = client.get(
            "/nonexistent/status",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 404


def test_get_status_access_denied(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value={"hashed_user_id": "other-user", "status": "SUCCESS"},
    ):
        resp = client.get(
            "/some-job/status",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 403


def test_get_download_not_found(client, valid_token):
    with patch(
        "infrastructure.redis.job_metadata_store.JobMetadataStore.get_job",
        return_value=None,
    ):
        resp = client.get(
            "/nonexistent/download",
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
            "/some-job/download",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert resp.status_code == 400
