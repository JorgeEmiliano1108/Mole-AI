"""Tests del cliente MCP de Django hacia mole_chat.

Se mockea MCPConnectionPool para evitar levantar el microservicio.
"""
from unittest.mock import MagicMock, patch

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

    @patch("apps.ai_models.infrastructure.mcp_client.MCPConnectionPool")
    def test_chat_success(self, mock_pool_cls):
        mock_pool = MagicMock()
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='{"respuesta": "ok", "sources": []}')]
        mock_pool.call_tool.return_value = mock_result
        mock_pool_cls.return_value = mock_pool

        client = MCPChatClient()
        result = client.chat(user_id="u1", message="hola")
        self.assertEqual(result["respuesta"], "ok")
        mock_pool.call_tool.assert_called_once_with("chat", {
            "user_id": "u1",
            "message": "hola",
        })

    @patch("apps.ai_models.infrastructure.mcp_client.MCPConnectionPool")
    def test_chat_raises_mole_ai_service_error(self, mock_pool_cls):
        mock_pool = MagicMock()
        mock_pool.call_tool.side_effect = ConnectionError("boom")
        mock_pool_cls.return_value = mock_pool

        client = MCPChatClient()
        with self.assertRaises(MoleAIServiceError):
            client.chat(user_id="u1", message="hola")
