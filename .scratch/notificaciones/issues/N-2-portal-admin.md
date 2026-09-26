# Issue N-2: Portal admin (Dispositivos, Auditoría, Centro de fallas)

Status: needs-triage
Sev: P0 · Área: mobile+backend · Fase: N-2 · Bloqueado por: N-0

## Problema
Admin sin portal único ni fallas del sistema en tiempo real (vulns incluidas).

## Aceptación
- `/admin` con 7 accesos (existen 3; nuevos: Dispositivos sobre
  `devices/<id>/health/`+bindings, Auditoría feed `AuditLog` con filtros,
  Centro de fallas sobre `system-events`).
- Doble gate (drawer+router); botánico con URL directa → bloqueado (test).
- Severidades info/warn/error/critical; vulnerabilidades = eventos auth+admin+MS.
- Tests widget + RBAC; `analyze` 0 issues.

## Compliance
`Superadmin` solo tocado por superadmin (existe); auditoría append-only intacta.

## Comments
(none)
