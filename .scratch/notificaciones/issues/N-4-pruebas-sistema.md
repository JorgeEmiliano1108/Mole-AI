# Issue N-4: Ejecución de pruebas del sistema

Status: ready-for-human
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
Ejecutado (todo menos teléfono):
1. FW 46/46, Flutter 107/107 (analyze 3 infos preexistentes), backend apps/ 87/87.
2. OpenAPI con my-alerts/system-events/audit-log/devices; verify-staging.sh
   extendido (anon 401/403 ×4, my-alerts 200, system-events 403 botánico +
   4 secciones admin) → STAGING-OK en vivo.
3. E2E vivo: botánico solo ve SUS alertas (humedad 9.5% + nodo offline propios);
   admin ve devices/services down (probes MS funcionan)/security real.
   Hallazgo: probes serie tardaban ~24 s (DNS caído) → ThreadPoolExecutor(3) +
   curl -m 40. Nota: nginx no arranca sin MS (upstream estático preexistente);
   staging directo a django:8080... (override /tmp 8000, no versionado).
4. Pendiente usuario en teléfono: APK contra http://98.12.2.179:8000/api/v1/
   (a) Mis avisos muestra humedad crítica+nodo offline, (b) admin abre Centro
   de fallas con 3 MS down, (c) botánico bloqueado del portal, (d) badge.
   Teardown: `docker compose -f infrastructure/docker-compose.yml down`.
