"""Tests for generic async circuit breaker (I-03)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import asyncio

from app.core.circuit_breaker import AsyncCircuitBreaker, CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_successful_call():
    cb = AsyncCircuitBreaker(name="test", fail_max=3, reset_timeout=60)
    result = await cb.call(lambda: _success())
    assert result == "ok"
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0


@pytest.mark.asyncio
async def test_failure_opens_after_fail_max():
    cb = AsyncCircuitBreaker(name="test", fail_max=2, reset_timeout=60)
    with pytest.raises(RuntimeError):
        await cb.call(lambda: _fail())
    assert cb.state == "CLOSED"  # 1st failure
    assert cb.failure_count == 1

    with pytest.raises(RuntimeError):
        await cb.call(lambda: _fail())
    assert cb.state == "OPEN"  # 2nd failure = fail_max
    assert cb.failure_count == 2


@pytest.mark.asyncio
async def test_open_breaker_raises_immediately():
    cb = AsyncCircuitBreaker(name="test", fail_max=1, reset_timeout=60)
    with pytest.raises(RuntimeError):
        await cb.call(lambda: _fail())
    assert cb.state == "OPEN"

    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(lambda: _success())


@pytest.mark.asyncio
async def test_half_open_recovers_on_success():
    cb = AsyncCircuitBreaker(name="test", fail_max=1, reset_timeout=0.1)
    with pytest.raises(RuntimeError):
        await cb.call(lambda: _fail())
    assert cb.state == "OPEN"

    await asyncio.sleep(0.15)  # wait for reset timeout
    result = await cb.call(lambda: _success())
    assert result == "ok"
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0


@pytest.mark.asyncio
async def test_concurrent_safety():
    cb = AsyncCircuitBreaker(name="test", fail_max=3, reset_timeout=60)

    async def concurrent_call():
        return await cb.call(lambda: _success())

    results = await asyncio.gather(*[concurrent_call() for _ in range(10)])
    assert all(r == "ok" for r in results)
    assert cb.state == "CLOSED"


async def _success():
    return "ok"

async def _fail():
    raise RuntimeError("intentional failure")
