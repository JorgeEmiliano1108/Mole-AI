"""Tests for pgvector store adapter.

Uses FakeAsyncpgPool/FakeAsyncpgConnection (hand-written fakes) — no MagicMock.
For local development and CI without Docker.

⚠ This is the unit-test fallback. For real pgvector integration tests
   with testcontainers, see test_pgvector_integration.py (requires Docker).
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import AsyncMock, patch

from app.infrastructure.adapters.pgvector_store import PgVectorStore, settings
from app.infrastructure.adapters import pgvector_store as pgvector_module
from tests.fakes import FakeAsyncpgPool, FakeAsyncpgModule


@pytest.fixture(autouse=True)
def _patch_asyncpg():
    original = pgvector_module.asyncpg
    pgvector_module.asyncpg = FakeAsyncpgModule()
    yield
    pgvector_module.asyncpg = original


def _make_pool(fetch_return=None, fetchrow_return=None, execute_return=None):
    return FakeAsyncpgPool(
        fetch_return=fetch_return,
        fetchrow_return=fetchrow_return,
        execute_return=execute_return,
    )


@pytest.mark.asyncio
async def test_asearch_no_results():
    pool = _make_pool(fetch_return=[])
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        with patch.object(PgVectorStore, "_encode_async", AsyncMock(return_value=[[0.1, 0.2, 0.3]])):
            store = PgVectorStore()
            text, sources = await store.asearch("test query")
            assert text == ""
            assert sources == []


@pytest.mark.asyncio
async def test_asearch_with_results():
    pool = _make_pool(fetch_return=[
        {"content": "Some context", "source_name": "doc.pdf", "s3_key": "uploads/doc.pdf", "score": 0.95}
    ])
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        with patch.object(PgVectorStore, "_encode_async", AsyncMock(return_value=[[0.1, 0.2, 0.3]])):
            store = PgVectorStore()
            text, sources = await store.asearch("test query")
            assert "Some context" in text
            assert len(sources) > 0
            assert sources[0]["score"] == 0.95


@pytest.mark.asyncio
async def test_insert_chunks():
    conn_pool = FakeAsyncpgPool()
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=conn_pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        with patch.object(PgVectorStore, "_encode_async", AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])):
            store = PgVectorStore()
            result = await store.insert_chunks(
                doc_id="doc-1",
                s3_key="uploads/test.pdf",
                source_name="test.pdf",
                chunks=["chunk1", "chunk2"],
            )
            assert result == 2


@pytest.mark.asyncio
async def test_delete_by_doc_id():
    pool = _make_pool(execute_return="DELETE 3")
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        store = PgVectorStore()
        deleted = await store.delete_by_doc_id("doc-1")
        assert deleted == 3


@pytest.mark.asyncio
async def test_delete_by_doc_id_not_found():
    pool = _make_pool(execute_return="DELETE 0")
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        store = PgVectorStore()
        deleted = await store.delete_by_doc_id("nonexistent")
        assert deleted == 0


@pytest.mark.asyncio
async def test_delete_by_s3_key():
    pool = _make_pool(execute_return="DELETE 2")
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        store = PgVectorStore()
        deleted = await store.delete_by_s3_key("uploads/doc.pdf")
        assert deleted == 2


@pytest.mark.asyncio
async def test_insert_chunks_empty():
    pool = FakeAsyncpgPool()
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        store = PgVectorStore()
        result = await store.insert_chunks(
            doc_id="doc-1",
            s3_key="uploads/test.pdf",
            source_name="test.pdf",
            chunks=[],
        )
        assert result == 0


@pytest.mark.asyncio
async def test_close():
    pool = FakeAsyncpgPool()
    pgvector_module.asyncpg = type("M", (), {"create_pool": AsyncMock(return_value=pool)})()
    with patch.object(settings, "DATABASE_URL", "postgresql://test:test@localhost:5432/test"):
        store = PgVectorStore()
        store._pool = pool
        await store.close()
        assert pool._closed


@pytest.mark.asyncio
async def test_close_idempotent():
    pgvector_module.asyncpg = FakeAsyncpgModule()
    store = PgVectorStore()
    await store.close()
    assert store._pool is None
