"""Cliente para el endpoint interno de validación de seguridad de Django.

mole_chat delega la validación legal/agroquímica al SafetyValidator del
backend (única fuente de verdad), consumiendo `/internal/v1/safety/validate/`
con una API key interna compartida.

Fail-closed: cualquier error de red o respuesta inesperada se traduce a
`safe=False`.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class SafetyValidationResult:
    def __init__(self, safe: bool, code: str = "", reason: str = "", status_code: int = 200):
        self.safe = safe
        self.code = code
        self.reason = reason
        self.status_code = status_code


class SafetyClient:
    """Cliente asíncrono para el validador de seguridad del host Django."""

    def __init__(self, url: str | None = None, api_key: str | None = None, timeout: float = 10.0):
        self.url = url or settings.SAFETY_VALIDATOR_URL
        self.api_key = api_key or settings.INTERNAL_API_KEY
        self.timeout = timeout

    async def validate(self, text: str, user_id: str | None = None) -> SafetyValidationResult:
        """Envía texto al validador de Django y devuelve SafetyValidationResult.

        Fail-closed: si falla la comunicación, se considera inseguro.
        """
        if not text:
            return SafetyValidationResult(safe=True, code="SAFETY_OK")

        payload: dict[str, Any] = {"text": text}
        if user_id:
            payload["user_id"] = user_id

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Internal-Key"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.url, json=payload, headers=headers)
        except Exception as exc:  # noqa: BLE001
            logger.error("Safety validator unreachable: %s", exc)
            return SafetyValidationResult(
                safe=False,
                code="SAFETY_VALIDATOR_UNREACHABLE",
                reason="No se pudo contactar al validador de seguridad; bloqueado por política.",
                status_code=503,
            )

        try:
            data = response.json()
        except Exception:  # noqa: BLE001
            logger.error("Invalid JSON from safety validator: %s", response.text[:200])
            return SafetyValidationResult(
                safe=False,
                code="SAFETY_VALIDATOR_INVALID",
                reason="Respuesta inválida del validador de seguridad; bloqueado por política.",
                status_code=502,
            )

        if response.status_code == 200:
            return SafetyValidationResult(
                safe=bool(data.get("safe", False)),
                code=data.get("code", ""),
                reason=data.get("reason", ""),
                status_code=data.get("status_code", 200),
            )

        # Auth errors or any other HTTP error -> fail closed.
        return SafetyValidationResult(
            safe=False,
            code=data.get("code", "SAFETY_VALIDATOR_ERROR"),
            reason=data.get("reason", "Error del validador de seguridad."),
            status_code=response.status_code,
        )
