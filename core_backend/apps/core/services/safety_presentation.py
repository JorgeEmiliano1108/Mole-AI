"""Presentación pública de bloqueos de seguridad (silent-compliance).

El sistema cumple la normativa internamente (SafetyValidator + AuditLog con
código/motivo reales), pero la interfaz expone solo mensajes genéricos: no se
mencionan normas (NOM-059, COFEPRIS) ni códigos internos al usuario para no
asumir responsabilidad legal explícita en la UX.
"""
from __future__ import annotations

PUBLIC_BLOCK_MESSAGE = "Contenido bloqueado por directrices de seguridad interna."
PUBLIC_BLOCK_CODE = "SAFETY_BLOCKED"


def public_safety_error(source: str = "chat") -> dict:
    """Payload 403 genérico para respuestas HTTP directas."""
    return {"error": PUBLIC_BLOCK_MESSAGE, "code": PUBLIC_BLOCK_CODE, "source": source}


def public_safety_block() -> dict:
    """Payload genérico para workers Celery (polling)."""
    return {
        "blocked": True,
        "safety_block": {
            "code": PUBLIC_BLOCK_CODE,
            "reason": PUBLIC_BLOCK_MESSAGE,
        },
    }
