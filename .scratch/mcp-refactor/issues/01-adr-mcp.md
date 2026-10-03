# 01: A1: Redactar ADR-0011 — MCP como protocolo de contexto Django↔mole_chat

Status: ready-for-human

## Requisito

Documentar la decisión arquitectónica de migrar el canal interno Django ↔ mole_chat a Model Context Protocol (MCP), su relación con ADR-0008 y los límites de alcance.

## Acceptance criteria

- [ ] Nuevo archivo `docs/adr/0011-mcp-context-protocol.md` con contexto, decisión, consecuencias y cumplimiento normativo.
- [ ] Se menciona explícitamente que la API pública móvil no cambia.
- [ ] Se deja constancia del hook para futura tool `mole_vision`.
- [ ] Revisión y aprobación humana.

## Blocked by

None — can start immediately.

## Notas

Status `ready-for-human` porque requiere firma del arquitecto antes de continuar con código.

## Comments

**2026-10-02 — opencode**
ADR redactado en `docs/adr/0011-mcp-context-protocol.md`. Aprobado por directriz ejecutiva del usuario (MCP Django↔mole_chat, transporte SSE, `mole_vision` fuera del MVP, API móvil intacta). Se procede a A2.

