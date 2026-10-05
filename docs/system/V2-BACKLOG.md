# V2-BACKLOG — Deuda técnica consolidada (generado, no editar a mano)

> Generado por `scripts/build-v2-backlog.py` desde `.scratch/<tracker>/issues/`.
> Para actualizar: edita el issue en `.scratch/` y re-ejecuta el script.
> Total: 115 issues, 97 no completados.

## admin-ux-audit (10 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/admin-ux-audit/issues/01-trailing-slash-admin.md` | desconocido | — | Issue 01 — Trailing slash en endpoints admin |
| `.scratch/admin-ux-audit/issues/02-record-id-training.md` | desconocido | — | Issue 02 — Campo record_id en listados de training |
| `.scratch/admin-ux-audit/issues/03-training-permissions-admin.md` | desconocido | — | Issue 03 — Restringir listados de training a admin |
| `.scratch/admin-ux-audit/issues/04-error-retry-knowledge-audit.md` | desconocido | — | Issue 04 — Patrón unificado error + retry en Knowledge y Auditoría |
| `.scratch/admin-ux-audit/issues/05-snackbar-users-mutation.md` | desconocido | — | Issue 05 — Feedback positivo en mutaciones de Usuarios |
| `.scratch/admin-ux-audit/issues/06-a11y-admin.md` | desconocido | — | Issue 06 — Mejoras de accesibilidad en listas admin |
| `.scratch/admin-ux-audit/issues/07-openapi-delete-status.md` | desconocido | — | Issue 07 — Alinear openapi.yml DELETE users con backend |
| `.scratch/admin-ux-audit/issues/08-users-black-screen.md` | desconocido | — | Issue 08 — Pantalla negra en /admin/usuarios en dispositivo |
| `.scratch/admin-ux-audit/issues/09-consent-expired-token.md` | desconocido | — | Issue 09 — Consentimiento bloqueado con token expirado |
| `.scratch/admin-ux-audit/issues/10-audit-log-trailing-slash.md` | desconocido | — | Issue 10 — Trailing slash en GET admin/audit-log |

## anonimizacion (5 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/anonimizacion/issues/01-adr-anonimizacion.md` | ready-for-human | — | 01: B1: Redactar ADR — Esquema HMAC para datasets de entrenamiento |
| `.scratch/anonimizacion/issues/02-key-provider-strategy.md` | completed | — | 02: B2: Implementar KeyProvider y Anonymizer con HMAC-SHA256 |
| `.scratch/anonimizacion/issues/03-mirror-table-pipeline.md` | completed | — | 03: B3: Crear tabla espejo `training_dataset_anon` y pipeline de exportación |
| `.scratch/anonimizacion/issues/04-erasure-anonymize.md` | completed | — | 04: B4: Modificar `purge_user_data` para anonimizar en lugar de eliminar |
| `.scratch/anonimizacion/issues/05-sanitize-original-names.md` | ready-for-agent | — | 05: B5: Backfill controlado de `original_name` y validación final |

