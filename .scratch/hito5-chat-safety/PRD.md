# PRD — Hito 5: Seguridad en Interacciones Generativas (Chat RAG / MS2)

## Objetivo
Extender el `SafetyValidator` determinístico al pipeline de Chat RAG (MS2) para mitigar alucinaciones tóxicas y protección de especies NOM-059, sin degradar la UX ni ensuciar el historial de chat.

## Alcance
1. Validar **solo la salida del LLM** (respuesta de MS2), no la pregunta del usuario.
2. Bloquear respuestas que contengan especies protegidas por NOM-059 o agroquímicos fuera de límites; no persistir el turno bloqueado en `LLMRequest`.
3. Dejar rastro inmutable en `AuditLog` (`source='chat'` o `'chat_fallback'`) mediante el módulo centralizado `apps/core/services/safety_audit.py`.
4. Reflejar el bloqueo en Flutter como un turno de chat con `SafetyBlockBanner`.

## Decisiones arquitectónicas aprobadas
- **Interceptación**: en la vista síncrona `llm_chat_view` post-MS2, pre-persistencia; en el worker `chat_async` para el fallback.
- **No streaming**: MS2 actual devuelve JSON completo; la validación es síncrona de microsegundos.
- **UX**: 403 con `{error, code, source: 'chat'}`; Flutter lo convierte en un turno con banner rojo dentro del historial visual.
- **Persistencia**: solo `AuditLog` append-only; `LLMRequest` queda limpio.

## Criterios de aceptación
- Cobertura backend ≥ 80%, linter limpio en archivos tocados.
- Tests red-team: respuesta MS2 con "peyote" → 403 + `AuditLog` + 0 `LLMRequest`; respuesta segura → 200 + `LLMRequest`.
- Tests fallback: `chat_async` con respuesta insegura retorna `{blocked:true, safety_block:{...}}` + `AuditLog`.
- Flutter tests verdes y `SafetyBlockBanner` visible en el historial de chat.
