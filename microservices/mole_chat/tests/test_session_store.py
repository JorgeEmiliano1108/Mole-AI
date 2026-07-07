"""Tests for Redis session store — uses hand-written FakeRedis (no mocks)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import json
from unittest.mock import patch

from app.infrastructure.adapters.redis_session_store import RedisSessionStoreAdapter
from app.infrastructure.adapters import redis_session_store
from tests.fakes import FakeAioRedisModule, FakeAioRedisRaiser


@pytest.fixture(autouse=True)
def _patch_aioredis():
    """Replace aioredis module with FakeAioRedisModule for every test."""
    original = redis_session_store.aioredis
    redis_session_store.aioredis = FakeAioRedisModule()
    yield
    redis_session_store.aioredis = original


@pytest.mark.asyncio
async def test_set_and_get_session():
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    await store.set_session("sess-123", {"history": ["hi"]})
    result = await store.get_session("sess-123")
    assert result == {"history": ["hi"]}


@pytest.mark.asyncio
async def test_get_session_missing():
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    result = await store.get_session("sess-missing")
    assert result is None


@pytest.mark.asyncio
async def test_delete_session():
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    await store.set_session("sess-123", {"data": "val"})
    assert await store.get_session("sess-123") == {"data": "val"}
    await store.delete_session("sess-123")
    assert await store.get_session("sess-123") is None


@pytest.mark.asyncio
async def test_close():
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    redis = await store._get_redis()
    await store.close()
    assert redis._closed


@pytest.mark.asyncio
async def test_close_idempotent():
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    await store.close()
    assert store._redis is None


@pytest.mark.asyncio
async def test_get_session_exception():
    def raise_from_url(url: str, **kwargs):
        return FakeAioRedisRaiser(ConnectionError("redis down"))
    module = FakeAioRedisModule()
    module.from_url = raise_from_url  # type: ignore
    redis_session_store.aioredis = module  # type: ignore
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    result = await store.get_session("sess-err")
    assert result is None


@pytest.mark.asyncio
async def test_set_session_exception():
    def raise_from_url(url: str, **kwargs):
        return FakeAioRedisRaiser(TimeoutError("timeout"))
    module = FakeAioRedisModule()
    module.from_url = raise_from_url  # type: ignore
    redis_session_store.aioredis = module  # type: ignore
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    await store.set_session("sess-err", {"data": "val"})


@pytest.mark.asyncio
async def test_delete_session_exception():
    def raise_from_url(url: str, **kwargs):
        return FakeAioRedisRaiser(OSError("connection lost"))
    module = FakeAioRedisModule()
    module.from_url = raise_from_url  # type: ignore
    redis_session_store.aioredis = module  # type: ignore
    store = RedisSessionStoreAdapter(redis_url="redis://fake:6379/0")
    await store.delete_session("sess-err")
