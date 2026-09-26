# PRD — Notificaciones de plantas + portal admin de fallas

**Decisiones fijadas**: botánico y admin reciben avisos de SUS plantas (scoped a
colección propia); portal de fallas del sistema SOLO admin; polling 30 s solo
visible + backoff; local-notify en error+warn (dedup por id); sin FCM/websockets.
**Skills**: `to-prd`, `triage`, `tdd`, `enforce-compliance`.

## Fases
- **N-0** (`ready-for-agent`): `GET user-plants/my-alerts/` (scoped) +
  `GET admin/system-events/` (IsAdminUser) + tests RBAC + OpenAPI.
- **N-1** (`needs-triage`→`ready-for-agent` tras N-0): centro `Mis avisos` ambos
  roles + polling + local-notify + badge no-leídos.
- **N-2**: portal `/admin` ampliado (Dispositivos, Auditoría, Centro de fallas).
- **N-3**: cierre a11y/offline por pantalla (mapa etiquetas, reintentos, chips).
- **N-4**: ejecución de pruebas del sistema (matriz + E2E LAN en teléfono).

## Aceptación global
RBAC probado (403 cruzados), latencia evento→pantalla <60 s, 0 PII en logs,
NOM-059 intacto, suites verdes.
