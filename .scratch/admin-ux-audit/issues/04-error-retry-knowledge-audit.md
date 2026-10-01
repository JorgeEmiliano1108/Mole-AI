# Issue 04 — Patrón unificado error + retry en Knowledge y Auditoría

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — `AdminErrorPanel` reusable integrado en Knowledge y Auditoría; tests renderizan retry y ocultan vacío en error.
- **Priority:** medium
- **Skill:** tdd

## Problema
- Knowledge: primer load fallido muestra el mensaje de error Y "Sin documentos todavía." al mismo tiempo; no hay botón Reintentar si no hay lista previa.
- Auditoría: error visible pero sin botón Reintentar (solo pull-to-refresh).
- Inconsistencia con Métricas/Usuarios/Dispositivos/Fallas que sí tienen retry.

## Evidencia
- `mobile/lib/features/admin/knowledge_screen.dart:178-193`
- `mobile/lib/features/admin/audit_screen.dart:102-111`

## Solución
Unificar estado: si hay error, mostrar banner de error con botón Reintentar; NO mostrar estado vacío. Extraer widget reusable `AdminErrorRetry` si no existe.

## Tests
- Widget tests: estado de error renderiza retry, no renderiza vacío.

## Criterio de aceptación
- Ambas pantallas tienen retry explícito visible en estado de error.
