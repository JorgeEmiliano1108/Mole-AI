"""Tests para el endpoint interno de validación de seguridad Django → microservicios."""
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from apps.core.internal_views import validate_safety_view


@override_settings(INTERNAL_API_KEY="secret-internal-key")
class InternalSafetyValidateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_missing_header_returns_403(self):
        request = self.factory.post(reverse("core:internal_safety_validate"), {"text": "hola"}, format="json")
        response = validate_safety_view(request)
        self.assertEqual(response.status_code, 403)

    def test_invalid_key_returns_403(self):
        request = self.factory.post(
            reverse("core:internal_safety_validate"),
            {"text": "hola"},
            format="json",
            HTTP_X_INTERNAL_KEY="wrong-key",
        )
        response = validate_safety_view(request)
        self.assertEqual(response.status_code, 403)

    def test_empty_text_returns_safe(self):
        request = self.factory.post(
            reverse("core:internal_safety_validate"),
            {"text": ""},
            format="json",
            HTTP_X_INTERNAL_KEY="secret-internal-key",
        )
        response = validate_safety_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["safe"])

    @patch("apps.core.internal_views.log_safety_block")
    @patch("apps.core.internal_views.SafetyValidator")
    def test_blocked_text_audits_and_returns_unsafe(self, mock_validator_cls, mock_audit):
        from apps.core.services.safety_validator import SafetyResult

        mock_validator_cls.return_value.validate.return_value = SafetyResult(
            safe=False,
            code="SAFETY_NOM059_PROTECTED",
            reason="Especie protegida.",
            status_code=403,
        )
        request = self.factory.post(
            reverse("core:internal_safety_validate"),
            {"text": "quiero vender biznagas", "user_id": 7},
            format="json",
            HTTP_X_INTERNAL_KEY="secret-internal-key",
        )
        response = validate_safety_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["safe"])
        self.assertEqual(response.data["code"], "SAFETY_NOM059_PROTECTED")
        mock_audit.assert_called_once()

    @patch("apps.core.internal_views.SafetyValidator")
    def test_safe_text_returns_safe(self, mock_validator_cls):
        from apps.core.services.safety_validator import SafetyResult

        mock_validator_cls.return_value.validate.return_value = SafetyResult.ok()
        request = self.factory.post(
            reverse("core:internal_safety_validate"),
            {"text": "cómo hacer compost"},
            format="json",
            HTTP_X_INTERNAL_KEY="secret-internal-key",
        )
        response = validate_safety_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["safe"])
