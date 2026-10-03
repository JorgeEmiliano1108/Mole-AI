"""Tests de MCPConnectionPool.

Se mockea el SDK de cliente MCP para validar el pool persistente y
round-robin sin bloqueos globales.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase, override_settings

from apps.ai_models.infrastructure.mcp_pool import MCPConnectionPool


@override_settings(MCP_CHAT_URL="http://mole-chat:8002/mcp", MCP_TIMEOUT=10, MCP_POOL_SIZE=3)
class MCPConnectionPoolTests(TestCase):
    def setUp(self):
        # Forzar nuevo singleton por test.
        MCPConnectionPool._instance = None

    def tearDown(self):
        pool = getattr(self, "_pool", None)
        if pool:
            pool.stop()
        MCPConnectionPool._instance = None

    def _mock_sessions(self, count: int):
        """Crea N mocks de sesión listos para usarse por el pool."""
        sessions = []
        for _ in range(count):
            sess = MagicMock()
            sess.call_tool = AsyncMock(return_value={"respuesta": "ok"})
            sess.initialize = AsyncMock()
            sessions.append(sess)
        return sessions

    @patch("apps.ai_models.infrastructure.mcp_pool.sse_client")
    @patch("apps.ai_models.infrastructure.mcp_pool.ClientSession")
    def test_pool_initializes_sessions_once(self, mock_session_cls, mock_sse_client):
        sessions = self._mock_sessions(3)
        mock_session_cls.return_value.__aenter__ = AsyncMock(side_effect=sessions)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=False)

        self._pool = MCPConnectionPool()
        self._pool.call_tool("chat", {"user_id": "u1", "message": "hola"})

        for sess in sessions:
            sess.initialize.assert_called_once()

    @patch("apps.ai_models.infrastructure.mcp_pool.sse_client")
    @patch("apps.ai_models.infrastructure.mcp_pool.ClientSession")
    def test_round_robin_uses_all_sessions(self, mock_session_cls, mock_sse_client):
        sessions = self._mock_sessions(3)
        mock_session_cls.return_value.__aenter__ = AsyncMock(side_effect=sessions)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=False)

        self._pool = MCPConnectionPool()
        for i in range(3):
            result = self._pool.call_tool("chat", {"message": f"m{i}"})
            self.assertEqual(result, {"respuesta": "ok"})

        for sess in sessions:
            self.assertEqual(sess.call_tool.call_count, 1)

    @patch("apps.ai_models.infrastructure.mcp_pool.sse_client")
    @patch("apps.ai_models.infrastructure.mcp_pool.ClientSession")
    def test_call_tool_result_passed_through(self, mock_session_cls, mock_sse_client):
        sessions = self._mock_sessions(1)
        sessions[0].call_tool = AsyncMock(return_value={"respuesta": "hola"})
        mock_session_cls.return_value.__aenter__ = AsyncMock(side_effect=sessions)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=False)

        self._pool = MCPConnectionPool()
        self._pool._pool_size = 1
        result = self._pool.call_tool("chat", {"message": "hola"})
        self.assertEqual(result, {"respuesta": "hola"})

    @patch("apps.ai_models.infrastructure.mcp_pool.sse_client")
    @patch("apps.ai_models.infrastructure.mcp_pool.ClientSession")
    def test_failed_slot_retries_on_next_slot(self, mock_session_cls, mock_sse_client):
        sessions = self._mock_sessions(2)
        sessions[0].call_tool = AsyncMock(side_effect=RuntimeError("dead"))
        sessions[1].call_tool = AsyncMock(return_value={"respuesta": "ok"})
        mock_session_cls.return_value.__aenter__ = AsyncMock(side_effect=sessions)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_sse_client.return_value.__aexit__ = AsyncMock(return_value=False)

        self._pool = MCPConnectionPool()
        self._pool._pool_size = 2
        # Forzar selección del slot 0 inyectando sesiones ya listas.
        self._pool._ensure_started()
        for slot in self._pool._slots:
            slot.ready_event.set()
        self._pool._slots[0].session = sessions[0]
        self._pool._slots[1].session = sessions[1]

        result = self._pool.call_tool("chat", {"message": "hola"})
        self.assertEqual(result, {"respuesta": "ok"})
        sessions[1].call_tool.assert_called_once()
