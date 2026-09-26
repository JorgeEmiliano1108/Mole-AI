# Issue N-2: Portal admin (Dispositivos, Auditoría, Centro de fallas)

Status: ready-for-human
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
Resuelto: backend `admin/audit-log` (filtros+paginado, con IP por propósito de
seguridad) + `admin/devices/` (envelope results, sin tokens); app con
Centro de fallas (4 secciones), Dispositivos, Auditoría + panel/drawer/rutas
con doble gate; test de redirección botánico. Reportes maestro diferido:
flujo idéntico a /reportes vía proxy ya probado. Hallazgos: getJson exige
objeto (envelope, no array top-level); Override no exportado en Riverpod 3
(helper devuelve ProviderScope); Semantics fusiona labels (exclude + asserts
contains). Evidencia: backend 16/16, Flutter 102/102, analyze 0 nuevos.
