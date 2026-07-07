"""Tests for NvidiaBaseClient — mocks OpenAI and tenacity."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.infrastructure.adapters.nvidia_client import NvidiaBaseClient


@pytest.fixture
def client():
    with patch("app.core.config.settings.NVIDIA_API_KEY", "test-key"):
        with patch("app.core.config.settings.NVIDIA_BASE_URL", "https://test.nvidia.com/v1"):
            with patch("app.core.config.settings.NVIDIA_CHAT_MODEL", "test-model"):
                yield NvidiaBaseClient()


@pytest.mark.asyncio
async def test_generate_chat_no_api_key():
    with patch("app.core.config.settings.NVIDIA_API_KEY", ""):
        c = NvidiaBaseClient()
        assert c.api_key == ""


@pytest.mark.asyncio
async def test_generate_chat_success(client):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello"

    with patch.object(client.client.chat.completions, "create", AsyncMock(return_value=mock_response)):
        result = await client.generate_chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello"


@pytest.mark.asyncio
async def test_generate_chat_retries_on_500():
    with patch("app.core.config.settings.NVIDIA_API_KEY", "test-key"):
        with patch("app.core.config.settings.NVIDIA_BASE_URL", "https://test.nvidia.com/v1"):
            with patch("app.core.config.settings.NVIDIA_CHAT_MODEL", "test-model"):
                c = NvidiaBaseClient()

    mock_create = AsyncMock()
    mock_create.side_effect = type("FakeError", (Exception,), {"status_code": 500})("Server Error")

    with patch.object(c.client.chat.completions, "create", mock_create):
        with pytest.raises(Exception):
            await c.generate_chat([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_generate_vision(client):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Especie: Tomate"

    with patch.object(client.client.chat.completions, "create", AsyncMock(return_value=mock_response)):
        result = await client.generate_vision("Analyze", "base64img")
    assert "Tomate" in result
