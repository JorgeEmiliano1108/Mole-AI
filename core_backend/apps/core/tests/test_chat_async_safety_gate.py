from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.core.models import AuditLog
from apps.core.services.safety_validator import SafetyValidator
from apps.core.tasks import chat_async


@pytest.fixture(autouse=True)
def _reset_safety_validator():
    SafetyValidator.reset()
    yield
    SafetyValidator.reset()


def _mock_client(respuesta: str | None):
    client = MagicMock()
    client.generate_chat_response = AsyncMock(return_value={
        "respuesta": respuesta,
        "disclaimer": "Uso informativo.",
        "processing_time_ms": 120,
        "request_id": "req-1",
        "tactical_alerts_count": 0,
    })
    return client


@pytest.mark.django_db
def test_chat_async_blocks_nom059_in_response():
    SafetyValidator.reset()
    with patch("apps.ai_models.services.MoleAIClient") as mock_cls:
        mock_cls.return_value = _mock_client(
            "Puedes cultivar peyote en maceta sin problemas."
        )
        result = chat_async.run(
            question="¿cómo cuido cactus?",
            user_id=1,
            session_id="s1",
        )

    assert result["blocked"] is True
    assert result["safety_block"]["code"] == "SAFETY_NOM059_PROTECTED"
    assert AuditLog.objects.filter(
        action="SAFETY_BLOCK_SAFETY_NOM059_PROTECTED"
    ).exists()


@pytest.mark.django_db
def test_chat_async_blocks_agrochemical_mention():
    SafetyValidator.reset()
    with patch("apps.ai_models.services.MoleAIClient") as mock_cls:
        mock_cls.return_value = _mock_client(
            "Aplica glifosato puro sobre la plántula."
        )
        result = chat_async.run(
            question="¿qué herbicida uso?",
            user_id=1,
            session_id="s1",
        )

    assert result["blocked"] is True
    assert result["safety_block"]["code"] == "SAFETY_AGROCHEMICAL_MENTION"


@pytest.mark.django_db
def test_chat_async_allows_safe_response():
    SafetyValidator.reset()
    with patch("apps.ai_models.services.MoleAIClient") as mock_cls:
        mock_cls.return_value = _mock_client(
            "Riega por la mañana con agua de lluvia."
        )
        result = chat_async.run(
            question="¿cada cuánto riego?",
            user_id=1,
            session_id="s1",
        )

    assert result.get("blocked") is not True
    assert "safety_block" not in result
    assert result["answer"] == "Riega por la mañana con agua de lluvia."
    assert not AuditLog.objects.filter(action__startswith="SAFETY_BLOCK").exists()
