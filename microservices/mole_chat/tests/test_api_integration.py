"""Integration-level tests via httpx.AsyncClient + ASGITransport with hand-written fakes."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from httpx import AsyncClient, ASGITransport

from app.api.main import app
from app.api.dependencies import get_current_user
from tests.fakes import FakeLLMClient, FakeVectorStore, FakeRedisAdapter


@pytest.fixture(autouse=True)
def _setup_app_state():
    app.state.llm_client = FakeLLMClient()
    app.state.pgvector_store = FakeVectorStore()
    app.state.redis_adapter = FakeRedisAdapter()
    app.state.citation_manager = None
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mole_chat"


@pytest.mark.asyncio
async def test_chat_endpoint_success():
    app.dependency_overrides[get_current_user] = lambda: "user-123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "Hola",
        })
    assert response.status_code == 200
    data = response.json()
    assert "respuesta" in data
    assert "disclaimer" in data
    assert "generated_by" in data
    assert data["generated_by"] == "Mole.AI"


@pytest.mark.asyncio
async def test_chat_endpoint_user_mismatch():
    app.dependency_overrides[get_current_user] = lambda: "user-other"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "Hola",
        })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_endpoint_nom059_violation():
    app.dependency_overrides[get_current_user] = lambda: "user-123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "quiero extraer una biznaga",
        })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_endpoint_missing_user_id():
    app.dependency_overrides[get_current_user] = lambda: "user-123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "message": "Hola",
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_config_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "port" in data
    assert "db_connected" in data
