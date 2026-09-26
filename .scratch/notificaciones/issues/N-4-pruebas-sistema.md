# Issue N-4: Ejecución de pruebas del sistema

Status: needs-triage
Sev: P0 · Área: QA · Fase: N-4 · Bloqueado por: N-0..N-3

## Problema
Sin matriz de verificación E2E de notificaciones + portal.

## Aceptación
1. Suites: `make test` FW, `flutter test`, pytest (incl. RBAC 403 y scoped).
2. Contrato: OpenAPI con los 2 endpoints; `verify-staging.sh` con 200/403.
3. E2E LAN en teléfono: (a) aviso planta simulada <60 s, (b) centro fallas con
   FAILURE inyectado, (c) botánico bloqueado del portal, (d) kill MS → evento.
4. 0 TypeError, 0 PII en logs, NOM-059 intacto. Reporte con SHAs + tabla pasa/falla.

## Compliance
Evidencia de verificación (tdd); LFPDPPP en recorrido.

## Comments
(none)
