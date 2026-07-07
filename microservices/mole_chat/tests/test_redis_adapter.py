"""Tests for Redis sensor cache adapter — uses hand-written FakeRedis (no mocks)."""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.infrastructure.adapters.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from app.infrastructure.adapters import redis_sensor_cache_adapter
from tests.fakes import FakeAioRedisModule, FakeAioRedisRaiser


@pytest.fixture(autouse=True)
def _patch_aioredis():
    original = redis_sensor_cache_adapter.aioredis
    redis_sensor_cache_adapter.aioredis = FakeAioRedisModule()
    yield
    redis_sensor_cache_adapter.aioredis = original


@pytest.mark.asyncio
async def test_get_context_found():
    adapter = RedisSensorCacheAdapter("redis://fake:6379/0")
    redis = await adapter._get_redis()
    await redis.setex("mqtt:context:user-1", 300, '{"temp": 25}')
    result = await adapter.get_context("user-1")
    assert result == '{"temp": 25}'


@pytest.mark.asyncio
async def test_get_context_missing():
    adapter = RedisSensorCacheAdapter("redis://fake:6379/0")
    result = await adapter.get_context("user-missing")
    assert result == {}


@pytest.mark.asyncio
async def test_close():
    adapter = RedisSensorCacheAdapter("redis://fake:6379/0")
    redis = await adapter._get_redis()
    await adapter.close()
    assert redis._closed


@pytest.mark.asyncio
async def test_close_idempotent():
    adapter = RedisSensorCacheAdapter("redis://fake:6379/0")
    await adapter.close()
    assert adapter._redis is None


@pytest.mark.asyncio
async def test_get_context_connection_error():
    def raise_from_url(url: str, **kwargs):
        return FakeAioRedisRaiser(ConnectionError("redis down"))
    redis_sensor_cache_adapter.aioredis = type("FakeModule", (), {"from_url": raise_from_url})()  # type: ignore
    adapter = RedisSensorCacheAdapter("redis://fake:6379/0")
    result = await adapter.get_context("user-1")
    assert result == {}


def test_build_tls_kwargs_no_paths(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "TLS_CERT_PATH", None)
    monkeypatch.setattr(settings, "TLS_KEY_PATH", None)
    monkeypatch.setattr(settings, "TLS_CA_PATH", None)
    adapter = RedisSensorCacheAdapter("redis://localhost:6379/0")
    assert adapter._tls_kwargs == {}


def test_build_tls_kwargs_with_paths(monkeypatch, tmp_path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    ca = tmp_path / "ca.pem"
    cert.touch()
    key.touch()
    ca.touch()

    from app.core.config import settings
    monkeypatch.setattr(settings, "TLS_CERT_PATH", str(cert))
    monkeypatch.setattr(settings, "TLS_KEY_PATH", str(key))
    monkeypatch.setattr(settings, "TLS_CA_PATH", str(ca))
    adapter = RedisSensorCacheAdapter("redis://localhost:6379/0")
    assert adapter._tls_kwargs == {
        "ssl_certfile": str(cert),
        "ssl_keyfile": str(key),
        "ssl_ca_certs": str(ca),
        "ssl": True,
    }
