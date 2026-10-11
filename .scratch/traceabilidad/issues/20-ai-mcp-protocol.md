# 20: RF-AI-03: Model Context Protocol (MCP)

Status: ready-for-agent

## Requisito

- **ID:** RF-AI-03
- **Capa:** Agentes e IA
- **Tipo:** RF
- **Texto:** El sistema debe emplear el Model Context Protocol (MCP) para mantener la sesión abierta, permitiendo que la IA evalúe el historial previo del cultivo del usuario como contexto dinámico.

## Veredicto

❌ NO IMPLEMENTADO — MCP fue sustituido por REST.

## Evidencia

- ADR-0008: 'MCP → REST+NVIDIA: cero imports MCP; arquitectura real REST a MS1/MS2/3'.
- Comunicación HTTP/REST: `core_backend/apps/ai_models/services.py:186`, `core_backend/apps/ai_models/tasks.py:77`.
- Sesión/historial vía `LLMRequest.session_id` y Redis: `microservices/mole_chat/app/infrastructure/adapters/redis_session_store.py:29-48`.

## Delta (matriz ideal vs. estado implementado)

Discrepancia estructural: la matriz exige MCP; el estado implementado usa REST stateless + Redis/Django para sesión e historial.

## Nota normativa / riesgo

Bajo LFPDPPP, historial y contexto del cultivo son datos sensibles. El almacenamiento con `session_id` y TTL cumple minimización, pero el protocolo difiere del declarado.

## Siguiente paso sugerido

Decisión arquitectónica: implementar MCP o actualizar ficha/tesis para reflejar REST+Redis como protocolo de contexto.

## Decision 2026-10-02

Status actualizado a `ready-for-agent` tras directriz ejecutiva: pgvector/Store-and-Forward aprobados o MCP requiere implementación.
