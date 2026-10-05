"""Paridad REST vs MCP para el endpoint de chat (mcp-refactor/06).

Verifica que el cambio de transporte interno no altere el comportamiento
observable: mismos códigos, mismo disclaimer, mismos bloqueos de seguridad.
"""
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.ai_models.models import LLMRequest
from apps.ai_models.services import MoleAIServiceError
from apps.core.models import AuditLog
from apps.core.services.safety_validator import SafetyValidator

User = get_user_model()


@pytest.fixture(autouse=True)
def _reset_safety_validator():
    SafetyValidator.reset()
    yield
    SafetyValidator.reset()


@pytest.fixture
def chat_user(db):
    return User.objects.create_user(
        username="parityuser", password="pw", ai_consent=True
    )


@pytest.fixture
def auth_client(chat_user):
    client = APIClient()
    client.force_authenticate(user=chat_user)
    return client


def _rest_response(respuesta: str):
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {
        "respuesta": respuesta,
        "sources": [{"id": "s1", "title": "Fuente"}],
        "disclaimer": "Uso informativo.",
    }
    return MagicMock(return_value=mock)


def _mcp_client(respuesta: str):
    instance = MagicMock()
    instance.chat.return_value = {
        "respuesta": respuesta,
        "sources": [{"id": "s1", "title": "Fuente"}],
        "disclaimer": "Uso informativo.",
    }
    return MagicMock(return_value=instance)


@pytest.mark.django_db
@pytest.mark.parametrize("mcp_enabled", [False, True])
class TestChatMcpParity:
    def test_safe_response(self, auth_client, chat_user, mcp_enabled):
        with override_settings(MCP_ENABLED=mcp_enabled):
            if mcp_enabled:
                patch_target = patch(
                    "apps.ai_models.infrastructure.mcp_client.MCPChatClient",
                    _mcp_client("Riega por la mañana."),
                )
            else:
                patch_target = patch(
                    "apps.core.views.requests.post",
                    _rest_response("Riega por la mañana."),
                )

            with patch_target:
                resp = auth_client.post(
                    reverse("core:llm_chat"), {"message": "¿cada cuánto riego?"}
                )

        assert resp.status_code == 200
        body = resp.json()
        assert "Riega" in body["response"]
        assert body["disclaimer"] == "Uso informativo."
        assert body["sources"]
        assert LLMRequest.objects.filter(
            user=chat_user, prompt="¿cada cuánto riego?"
        ).exists()
        assert not AuditLog.objects.filter(action__startswith="SAFETY_BLOCK").exists()

    def test_blocked_nom059(self, auth_client, mcp_enabled):
        with override_settings(MCP_ENABLED=mcp_enabled):
            if mcp_enabled:
                patch_target = patch(
                    "apps.ai_models.infrastructure.mcp_client.MCPChatClient",
                    _mcp_client("Puedes transplantar peyote."),
                )
            else:
                patch_target = patch(
                    "apps.core.views.requests.post",
                    _rest_response("Puedes transplantar peyote."),
                )

            with patch_target:
                resp = auth_client.post(
                    reverse("core:llm_chat"), {"message": "¿cómo cuido cactus?"}
                )

        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == "SAFETY_BLOCKED"
        assert "NOM-059" not in body["error"]
        assert AuditLog.objects.filter(action__startswith="SAFETY_BLOCK").count() == 1
        assert LLMRequest.objects.count() == 0

    def test_blocked_agrochemical(self, auth_client, mcp_enabled):
        with override_settings(MCP_ENABLED=mcp_enabled):
            if mcp_enabled:
                patch_target = patch(
                    "apps.ai_models.infrastructure.mcp_client.MCPChatClient",
                    _mcp_client("Aplica glifosato 10 L/ha."),
                )
            else:
                patch_target = patch(
                    "apps.core.views.requests.post",
                    _rest_response("Aplica glifosato 10 L/ha."),
                )

            with patch_target:
                resp = auth_client.post(
                    reverse("core:llm_chat"), {"message": "¿qué herbicida uso?"}
                )

        assert resp.status_code == 403
        assert resp.json()["code"] == "SAFETY_BLOCKED"
        assert LLMRequest.objects.count() == 0


@pytest.mark.django_db
class TestChatMcpFallback:
    def test_mcp_failure_falls_back_to_rest(self, auth_client, chat_user):
        instance = MagicMock()
        instance.chat.side_effect = MoleAIServiceError("timeout MCP")
        mcp_mock = MagicMock(return_value=instance)

        with override_settings(MCP_ENABLED=True), patch(
            "apps.ai_models.infrastructure.mcp_client.MCPChatClient", mcp_mock
        ), patch(
            "apps.core.views.requests.post",
            _rest_response("Respuesta vía fallback REST."),
        ):
            resp = auth_client.post(
                reverse("core:llm_chat"), {"message": "hola"}
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "fallback" in body["response"]
        assert LLMRequest.objects.filter(
            user=chat_user, prompt="hola"
        ).exists()
        mcp_mock.assert_called_once()