## deuda-fase5 (22 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/deuda-fase5/issues/01-prov-fee1-validacion.md` | ready-for-agent | P0 | Issue 01: Validación de provisioning FEE1 (ssid/pass/token requeridos) |
| `.scratch/deuda-fase5/issues/02-partitions-nvs-flag.md` | ready-for-agent | P0 | Issue 02: Alinear partitions.csv (flag `encrypted` inerte) |
| `.scratch/deuda-fase5/issues/03-tls-edge-batch.md` | ready-for-human | P0 | Issue 03: TLS real en edge-batch (CN + https) |
| `.scratch/deuda-fase5/issues/04-adr-riesgo-mqtt.md` | ready-for-human | P0-doc | Issue 04: ADR riesgo MQTT + precondiciones Fase 2 |
| `.scratch/deuda-fase5/issues/05-password-reset-correo.md` | needs-info | P0 | Issue 05: Password-reset sin salida de correo |
| `.scratch/deuda-fase5/issues/06-esp-error-check-runtime.md` | ready-for-human | P1 | Issue 06: ESP_ERROR_CHECK en rutas runtime → degradado |
| `.scratch/deuda-fase5/issues/07-store-forward-cableado.md` | ready-for-human | P0-funcional | Issue 07: Cablear Store&Forward (offline_buffer_push muerto) |
| `.scratch/deuda-fase5/issues/08-retry-backoff.md` | ready-for-human | P1 | Issue 08: Cablear retry/backoff o eliminar config muerta |
| `.scratch/deuda-fase5/issues/09-ltr390-errores-i2c.md` | ready-for-human | P1 | Issue 09: Propagar errores I2C en LTR390 |
| `.scratch/deuda-fase5/issues/10-fee2-chunking-vs-spec.md` | needs-info | P1 | Issue 10: FEE2 chunking MTU vs recorte de spec |
| `.scratch/deuda-fase5/issues/11-mock-ltr390-politica.md` | needs-info | P1 | Issue 11: Política MOCK LTR390 (bits ON con dato falso) |
| `.scratch/deuda-fase5/issues/12-ci-firmware-esp32.md` | ready-for-agent | P1 | Issue 12: Job CI para firmware ESP32 + archivar LEGACY |
| `.scratch/deuda-fase5/issues/13-ingress-lan-hsts.md` | ready-for-agent | P1 | Issue 13: Ingress LAN + HSTS/duckdns sincerado |
| `.scratch/deuda-fase5/issues/14-healthchecks.md` | ready-for-agent | P2 | Issue 14: Healthchecks + depends_on healthy |
| `.scratch/deuda-fase5/issues/15-pins-y-env.md` | ready-for-agent | P2 | Issue 15: Pinear dependencias + .env.example completo |
| `.scratch/deuda-fase5/issues/16-backend-quality-pytest.md` | ready-for-agent | P2 | Issue 16: Ampliar backend-quality/pytest + e2e con Django |
| `.scratch/deuda-fase5/issues/17-str-e-en-500.md` | ready-for-human | P1 | Issue 17: str(e) fuera de respuestas + permisos schema/mock |
| `.scratch/deuda-fase5/issues/18-adrs-faltantes.md` | ready-for-agent | P2 | Issue 18: ADRs faltantes (target, IRAM, NVS, DB_*, MQTT) |
| `.scratch/deuda-fase5/issues/19-docs-sync.md` | ready-for-agent | P2 | Issue 19: Sincronizar docs con el código |
| `.scratch/deuda-fase5/issues/20-mobile-ble-stack.md` | ready-for-agent | P1 | Issue 20: Stack BLE real en Flutter |
| `.scratch/deuda-fase5/issues/21-endurecimiento-iot-firmware-c.md` | needs-info | P2 | Issue 21: Endurecimiento IoT (firmware C) — etapa dedicada, fuera del MVP |
| `.scratch/deuda-fase5/issues/21-mobile-hardening-casts.md` | ready-for-agent | P1 | Issue 21: Hardening mobile (casts + cobertura) |

## harness-empirico (5 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/harness-empirico/issues/01-harness-protocol.md` | ready-for-human | — | 01: C1: Definir protocolo de medición y formatos de reporte |
| `.scratch/harness-empirico/issues/02-edge-latency-harness.md` | ready-for-human | — | 02: C2: Implementar harness de latencia Edge AI |
| `.scratch/harness-empirico/issues/03-battery-harness.md` | ready-for-human | — | 03: C3: Implementar harness de drenaje de batería |
| `.scratch/harness-empirico/issues/04-rag-gold-set-harness.md` | completed | — | 04: C4: Implementar harness de alucinaciones RAG con gold set |
| `.scratch/harness-empirico/issues/05-matrix-update.md` | ready-for-agent | — | 05: C5: Actualizar matriz de trazabilidad con resultados empíricos |

## hito4-trazabilidad (4 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/hito4-trazabilidad/issues/01-auditlog-append-only.md` | completed | — | 01-auditlog-append-only |
| `.scratch/hito4-trazabilidad/issues/02-vision-safety-gate.md` | completed | — | 02-vision-safety-gate |
| `.scratch/hito4-trazabilidad/issues/03-mobile-safety-block-contract.md` | completed | — | 03-mobile-safety-block-contract |
| `.scratch/hito4-trazabilidad/issues/04-cierre-auditoria.md` | completed | — | 04-cierre-auditoria |

