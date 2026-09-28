import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from apps.ai_models.tasks import analyze_vision_async
from apps.core.models import AIDiagnostic, AuditLog
from apps.core.services.safety_validator import SafetyValidator

User = get_user_model()


@pytest.fixture(autouse=True)
def _reset_safety_validator():
    SafetyValidator.reset()
    yield
    SafetyValidator.reset()


@pytest.fixture
def vision_user(db):
    return User.objects.create_user(username="visiontest", password="pw")


@pytest.fixture
def temp_image():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake-image-bytes")
        path = f.name
    yield path
    import os

    if os.path.exists(path):
        os.remove(path)


def _mock_post(return_value: dict):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = return_value
    return MagicMock(return_value=mock_response)


@pytest.mark.django_db
def test_blocked_nom059_species_no_diagnostic_no_audit_other(
    vision_user, temp_image
):
    SafetyValidator.reset()
    ms1_response = {
        "condition": "Desconocida",
        "confidence": 0.87,
        "species_common": "Peyote",
        "species_scientific": "Lophophora williamsii",
        "immediate_actions": ["Consultar experto"],
    }

    with patch("apps.ai_models.tasks.requests.post", _mock_post(ms1_response)):
        result = analyze_vision_async.run(
            temp_image, auth_token="Bearer tk", user_id=vision_user.id
        )

    assert result["blocked"] is True
    assert result["safety_block"]["code"] == "SAFETY_NOM059_PROTECTED"
    assert "NOM-059" in result["safety_block"]["reason"]
    assert AIDiagnostic.objects.count() == 0
    assert AuditLog.objects.filter(
        action="SAFETY_BLOCK_SAFETY_NOM059_PROTECTED", user_id=vision_user.id
    ).exists()


@pytest.mark.django_db
def test_blocked_species_in_immediate_actions(vision_user, temp_image):
    SafetyValidator.reset()
    ms1_response = {
        "condition": "Mancha foliar",
        "confidence": 0.75,
        "species_common": "Cactácea",
        "species_scientific": "Mammillaria herrerae",
        "immediate_actions": ["Aplicar fungicida; cuidado con biznaga protegida"],
    }

    with patch("apps.ai_models.tasks.requests.post", _mock_post(ms1_response)):
        result = analyze_vision_async.run(
            temp_image, auth_token="Bearer tk", user_id=vision_user.id
        )

    assert result["blocked"] is True
    assert result["safety_block"]["code"] == "SAFETY_NOM059_PROTECTED"
    assert AIDiagnostic.objects.count() == 0


@pytest.mark.django_db
def test_safe_species_creates_diagnostic_and_no_safety_audit(
    vision_user, temp_image
):
    SafetyValidator.reset()
    ms1_response = {
        "condition": "Mildiu",
        "confidence": 0.91,
        "species_common": "Tomate",
        "species_scientific": "Solanum lycopersicum",
        "immediate_actions": ["Aplicar azufre orgánico"],
    }

    with patch("apps.ai_models.tasks.requests.post", _mock_post(ms1_response)):
        result = analyze_vision_async.run(
            temp_image, auth_token="Bearer tk", user_id=vision_user.id
        )

    assert result.get("blocked") is not True
    assert "safety_block" not in result
    assert AIDiagnostic.objects.filter(user=vision_user).count() == 1
    assert not AuditLog.objects.filter(action__startswith="SAFETY_BLOCK").exists()


@pytest.mark.django_db
def test_audit_log_details_are_json_and_have_source_vision(vision_user, temp_image):
    SafetyValidator.reset()
    ms1_response = {
        "condition": "Desconocida",
        "confidence": 0.5,
        "species_common": "Peyote",
        "species_scientific": "Lophophora williamsii",
    }

    with patch("apps.ai_models.tasks.requests.post", _mock_post(ms1_response)):
        analyze_vision_async.run(
            temp_image, auth_token="Bearer tk", user_id=vision_user.id
        )

    log = AuditLog.objects.get(action__startswith="SAFETY_BLOCK")
    details = json.loads(log.details)
    assert details["source"] == "vision"
    assert details["code"] == "SAFETY_NOM059_PROTECTED"
    assert "task_id" in details
    assert "reason" in details
