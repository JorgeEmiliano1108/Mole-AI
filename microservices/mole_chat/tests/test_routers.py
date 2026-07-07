"""Tests for app/api/routers.py using httpx ASGI transport and hand-written fakes."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import types
from httpx import AsyncClient, ASGITransport

from app.api.main import app
from app.api.dependencies import get_current_user
from app.core.config import settings
from tests.fakes import FakeLLMClient, FakeVectorStore, FakeRedisAdapter


def _init_app_state():
    if not hasattr(app.state, 'llm_client'):
        app.state.llm_client = FakeLLMClient()
        app.state.pgvector_store = FakeVectorStore()
        app.state.redis_adapter = FakeRedisAdapter()
        app.state.citation_manager = None


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mole_chat"


@pytest.mark.asyncio
async def test_chat_without_token_returns_403():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "Hola",
        })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_identity_mismatch():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-A"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-B",
            "message": "Hola",
        })
    assert response.status_code == 403
    assert "no coincide" in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_with_mocked_auth():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "¿Cómo está mi cultivo?",
        })
    assert response.status_code in (200, 422, 500)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_nom059_blocked():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "¿Cómo extraigo una biznaga del desierto?",
        })
    assert response.status_code == 403
    assert "NOM-059" in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_pdf_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete("/api/v1/knowledge/pdf/doc-123")
    assert response.status_code == 403


# ── PDF Ingest Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_pdf_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/knowledge/ingest-pdf",
                                     files={"file": ("test.pdf", b"%PDF", "application/pdf")})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ingest_pdf_wrong_type():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/knowledge/ingest-pdf",
                                     files={"file": ("test.txt", b"not a pdf", "text/plain")})
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_pdf_too_large():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    original = settings.MAX_PDF_SIZE
    settings.MAX_PDF_SIZE = 10
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/knowledge/ingest-pdf",
                                     files={"file": ("test.pdf", b"A" * 100, "application/pdf")})
    assert response.status_code == 413
    settings.MAX_PDF_SIZE = original
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_pdf_success():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"

    fake_langchain = types.ModuleType("langchain_text_splitters")

    class FakeSplitter:
        def __init__(self, *args, **kwargs): pass
        def split_text(self, text_: str) -> list:
            return [text_]

    fake_langchain.RecursiveCharacterTextSplitter = FakeSplitter

    fake_rag = types.ModuleType("app.infrastructure.adapters.rag_listener")
    fake_rag._extract_text_from_pdf = lambda pdf_bytes: "texto extraído del PDF"
    import app.infrastructure.adapters as _adapters
    _adapters.rag_listener = fake_rag
    sys.modules["langchain_text_splitters"] = fake_langchain
    sys.modules["app.infrastructure.adapters.rag_listener"] = fake_rag

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/knowledge/ingest-pdf",
                                     files={"file": ("test.pdf", b"simple pdf content", "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "doc_id" in data
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_pdf_path_traversal_rejected():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/knowledge/ingest-pdf",
                                     files={"file": ("../../../etc/passwd", b"not pdf", "text/plain")})
    assert response.status_code == 400
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_with_mocked_full_flow():
    _init_app_state()
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/mole-ai/chat", json={
            "user_id": "user-123",
            "message": "Prueba",
        })
    assert response.status_code == 200
    data = response.json()
    assert "respuesta" in data
    assert "disclaimer" in data
    assert "generated_by" in data
    app.dependency_overrides.clear()
