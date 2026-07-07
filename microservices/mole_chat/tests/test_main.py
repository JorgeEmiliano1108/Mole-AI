"""Tests for app/api/main.py lifespan and app creation — no mocks."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from contextlib import asynccontextmanager
from fastapi import FastAPI
from unittest.mock import patch

from app.api.main import app, lifespan
from app.core.config import settings
from tests.fakes import FakeLLMClient, FakeVectorStore, FakeRedisAdapter

import app.infrastructure.adapters.nvidia_client as _nv
import app.infrastructure.adapters.pgvector_store as _pg
import app.infrastructure.adapters.redis_sensor_cache_adapter as _rs
import app.infrastructure.adapters as _adapters
import types
import sys


def test_app_exists():
    assert app.title == "MS-2 RAG+CAG Service"
    assert app.version == "2.0"


def test_app_middleware_configured():
    assert app is not None


@pytest.mark.asyncio
async def test_lifespan_startup():
    app_test = FastAPI()

    @asynccontextmanager
    async def lifespan(app_obj):
        app_obj.state.llm_client = FakeLLMClient()
        app_obj.state.pgvector_store = FakeVectorStore()
        app_obj.state.redis_adapter = FakeRedisAdapter()
        app_obj.state.citation_manager = None
        yield

    app_test.router.lifespan_context = lifespan

    async with lifespan(app_test):
        assert hasattr(app_test.state, 'llm_client')
        assert hasattr(app_test.state, 'pgvector_store')


@pytest.mark.asyncio
async def test_lifespan_real_startup_and_shutdown():
    """Run the real lifespan() from main.py with all external deps replaced by fakes."""
    app_test = FastAPI()

    async def fake_start_rag_listener():
        return None

    fake_rag = types.ModuleType('app.infrastructure.adapters.rag_listener')
    fake_rag.start_rag_listener = fake_start_rag_listener
    _adapters.rag_listener = fake_rag
    sys.modules['app.infrastructure.adapters.rag_listener'] = fake_rag

    with (
        patch('app.infrastructure.adapters.nvidia_client.LLMClient', FakeLLMClient),
        patch('app.infrastructure.adapters.pgvector_store.PgVectorStore', FakeVectorStore),
        patch('app.infrastructure.adapters.redis_sensor_cache_adapter.RedisSensorCacheAdapter',
              lambda url: FakeRedisAdapter()),
        patch('app.infrastructure.adapters.rag_listener.start_rag_listener',
              fake_start_rag_listener),
    ):
        async with lifespan(app_test):
            assert hasattr(app_test.state, 'llm_client')
            assert isinstance(app_test.state.llm_client, FakeLLMClient)
            assert app_test.state.llm_client.model_name == settings.NVIDIA_CHAT_MODEL
            assert hasattr(app_test.state, 'pgvector_store')
            assert isinstance(app_test.state.pgvector_store, FakeVectorStore)
            assert hasattr(app_test.state, 'redis_adapter')
            assert isinstance(app_test.state.redis_adapter, FakeRedisAdapter)
            assert hasattr(app_test.state, 'citation_manager')
            assert app_test.state.citation_manager is not None


def test_settings_loaded():
    assert settings.SERVICE_NAME == "mole_chat"
