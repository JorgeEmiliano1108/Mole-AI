import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    # ensure tests don't attempt to load a real model by default
    monkeypatch.setenv("CNN_MODEL_PATH", "/tmp/nonexistent-model.tflite")
    yield


def test_reject_missing_token(monkeypatch):
    # import app after any monkeypatching to ensure startup hooks run under test control
    from ms1_vision.app.main import app

    client = TestClient(app)

    response = client.post("/api/v1/vision/analyze", files={"file": ("test.jpg", b"fakebytes")})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["status"] == 401


def test_reject_null_token(monkeypatch):
    from ms1_vision.app.main import app

    client = TestClient(app)
    headers = {"Authorization": "Bearer null"}
    response = client.post("/api/v1/vision/analyze", files={"file": ("test.jpg", b"fakebytes")}, headers=headers)
    assert response.status_code == 401


def test_healthz_reports_unhealthy_when_model_missing(monkeypatch):
    # Simulate model load failure by monkeypatching get_vision_client to raise
    import importlib

    deps = importlib.import_module("ms1_vision.app.dependencies")

    def _fail():
        raise RuntimeError("model missing")

    monkeypatch.setattr(deps, "get_vision_client", _fail)

    from ms1_vision.app.main import app
    client = TestClient(app)
    resp = client.get("/api/v1/vision/healthz")
    assert resp.status_code == 503
    body = resp.json()
    assert body["detail"]["checks"]["model_loaded"] is False
