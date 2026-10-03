"""Vistas internas de sistema (no públicas) usadas por microservicios.

Estos endpoints están protegidos por InternalAPIKeyAuthentication y nunca
quedan expuestos al exterior a través del proxy reverso.
"""
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from apps.core.authentication import InternalAPIKeyAuthentication
from apps.core.services.safety_validator import SafetyValidator
from apps.core.services.safety_audit import log_safety_block


@api_view(["POST"])
@authentication_classes([InternalAPIKeyAuthentication])
@permission_classes([])
def validate_safety_view(request):
    """POST /internal/v1/safety/validate/

    Ejecuta SafetyValidator sobre un texto y devuelve el resultado. Usado por
    mole_chat para validar la salida del LLM antes de devolverla por MCP.
    """
    text = request.data.get("text", "")
    if not text:
        return Response({"safe": True, "code": "", "reason": ""}, status=status.HTTP_200_OK)

    safety = SafetyValidator().validate({"text": text})
    if not safety.safe:
        # No tenemos user_id en este contexto interno; usamos source=mcp.
        log_safety_block(
            user_id=request.data.get("user_id"),
            safety_result=safety,
            task_id=None,
            source="mcp",
        )
    return Response(
        {
            "safe": safety.safe,
            "code": safety.code,
            "reason": safety.reason,
            "status_code": safety.status_code,
        },
        status=status.HTTP_200_OK,
    )