## hito5-chat-safety (5 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/hito5-chat-safety/issues/01-safety-audit-module.md` | completed | — | 01-safety-audit-module |
| `.scratch/hito5-chat-safety/issues/02-llm-chat-safety-gate.md` | completed | — | 02-llm-chat-safety-gate |
| `.scratch/hito5-chat-safety/issues/03-chat-async-safety-gate.md` | completed | — | 03-chat-async-safety-gate |
| `.scratch/hito5-chat-safety/issues/04-mobile-chat-safety-ui.md` | completed | — | 04-mobile-chat-safety-ui |
| `.scratch/hito5-chat-safety/issues/05-cierre-auditoria.md` | completed | — | 05-cierre-auditoria |

## mcp-refactor (7 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/mcp-refactor/issues/01-adr-mcp.md` | completed | — | 01: A1: Redactar ADR-0011 — MCP como protocolo de contexto Django↔mole_chat |
| `.scratch/mcp-refactor/issues/02-mcp-server-scaffold.md` | ready-for-agent | — | 02: A2: Scaffold del servidor MCP en mole_chat (Streamable HTTP/SSE) |
| `.scratch/mcp-refactor/issues/03-mcp-tools-resources.md` | ready-for-agent | — | 03: A3: Implementar tools y resources MCP iniciales |
| `.scratch/mcp-refactor/issues/04-django-mcp-client.md` | ready-for-agent | — | 04: A4: Adaptador MCP cliente en Django (MoleAIClient) |
| `.scratch/mcp-refactor/issues/05-mcp-safety-gate.md` | ready-for-agent | — | 05: A5: Aplicar SafetyValidator a nivel de tool call y respuesta final |
| `.scratch/mcp-refactor/issues/06-mcp-parity-tests.md` | completed | — | 06: A6: Tests de paridad REST vs MCP y validación de contrato móvil |
| `.scratch/mcp-refactor/issues/07-mcp-feature-flag-flip.md` | ready-for-human | — | 07: A7: Activar MCP por defecto y deprecar rama REST interna |

## mvp-flutter (19 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/mvp-flutter/issues/00-env-generico-pg-local.md` | ready-for-agent | — | 00 — Variables genéricas + PostgreSQL local |
| `.scratch/mvp-flutter/issues/01-gobernanza-harness.md` | ready-for-agent | — | 01 — Gobernanza y harness de tests |
| `.scratch/mvp-flutter/issues/02-auth-hs256.md` | needs-triage | — | 02 — Auth unificada HS256 + TokenStore |
| `.scratch/mvp-flutter/issues/03-especies-nom059.md` | needs-triage | — | 03 — Especies y NOM-059 |
| `.scratch/mvp-flutter/issues/04-telemetria-edge.md` | needs-triage | — | 04 — Telemetría trama edge + lectura móvil |
| `.scratch/mvp-flutter/issues/05-vision.md` | needs-triage | — | 05 — Visión diagnóstica |
| `.scratch/mvp-flutter/issues/06-chat-rag.md` | needs-triage | — | 06 — Chat RAG única vía Celery |
| `.scratch/mvp-flutter/issues/07-mapa-reportes.md` | needs-triage | — | 07 — Mapa, clima y reportes |
| `.scratch/mvp-flutter/issues/08-hardening-mobile.md` | needs-triage | — | 08 — Hardening, CI y scaffold mobile/ |
| `.scratch/mvp-flutter/issues/09-retiro-huggingface.md` | ready-for-agent | — | 09 — Retiro HuggingFace (NVIDIA + OpenWeather únicos) |
| `.scratch/mvp-flutter/issues/10-seguridad-ingesta-consentimiento.md` | ready-for-agent | — | 10 — Seguridad ingesta + consentimiento (S09 parcial) |
| `.scratch/mvp-flutter/issues/11-contrato-movil-congelado.md` | ready-for-human | — | 11 — Contrato móvil congelado (snapshot OpenAPI + cliente Dart) |
| `.scratch/mvp-flutter/issues/12-coherencia-docs.md` | ready-for-agent | — | 12 — Coherencia código ↔ docs (CONTEXT, README, audit-matrix) |
| `.scratch/mvp-flutter/issues/13-stack-formal.md` | ready-for-agent | — | 13 — Stack formal MRF/MRNF + matriz de trazabilidad |
| `.scratch/mvp-flutter/issues/14-portal-publico.md` | ready-for-agent | — | 14 — Portal público + autenticación móvil |
| `.scratch/mvp-flutter/issues/15-drawer-roles-admin.md` | ready-for-agent | — | 15 — Drawer, roles y panel admin |
| `.scratch/mvp-flutter/issues/16-password-reset.md` | ready-for-agent | — | 16 — Backend portal: password-reset + usuarios admin + flora endémica |
| `.scratch/mvp-flutter/issues/17-ble-live.md` | ready-for-agent | — | 17 — BLE live telemetry (firmware + app) |
| `.scratch/mvp-flutter/issues/18-curaduria-flora.md` | ready-for-human | — | 18 — Curaduría flora endémica (bloquea portal) |

