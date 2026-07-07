"""Tests for PgVectorAdapter — mocks asyncpg and OpenAI.

Uses TDD approach:
1. RED: test defines expected behavior, fails without implementation
2. GREEN: implementation via mocks
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.vector.pgvector_adapter import PgVectorAdapter


def _make_mock_pool(rows):
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=rows)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_conn

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = mock_cm
    return mock_pool


@pytest.mark.asyncio
async def test_search_no_database_url():
    adapter = PgVectorAdapter()
    with patch("app.config.settings.database_url", None):
        result = await adapter.search("test query")
    assert result == ""


@pytest.mark.asyncio
async def test_search_empty_pool_creates_one():
    adapter = PgVectorAdapter()
    mock_pool = _make_mock_pool([])

    with patch("app.config.settings.database_url", "postgresql://localhost:5432/test"):
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
            with patch.object(adapter, "_encode", return_value="[0.1,0.2,0.3]"):
                result = await adapter.search("test query")
    assert result == ""


@pytest.mark.asyncio
async def test_search_with_results():
    adapter = PgVectorAdapter()
    rows = [
        {"content": "First chunk content", "source_name": "doc_1", "s3_key": "path/1", "score": 0.95},
        {"content": "Second chunk content", "source_name": "doc_2", "s3_key": "path/2", "score": 0.87},
    ]
    mock_pool = _make_mock_pool(rows)

    with patch("app.config.settings.database_url", "postgresql://localhost:5432/test"):
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
            with patch.object(adapter, "_encode", return_value="[0.1,0.2,0.3]"):
                result = await adapter.search("test query", top_k=2)
    assert "First chunk content" in result
    assert "Second chunk content" in result


@pytest.mark.asyncio
async def test_encode_calls_openai():
    adapter = PgVectorAdapter()
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3]

    with patch("app.config.settings.nvidia_api_key", "test-key"):
        with patch("infrastructure.vector.pgvector_adapter.OpenAI") as mock_client_cls:
            mock_client_cls.return_value.embeddings.create.return_value = mock_response
            result = adapter._encode("test query")
    assert result == "[0.1,0.2,0.3]"
