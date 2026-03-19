import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_vision_route(monkeypatch):
    class DummyUseCase:
        async def execute(self, image_bytes, metadata=None):
            return {"condition": "Healthy", "confidence": 0.99}
    app.dependency_overrides[app.main.get_diagnostic_use_case] = lambda: DummyUseCase()
    response = client.post("/api/v1/vision/analyze", files={"file": ("test.jpg", b"fakebytes")})
    assert response.status_code == 200
    assert response.json()["condition"] == "Healthy"