## notificaciones (5 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/notificaciones/issues/N-0-endpoints-eventos.md` | ready-for-human | P0 | Issue N-0: Endpoints my-alerts + system-events |
| `.scratch/notificaciones/issues/N-1-mis-avisos-app.md` | ready-for-human | P0 | Issue N-1: Mis avisos en app (ambos roles) |
| `.scratch/notificaciones/issues/N-2-portal-admin.md` | ready-for-human | P0 | Issue N-2: Portal admin (Dispositivos, Auditoría, Centro de fallas) |
| `.scratch/notificaciones/issues/N-3-a11y-offline.md` | ready-for-human | P1 | Issue N-3: Cierre a11y/offline por pantalla |
| `.scratch/notificaciones/issues/N-4-pruebas-sistema.md` | ready-for-human | P0 | Issue N-4: Ejecución de pruebas del sistema |

## traceabilidad (33 issues)

| Issue | Estado | Sev | Título |
|---|---|---|---|
| `.scratch/traceabilidad/issues/01-fe-flutter-framework.md` | ready-for-human | — | 01: RF-FE-01: Framework Flutter y compatibilidad Android |
| `.scratch/traceabilidad/issues/02-fe-telemetry-dashboard.md` | ready-for-agent | — | 02: RF-FE-02: Telemetría local MQTT/CoAP y dashboard interactivo |
| `.scratch/traceabilidad/issues/03-fe-camera-roi-normalization.md` | ready-for-agent | — | 03: RF-FE-03: Cámara, recorte de ROI y normalización |
| `.scratch/traceabilidad/issues/04-fe-diagnosis-progressive-disclosure.md` | ready-for-agent | — | 04: RF-FE-04: Diagnóstico visual y Progressive Disclosure |
| `.scratch/traceabilidad/issues/05-fe-mvc-pattern.md` | ready-for-agent | — | 05: RNF-FE-01: Patrón arquitectónico MVC |
| `.scratch/traceabilidad/issues/06-fe-graceful-degradation.md` | ready-for-human | — | 06: RNF-FE-02: Graceful Degradation y offline-first |
| `.scratch/traceabilidad/issues/07-fe-capture-validation.md` | ready-for-agent | — | 07: RNF-FE-03: Prevención de errores en captura de imágenes |
| `.scratch/traceabilidad/issues/08-be-django-monolith.md` | ready-for-human | — | 08: RF-BE-01: Backend principal en Django |
| `.scratch/traceabilidad/issues/09-be-jwt-profiles.md` | ready-for-human | — | 09: RF-BE-02: Autenticación JWT y gestión de perfiles/parcelas |
| `.scratch/traceabilidad/issues/10-be-offline-sync.md` | ready-for-human | — | 10: RF-BE-03: Endpoints seguros para conciliación offline |
| `.scratch/traceabilidad/issues/11-be-orm-sql-injection.md` | completed | — | 11: RNF-BE-01: ORM y protección contra inyección SQL |
| `.scratch/traceabilidad/issues/12-be-https-tls.md` | completed | — | 12: RNF-BE-02: Seguridad perimetral HTTPS/TLS |
| `.scratch/traceabilidad/issues/13-ms-web-mining.md` | ready-for-human | — | 13: RF-MS-01: Microservicio independiente de Web Mining |
| `.scratch/traceabilidad/issues/14-ms-nlp-pipeline.md` | ready-for-human | — | 14: RF-MS-02: NLP para Web Mining (stop-words, lematización, chunking) |
| `.scratch/traceabilidad/issues/15-ms-embeddings-vector-store.md` | wontfix | — | 15: RF-MS-03: Embeddings con Transformers a base de datos vectorial |
| `.scratch/traceabilidad/issues/16-ms-decoupling.md` | ready-for-human | — | 16: RNF-MS-01: Desacoplamiento ante falla de Web Mining |
| `.scratch/traceabilidad/issues/17-ms-robots-txt.md` | ready-for-human | — | 17: RNF-MS-02: Cumplimiento ético robots.txt |
| `.scratch/traceabilidad/issues/18-ai-agent-orchestrator.md` | ready-for-agent | — | 18: RF-AI-01: Arquitectura agéntica con Orquestador, Telemetría y Visión |
| `.scratch/traceabilidad/issues/19-ai-chain-of-thought.md` | ready-for-agent | — | 19: RF-AI-02: Chain-of-Thought (CoT) en el LLM |
| `.scratch/traceabilidad/issues/20-ai-mcp-protocol.md` | ready-for-agent | — | 20: RF-AI-03: Model Context Protocol (MCP) |
| `.scratch/traceabilidad/issues/21-ai-safety-validators.md` | ready-for-human | — | 21: RF-AI-04: Safety Validators toxicológicos |
| `.scratch/traceabilidad/issues/22-ai-rag-hallucination-rate.md` | ready-for-agent | — | 22: RNF-AI-01: RAG con tasa de alucinaciones <5% |
| `.scratch/traceabilidad/issues/23-ai-edge-inference-performance.md` | ready-for-agent | — | 23: RNF-AI-02: Rendimiento de inferencia local MobileNetV2 |
| `.scratch/traceabilidad/issues/24-db-sqlite-local.md` | ready-for-human | — | 24: RF-DB-01: SQLite3 local offline |
| `.scratch/traceabilidad/issues/25-db-postgresql-django.md` | ready-for-human | — | 25: RF-DB-02: PostgreSQL acoplado a Django |
| `.scratch/traceabilidad/issues/26-db-faiss-chroma.md` | wontfix | — | 26: RF-DB-03: Base de datos vectorial FAISS o Chroma |
| `.scratch/traceabilidad/issues/27-db-sqlcipher.md` | ready-for-human | — | 27: RNF-DB-01: SQLCipher AES-256 para SQLite local |
| `.scratch/traceabilidad/issues/28-db-anonymization.md` | completed | — | 28: RNF-DB-02: Anonimización en PostgreSQL para reentrenamiento |
| `.scratch/traceabilidad/issues/29-df-sensor-queue.md` | ready-for-agent | — | 29: RF-DF-01: Captura pasiva de métricas ESP32 → móvil y cola local |
| `.scratch/traceabilidad/issues/30-df-background-sync.md` | ready-for-agent | — | 30: RF-DF-02: Sincronización en segundo plano al detectar conectividad |
| `.scratch/traceabilidad/issues/31-df-crdt-conflict-resolution.md` | wontfix | — | 31: RNF-DF-01: CRDTs o marcas de tiempo vectoriales |
| `.scratch/traceabilidad/issues/32-df-transport-efficiency.md` | ready-for-agent | — | 32: RNF-DF-02: Eficiencia de transporte y latencia ≤2 s online |
| `.scratch/traceabilidad/issues/33-alcance-poc-cumplimiento.md` | needs-info | P2 | Issue 33: Alcance PoC de cumplimiento normativo (deuda explícita) |
