from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.ai_models.models import LLMRequest
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
    user = User.objects.create_user(
        username="chatuser", password="pw", ai_consent=True
    )
    return user


@pytest.fixture
def auth_client(chat_user):
    client = APIClient()
    client.force_authenticate(user=chat_user)
    return client


def _mock_post(respuesta: str | None, status_code: int = 200):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "respuesta": respuesta,
        "sources": [],
        "disclaimer": "Uso informativo.",
    }
    return MagicMock(return_value=mock_response)


@pytest.mark.django_db
class TestChatSafetyGate:
    def test_blocked_nom059_species_returns_403_and_audit_log(self, auth_client):
        SafetyValidator.reset()
        with patch(
            "apps.core.views.requests.post",
            _mock_post("Puedes transplantar peyote si usas guantes."),
        ):
            resp = auth_client.post(
                reverse("core:llm_chat"), {"message": "¿cómo cuido cactus?"}
            )

        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == "SAFETY_NOM059_PROTECTED"
        assert "NOM-059" in body["error"]
        assert body["source"] == "chat"
        assert AuditLog.objects.filter(action__startswith="SAFETY_BLOCK").count() == 1
        assert LLMRequest.objects.count() == 0

    def test_blocked_agrochemical_mention_returns_403(self, auth_client):
        SafetyValidator.reset()
        with patch(
            "apps.core.views.requests.post",
            _mock_post("Aplica glifosato 10 litros por hectárea."),
        ):
            resp = auth_client.post(
                reverse("core:llm_chat"), {"message": "¿qué herbicida uso?"}
            )

        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == "SAFETY_AGROCHEMICAL_MENTION"
        assert LLMRequest.objects.count() == 0

    def test_safe_response_saves_llm_request(self, auth_client, chat_user):
        SafetyValidator.reset()
        with patch(
            "apps.core.views.requests.post",
            _mock_post("Riega por la mañana con agua de lluvia."),
        ):
            resp = auth_client.post(
                reverse("core:llm_chat"), {"message": "¿cada cuánto riego?"}
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "Riega" in body["response"]
        assert LLMRequest.objects.filter(
            user=chat_user, prompt="¿cada cuánto riego?"
        ).exists()
        assert not AuditLog.objects.filter(action__startswith="SAFETY_BLOCK").exists()

    def test_empty_response_is_safe(self, auth_client, chat_user):
        SafetyValidator.reset()
        with patch("apps.core.views.requests.post", _mock_post(None)):
            resp = auth_client.post(
                reverse("core:llm_chat"), {"message": "hola"}
            )

        assert resp.status_code == 200
        assert LLMRequest.objects.filter(user=chat_user, prompt="hola").exists()
