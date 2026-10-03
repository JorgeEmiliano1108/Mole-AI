# 07: A7: Activar MCP por defecto y deprecar rama REST interna

Status: ready-for-human

## Requisito

Una vez que la paridad sea verde, cambiar `MCP_ENABLED` a `True` por defecto y documentar la deprecación del cliente REST interno.

## Acceptance criteria

- [ ] Default `MCP_ENABLED=True` en settings de producción.
- [ ] Fallback REST mantiene activo por seguridad durante un sprint.
- [ ] ADR-0011 actualizado con fecha de flip.
- [ ] Aprobación humana para el cambio en producción.

## Blocked by

- `06-mcp-parity-tests`.

## Notas

Status `ready-for-human` porque es decisión de release.

