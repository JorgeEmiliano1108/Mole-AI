# CONTEXT.md — Lenguaje de dominio Mole.AI (single-context)

Glosario canónico. Usar estos términos en issues, tests y código nuevo. Evitar sinónimos.

## Términos

- **Espécimen**: planta individual del usuario (`UserPlant`). Evitar: `planta`, `cultivo`, `matica` en código nuevo.
- **Catálogo de especies**: fichas públicas de flora (`SpeciesCatalog`). Evitar: `wiki` como nombre de módulo nuevo (legacy `wiki.js` se mantiene hasta Flutter).
- **Telemetría**: lecturas de sensores del ESP32 (`SoilReading`, `AmbientReading`). Evitar: `sensor-data` genérico en contratos nuevos.
- **Trama edge (EdgeFrame)**: contrato compacto de ingesta `{ts, ri, a:{t,h,l,u}, s:[{p,v}], dg}` (`microservices/esp32_node/main/include/edge_frame.h`). Canónico para ingesta hardware. Evitar: `batch` verbose en contratos nuevos.
- **Diagnóstico**: resultado de visión IA (`AIDiagnostic`: `diagnosis_label`, `confidence`, `metadata{species,severity,ph_predicted}`). Evitar: `identificación`, `análisis` como entidad.
- **Chat RAG**: conversación contextual vía MS-2 (`LLMRequest`), transporte interno REST o MCP (pool SSE, ADR-0011). La vía asíncrona de respaldo existe como `chat_fallback_view`/`chat_async` (Celery) para indisponibilidad de MS2; no renombrar (estabilidad de interfaces).
- **Issue tracker**: `.scratch/<feature>/` local (ver `docs/agents/issue-tracker.md`). Evitar: `backlog`.
- **Issue**: unidad de trabajo (bug, tarea, PRD, slice). Evitar: `ticket`.
- **Triage role**: `needs-triage / needs-info / ready-for-agent / ready-for-human / wontfix` (ver `docs/agents/triage-labels.md`).

## Relaciones

- Un Issue tracker contiene muchos Issues; un Issue lleva un Triage role a la vez.
- Una Trama edge es emitida por un Dispositivo (`Device`), ligada a un Espécimen vía `HardwareBinding`.
- Un Diagnóstico referencia un Espécimen y puede citar el Catálogo de especies.
- Una sesión de Chat RAG referencia un Espécimen + su Telemetría reciente.

## Directrices científicas (marco teórico del MVP)

- **Sin LLMs locales en el móvil:** la arquitectura rechaza la inferencia de LLMs en el dispositivo por limitaciones severas de memoria (RAM) y consumo energético/térmico en gamas media/baja. La carga generativa se delega al cloud (proveedor LLM OpenAI-compatible, configurable sin vendor lock-in) y el Edge opera solo visión de bajo consumo (MobileNetV2 **FP16** 4.8 MB, 38 clases, `confidenceThreshold=0.70`; INT8 descartado por contrato Dart f32 — ver `mobile/assets/models/README.md`).
- **Strict claim-level faithfulness:** el RAG se evalúa por fidelidad estricta a nivel de afirmación bajo políticas fail-closed: es alucinación tanto no abstenerse cuando el contexto no alcanza (frase exacta de la REGLA DE ORO) como cualquier afirmación no fundamentada detectada por el juez, incluso en respuestas a consultas válidas. Esto mitiga el sesgo de longitud (verbosity bias) de los jueces genéricos y mide seguridad real, no elocuencia.

## Ambigüedades resueltas

- `diagnóstico vs identificación`: canónico **Diagnóstico**.
- `sensor-data/batch vs edge-batch`: canónico **Trama edge (`sensor-data/edge-batch/`)** (ADR-0002). `sensor-data/batch/` sigue activo como alias legacy (sin header de deprecación; ver docs/system/02 RF-05) — no renombrar rutas en producción.
- `backlog`: no es término de dominio; usar **Issue tracker**.

## Deuda canónica (un ID por tema; el resto de docs referencia aquí)

- **JWT-localStorage**: JWT en `localStorage` + 2 keys (FE-DT01/VS-FE01/OWASP-A02/ETSI/RNF-08/ADR-004 frontend). Bloqueado por backend HttpOnly.
- **Sin-gate-calidad**: sin coverage/umbral/SCA/pre-commit (TD-06/08 backend, REC-CICD, ADR-005).
- **Downsampling-no-programada**: task existe, fuera de beat (RF-08/RNF-14 backend, REC-4).
- **MQTT-plano-legacy**: 1883 + `allow_anonymous` abiertos (MS-14, TD-MQTT, BR-05).
- **Sin-rotación**: RESUELTO 2026-09-14 — `auth_token_expires_at` + `rotate_token()` + `POST devices/<id>/rotate/` (migraciones `0012`/`0013`).
- **Sin-paginación**: RESUELTO 2026-09-17 — `DEFAULT_PAGINATION_CLASS=PageNumberPagination/PAGE_SIZE=50` (solo afecta `GET plants/species/`; web tolerante).
- **Consentimiento-solo-frontend**: RESUELTO 2026-09-14 — `POST auth/consent/` + `AuditLog` + `frontend/privacy.html`; APK registra consentimiento en onboarding.
- **Contrato-móvil-ausente**: RESUELTO 2026-09-17 — `docs/mobile-contract.md` + snapshot `docs/contracts/openapi.yml` (91 paths v1 + `/api/schema/`, 106 operaciones, 2026-09-17; counts re-verificados Wave D 2026-10-06) + gate CI `mobile-contract` (REC-5/S12).
- **Web-retirada**: 2026-09-21, admin = Django Admin RBAC nativo (grupo Botánico solo-view vía migración 0014; SuperAdmin = is_superuser). Cero Node/pnpm/vitest/Playwright en el repo; E2E en pytest + `integration_test` Dart.
