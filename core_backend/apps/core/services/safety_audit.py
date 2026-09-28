# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""Servicio centralizado de auditoría para bloqueos del SafetyValidator.

Usado por visión (MS1), chat RAG (MS2) y cualquier otro pipeline que necesite
registrar rechazos de seguridad en AuditLog de forma inmutable.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.core.services.safety_validator import SafetyResult


def log_safety_block(
    *,
    user_id: int | None,
    safety_result: SafetyResult,
    task_id: str | None,
    source: str,
) -> None:
    """Persiste un bloqueo de seguridad en AuditLog (append-only).

    Args:
        user_id: ID del usuario que originó la operación. Puede ser None.
        safety_result: resultado del SafetyValidator (debe ser `safe=False`).
        task_id: identificador de tarea Celery o de sesión.
        source: origen del bloqueo ('vision', 'chat', 'chat_fallback', etc.).
    """
    from apps.core.models import AuditLog

    AuditLog.objects.create(
        user_id=user_id,
        action=f"SAFETY_BLOCK_{safety_result.code}",
        details=json.dumps(
            {
                "source": source,
                "task_id": task_id,
                "code": safety_result.code,
                "reason": safety_result.reason,
            },
            default=str,
        ),
    )
