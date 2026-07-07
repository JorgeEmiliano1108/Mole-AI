"""Tests for domain abstractions — no mocks, hand-written concrete subclasses."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.domain.chat import SensorCachePort, CitationManagerPort, SessionStorePort


class FakeSensorCache(SensorCachePort):
    async def get_context(self, user_id: str):
        return {"temp": 25}


class FakeCitationManager(CitationManagerPort):
    async def extract_sources(self, context: dict) -> list:
        return []


class FakeSessionStore(SessionStorePort):
    def __init__(self):
        self._data = {}

    async def get_session(self, session_id: str):
        return self._data.get(session_id)

    async def set_session(self, session_id: str, data: dict, ttl: int = 900):
        self._data[session_id] = data

    async def delete_session(self, session_id: str):
        self._data.pop(session_id, None)


class TestSensorCachePort:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            SensorCachePort()

    @pytest.mark.asyncio
    async def test_concrete_implementation(self):
        impl = FakeSensorCache()
        result = await impl.get_context("user-123")
        assert result == {"temp": 25}


class TestCitationManagerPort:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            CitationManagerPort()

    @pytest.mark.asyncio
    async def test_concrete_implementation(self):
        impl = FakeCitationManager()
        result = await impl.extract_sources({})
        assert result == []


class TestSessionStorePort:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            SessionStorePort()

    @pytest.mark.asyncio
    async def test_concrete_implementation(self):
        impl = FakeSessionStore()
        assert await impl.get_session("x") is None
        await impl.set_session("x", {"a": 1})
        assert await impl.get_session("x") == {"a": 1}
        await impl.delete_session("x")
        assert await impl.get_session("x") is None
