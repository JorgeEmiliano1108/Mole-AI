# ADR-0010: Safety gate en Chat RAG (MS2)

- **Fecha:** 2026-09-28
- **Estado:** Aceptado
- **Contexto:** Hito 5 — Seguridad en Interacciones Generativas. El LLM generativo es el mayor vector de riesgo de alucinaciones toxicológicas y recomendaciones sobre especies protegidas (NOM-059). Hasta el Hito 4 el `SafetyValidator` solo protegía visión (MS1) y entradas de texto estructuradas; faltaba cerrar el pipeline de chat RAG (MS2).

## Decisiones

### 1. Validar solo la salida del LLM, no la pregunta del usuario
- Se permite que el usuario pregunte por curiosidad o fines educativos.
- Lo restrictivo es que el sistema **nunca** recomiende, avale o emita instrucciones que involucren especies protegidas o agroquímicos catalogados.
- Esto reduce falsos positivos sin debilitar el control de salida.

### 2. Punto de corte en la frontera Django, no en MS2
- **Síncrono (`llm_chat_view`):** inmediatamente después de `response.json()` y antes de persistir `LLMRequest`.
- **Asíncrono (`chat_async`):** dentro del worker Celery, antes de retornar el payload de respuesta.
- MS2 sigue siendo un servicio HTTP puro; no se le acopla lógica de seguridad ni se le exige streaming.

### 3. Bloqueo sin persistencia en historial de chat
- Si se detecta violación, no se crea `LLMRequest`.
- Se responde `403 Forbidden` con `{error, code, source: 'chat'}` (sync) o `{blocked: true, safety_block: {...}}` (async poll).
- La traza queda en `AuditLog` (`source='chat'|'chat_fallback'`) vía `apps/core/services/safety_audit.py`, que es append-only.

### 4. Extensión del SafetyValidator para texto libre
- Se añadió `check_agrochemical_mention(text)`: bloquea cualquier mención de nombre comercial o ingrediente activo catalogado en texto libre (capa fail-closed para salidas generativas desestructuradas).
- Las validaciones estructuradas por `agrochemical_id` permanecen para payloads con datos de dosis/cultivo/region.

## Consecuencias
- El chat puede perder utilidad si la respuesta segura es informationalmente neutra; esto es aceptable en el MVP bajo el principio fail-closed.
- No se rompe la compatibilidad con el contrato anterior: respuestas seguras siguen el mismo schema 200; solo se agrega el caso 403.

## Cumplimiento
- **OWASP LLM Top 10 / Excessive Agency:** se evita que el LLM emita instrucciones ejecutables sobre sustancas reguladas.
- **NIST AI RMF:** mitigación de alucinaciones toxicológicas mediante reglas duras post-generación.
- **LGEEPA / NOM-059:** doble capa de protección (MS1 + monolito) y aviso obligatorio en UI.
- **LFPDPPP:** `AuditLog.details` no contiene PII; solo IDs, códigos y fragmentos de texto de seguridad.
