# 05: A5: Aplicar SafetyValidator a nivel de tool call y respuesta final

Status: ready-for-agent

## Requisito

Garantizar que MCP no relaje el cumplimiento normativo: validar inputs/outputs de tools y la respuesta final del LLM.

## Acceptance criteria

- [ ] `SafetyValidator` aplicado al resultado de cada tool antes de inyectarlo al contexto.
- [ ] `SafetyValidator` aplicado a la respuesta final generada por el orquestador.
- [ ] Si una tool devuelve contenido bloqueado, se registra en `AuditLog` y se devuelve mensaje seguro al LLM.
- [ ] Tests red-team: queries de agroquímicos y especies protegidas siguen bloqueándose vía MCP.

## Blocked by

- `04-django-mcp-client`.

## Notas

Cumplimiento LFPDPPP, NOM-059, COFEPRIS, NIST AI RMF.

