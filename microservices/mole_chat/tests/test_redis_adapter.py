import pytest
import asyncio


from app.infrastructure.adapters.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from app.infrastructure.adapters import redis_sensor_cache_adapter

@pytest.mark.asyncio
async def test_redis_adapter_handles_connection_error(monkeypatch):
    # Simulate aioredis.from_url raising a connection error
    async def fake_from_url(url, decode_responses=True):
        raise ConnectionError("simulated connection failure")

    # Patch the module-level aioredis in the adapter module
    monkeypatch.setattr(redis_sensor_cache_adapter, "aioredis", type("m", (), {"from_url": fake_from_url}))

    adapter = RedisSensorCacheAdapter("redis://localhost:6379/0")

    # Should not raise and should return fallback empty dict
    ctx = await adapter.get_context("test-user")
    assert isinstance(ctx, dict)
    assert ctx == {}