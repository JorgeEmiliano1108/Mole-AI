"""Autenticación para endpoints internos entre microservicios.

No expone a usuarios finales; solo valida un secret compartido inyectado por
variable de entorno (`INTERNAL_API_KEY`).
"""
from django.conf import settings
from rest_framework import authentication, exceptions


class InternalAPIKeyAuthentication(authentication.BaseAuthentication):
    """Autentica requests internas mediante header `X-Internal-Key`."""

    def authenticate(self, request):
        provided = request.headers.get("X-Internal-Key", "")
        expected = getattr(settings, "INTERNAL_API_KEY", "")
        if not expected:
            raise exceptions.AuthenticationFailed("INTERNAL_API_KEY no configurada.")
        if not provided:
            raise exceptions.AuthenticationFailed("Falta header X-Internal-Key.")
        if provided != expected:
            raise exceptions.AuthenticationFailed("X-Internal-Key inválida.")
        # No retornamos user/authenticator; el endpoint es de sistema.
        return (None, None)
