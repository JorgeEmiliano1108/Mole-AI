"""Tests del cliente MCP de Django hacia mole_chat.

Se mockea el SDK de cliente MCP para evitar levantar el microservicio.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase, override_settings

from apps.ai_models.infrastructure.mcp_client import MCPChatClient, _parse_tool_result
from apps.ai_models.services import MoleAIServiceError


@override_settings(MCP_CHAT_URL="http://mole-chat:8002/mcp", MCP_TIMEOUT=10)
class MCPChatClientTests(TestCase):
    def test_parse_tool_result_with_dict(self):
        data = {"respuesta": "ok", "sources": []}
        self.assertEqual(_parse_tool_result(data), data)

    def test_parse_tool_result_with_content_text(self):
        fake = MagicMock()
        fake.content = [MagicMock(text='{"respuesta": "hola"}')]
        parsed = _parse_tool_result(fake)
        self.assertEqual(parsed["respuesta"], "hola")

    def test_parse_tool_result_with_plain_text(self):
        fake = MagicMock()
        fake.content = [MagicMock(text="hola")]
        parsed = _parse_tool_result(fake)
        self.assertEqual(parsed["respuesta"], "hola")

    @patch("apps.ai_models.infrastructure.mcp_client.sse_client")
    @patch("apps.ai_models.infrastructure.mcp_client.ClientSession")
    def test_chat_success(self, mock_session_cls, mock_sse_client):
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value={"respuesta": "ok", "sources": []})
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        import asyncio
        client = MCPChatClient()
        result = asyncio.run(client.chat(user_id="u1", message="hola"))
        self.assertEqual(result["respuesta"], "ok")

    @patch("apps.ai_models.infrastructure.mcp_client.sse_client")
    @patch("apps.ai_models.infrastructure.mcp_client.ClientSession")
    def test_chat_raises_mole_ai_service_error(self, mock_session_cls, mock_sse_client):
        mock_sse_client.return_value.__aenter__ = AsyncMock(side_effect=ConnectionError("boom"))
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=False)

        import asyncio
        client = MCPChatClient()
        with self.assertRaises(MoleAIServiceError):
            asyncio.run(client.chat(user_id="u1", message="hola"))
