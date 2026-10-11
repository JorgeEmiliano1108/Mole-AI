# PRD — Auditoría de Trazabilidad RF/RNF vs. Código Real

**Feature:** `traceabilidad`  
**Fecha:** 2026-10-02  
**Auditor:** opencode (skills-main: zoom-out, enforce-compliance, grill-with-docs, to-prd, to-issues, triage)  
**Fuentes de verdad:**
- Estado ideal: matriz de 32 requisitos RF/RNF proporcionada por el usuario (6 capas).
- Estado implementado: `docs/thesis/capitulo_arquitectura_movil.md` + ADRs (`docs/adr/0008-auditoria-metodologica-v1.md` y resto).
- Evidencia ejecutable: código fuente, tests y contratos en `docs/contracts/openapi.yml`, `docs/mobile-contract.md`.

> Nota metodológica: la matriz detallada por el usuario contiene **32 requisitos**. El contexto previo mencionaba 40, pero la lista explícita suma 32 (7 FE + 5 BE + 5 MS + 6 AI + 5 DB + 4 DF). Este PRD audita esos 32.

---

## 1. Resumen ejecutivo

| Capa | Requisitos | ✅ CUMPLE | ⚠️ PARCIAL | ❌ NO IMPLEMENTADO | 🔴 Brecha normativa |
|---|---|---|---|---|---|
| 1. Frontend | 7 | 2 | 3 | 2 | 0 |
| 2. Backend | 5 | 3 | 2 | 0 | 1 (RNF-BE-02) |
| 3. Microservicios y Web Mining | 5 | 0 | 3 | 2 | 0 |
| 4. Agentes e IA | 6 | 1 | 0 | 5 | 0 |
| 5. Bases de datos | 5 | 3 | 1 | 1 | 0 |
| 6. Flujo de datos y sincronización | 4 | 0 | 3 | 1 | 0 |
| **Total** | **32** | **9** | **12** | **11** | **1** |

### Hallazgos estructurales críticos (delta matriz ↔ tesis/código)

1. **MCP → REST** (RF-AI-03): la matriz exige Model Context Protocol; ADR-0008 documenta que fue sustituido por REST + sesión Redis/Django.
2. **Web Mining fuera del MVP** (RF-MS-01, RF-MS-02, RNF-MS-02): la matriz exige un microservicio de minería web; ADR-0008 y la tesis lo excluyeron. El pipeline RAG actual funciona sobre ingest manual/S3 de PDFs.
3. **FAISS/Chroma → pgvector** (RF-DB-03, RF-MS-03): la matriz exige FAISS/Chroma; el vector store real es PostgreSQL + pgvector.
4. **CRDTs → Store-and-Forward** (RNF-DF-01): la matriz exige CRDTs o relojes vectoriales; el código implementa Store-and-Forward + cursor + deduplicación por timestamp.

### Hallazgos normativos destacados

- **Cumplen robustamente:** `SafetyValidator` + `AuditLog` inmutable (NOM-059, COFEPRIS, ISO/IEC 27001), SQLCipher AES-256 en móvil (OWASP MASVS-STORAGE, LFPDPPP), HTTPS pinning fail-closed en Flutter (MASVS-NETWORK).
- **Brecha normativa:** `SECURE_SSL_REDIRECT` por defecto `False` en Django (`core_backend/mole_ai_backend/settings.py:72`) contradice el requisito de forzar HTTPS en todos los endpoints (RNF-BE-02).
- **Riesgo LFPDPPP:** falta pipeline sistemático de anonimización de datasets de reentrenamiento en PostgreSQL (RNF-DB-02).

---

## 2. Matriz de trazabilidad detallada

### 2.1 CAPA FRONTEND

| ID | Requisito | Estado | Evidencia | Delta (matriz vs. tesis/código) |
|---|---|---|---|---|
| RF-FE-01 | Framework Flutter, multiplataforma (Android prioritario) | ✅ CUMPLE | `mobile/pubspec.yaml:31-32` declara Flutter SDK; `mobile/android/` confirma target Android; modelo TFLite empaquetado en assets. | Coincide con tesis §4.3.1. iOS/web no son prioridad MVP. |
| RF-FE-02 | Capturar telemetría local vía MQTT/CoAP desde ESP32 y mostrar dashboard humedad/temp/luz UV | ⚠️ PARCIAL | Dashboard: `mobile/lib/features/plants/plant_detail.dart:132-155`, `telemetry_badge.dart:21-37` (origen `server` vs `bleLive`). BLE FEE2: `mobile/lib/features/ble/ble_telemetry.dart:73-137`. No se encontró cliente MQTT/CoAP en la app. | El móvil no suscribe MQTT/CoAP; recibe BLE en vivo (`0xFEE2`) y servidor REST. El gateway edge (`edge_node/`) es quien recibe MQTT. Tesis §4.5.2 documenta BLE FEE2 como alternativa, no sustituto completo. |
| RF-FE-03 | Cámara, recorte de ROI y normalización previa a inferencia | ⚠️ PARCIAL | Cámara: `mobile/lib/features/vision/diagnosis_screen.dart:159-161` (`image_picker`). Normalización: `mobile/lib/features/vision/edge_ai.dart:70-86` redimensiona a 224×224 y normaliza `[-1,1]`. Tests: `mobile/test/edge_ai_test.dart:19-31`. | No existe recorte interactivo de ROI; solo guía visual estática (`diagnosis_screen.dart:387-398`, comentario “Sin segmentación en v1”). Normalización OK. |
| RF-FE-04 | Mostrar diagnóstico (mapas de calor / bounding boxes) + recomendaciones paso a paso con Progressive Disclosure | ⚠️ PARCIAL | Recomendaciones: `mobile/lib/features/vision/diagnosis_screen.dart:335-365` (especie, severidad, pH, acciones, consejo offline). Historial: `diagnosis_history.dart:84-97`. | No se renderizan heatmaps ni bounding boxes. No hay Progressive Disclosure explícito (expand/collapse por pasos). |
| RNF-FE-01 | Patrón MVC con separación estricta presentación/negocio | ❌ NO IMPLEMENTADO | La app usa Riverpod + StatefulWidget: `mobile/lib/features/auth/auth_controller.dart:58` (Notifier), `diagnosis_screen.dart:34-232` mezcla UI y lógica. Existen repositorios (`VisionRepository`, `PlantsRepository`, etc.) pero no MVC estricto. | Tesis §4.3.1 describe “provider inyectable”, no MVC. Código coincide con tesis, no con la matriz. |
| RNF-FE-02 | Graceful Degradation: UI offline con datos cacheados e inferencia local sin crash | ✅ CUMPLE | SQLCipher AES-256: `mobile/lib/core/offline_db.dart`. Cola fotos: `mobile/lib/core/offline_store.dart:122-142`. Drenaje automático: `mobile/lib/home_shell.dart:47-62`. Edge AI: `mobile/lib/features/vision/edge_ai.dart`. PVU: `mobile/lib/pvu/routing.dart:51-65`. Tests: `offline_test.dart`, `pvu_routing_test.dart`, `edge_ai_test.dart`. | Totalmente alineado con tesis §4.3.3-4.3.4, §4.4.2-4.4.3. Patrón real Store-and-Forward. |
| RNF-FE-03 | Validación en tiempo real de captura (iluminación insuficiente, etc.) | ❌ NO IMPLEMENTADO | Única medida: guía visual de encuadre (`diagnosis_screen.dart:387-398`). `preprocessJpeg` solo valida decodificación JPEG (`edge_ai.dart:72`). | No hay validación de iluminación, desenfoque u orientación. Tesis tampoco lo documenta. |

### 2.2 CAPA BACKEND

| ID | Requisito | Estado | Evidencia | Delta (matriz vs. tesis/código) |
|---|---|---|---|---|
| RF-BE-01 | Backend principal en Django como enrutador y sincronizador de telemetría | ✅ CUMPLE | Django 5.2.7: `core_backend/mole_ai_backend/settings.py:6`. Enrutador `/api/v1/`: `urls.py:44-51`. Telemetría: `core_backend/apps/core/urls.py:21-26`, `views.py:233-370` (`EdgeNodeIngestView`, `SyncBatchView`). Celery: `celery.py`. | Coincide con tesis §4.6.1 y §4.5.3. |
| RF-BE-02 | Autenticación JWT y gestión de perfiles/agricultores/parcelas | ✅ CUMPLE | JWT HS256 local: `apps/authentication/infrastructure/local_jwt_auth.py:13-115`; login `views.py:289-359`; refresh `refresh.py:19-49`. Perfil: `views.py:30-107`. Parcelas: `apps/plants/models.py:82-116`, `views.py:117-152`. Consentimientos LFPDPPP en `User`. | Coincide con tesis §4.3.2 y §4.6. Supabase deshabilitado como método canónico. |
| RF-BE-03 | Endpoints seguros para recibir/conciliar datos offline del móvil | ✅ CUMPLE | Endpoints `batch/`, `edge-batch/`, `sync/batch/`: `core_backend/apps/core/urls.py:23-26`. Implementaciones: `views.py:200-217`, `:233-275`, `:278-369`. Autenticación dispositivo: `views.py:120-148` (`DeviceBearerPermission`). | Coincide con tesis §4.3.4 (Store-and-Forward) y §4.5.3. Patrón real es Store-and-Forward, no CRDT. |
| RNF-BE-01 | ORM para acceso a BD, sin SQL directo ni riesgo de inyección | ✅ CUMPLE (con excepción documentada) | Vistas productivas vía ORM, incluido `AdminStats.objects.first()` contra la MV `admin_stats` (`core_backend/apps/core/admin_views.py:42-43`, modelo `managed=False` en `apps/core/models.py:352-365`). Resta una única sentencia SQL fija no inyectable: `REFRESH MATERIALIZED VIEW CONCURRENTLY admin_stats` en `apps/core/tasks.py:80` (sin interpolación de entrada; ver ADR-0013). | Sentencias fijas de mantenimiento quedan fuera del requisito de abstracción total; prohibido añadir `cursor.execute` con entrada de usuario. |
| RNF-BE-02 | HTTPS forzado + TLS; peticiones no autorizadas bloqueadas inmediatamente | ✅ CUMPLE | HSTS/cookies seguras: `settings.py:67-71`. `SECURE_SSL_REDIRECT` default `True` en prod (`settings.py:72-74`) con exenciones documentadas `health/` y `api/schema/` (`SECURE_REDIRECT_EXEMPT`, `settings.py:77`) — ver ADR-0014. `IsAuthenticated` global: `settings.py:207`. JWT/Hardware auth + 401: `middleware.py:127-229`, `core/views.py:120-148`. | HTTPS forzado por app en prod; el proxy solo termina TLS, ya no lo sustituye. |

### 2.3 MICROSERVICIOS Y WEB MINING

| ID | Requisito | Estado | Evidencia | Delta (matriz vs. tesis/código) |
|---|---|---|---|---|
| RF-MS-01 | Microservicio independiente de Web Mining (manuales agronómicos, NOM-037-FITO, OMRI) | ❌ NO IMPLEMENTADO | `microservices/` solo contiene `mole_chat`, `mole_report`, `mole_vision`, `esp32_node`. ADR-0008: “Web Mining fuera del MVP”. Tesis §4.2.1, §4.6.1. | Discrepancia estructural: requisito ideal vs. alcance MVP. |
| RF-MS-02 | NLP: stop-words, lematización, chunking semántico | ⚠️ PARCIAL | Chunking: `microservices/mole_chat/app/infrastructure/adapters/rag_listener.py:156-162` (`RecursiveCharacterTextSplitter`). No se encontró stop-words ni lematización. | El pipeline NLP existe para PDF subidos manualmente/S3, no para Web Mining. |
| RF-MS-03 | Embeddings con Transformers a BD vectorial | ⚠️ PARCIAL | Modelo NVIDIA `nv-embedqa-e5-v5`: `config.py:73`. Inserción pgvector: `pgvector_store.py:137-202`. Columna `embedding vector(1024)`. | Funcionalmente cumple, pero la BD vectorial es **pgvector**, no FAISS/Chroma, y la fuente no es Web Mining. |
| RNF-MS-01 | Bajo acoplamiento: si Web Mining falla, Django sigue operando | ⚠️ PARCIAL | Fallback/retries/circuit-breaker para MS1/MS2/MS3: `microservices.py:287-333`, `core/views.py:686-688`, `circuit_breaker.py:20-90`, `redis_sensor_cache_adapter.py:55-63`. | No existe Web Mining, por lo que el escenario específico no es verificable. El patrón de desacoplamiento sí está demostrado para los microservicios actuales. |
| RNF-MS-02 | Respeto a robots.txt en scraping | ❌ NO IMPLEMENTADO | No hay scrapers, crawlers ni parser de `robots.txt`. ADR-0008 confirma ausencia. | Discrepancia estructural: sin Web Mining no hay scraping. |

### 2.4 SISTEMA DE AGENTES E IA

| ID | Requisito | Estado | Evidencia | Delta (matriz vs. tesis/código) |
|---|---|---|---|---|
| RF-AI-01 | Agente Orquestador + Agente de Telemetría + Agente de Visión | ❌ NO IMPLEMENTADO | No existen clases `TelemetryAgent`, `VisionAgent`, `OrchestratorAgent`. Fusión parcial sensor→chat: `ai_models/services.py:50-89`, `mole_chat/app/application/use_cases/chat_usecase.py:69-88`. Visión aislada: `ai_models/tasks.py:60-142`. Router LangGraph solo chat: `mole_chat/app/application/orchestration/graph.py:44-127`. | Tesis no describe topología de agentes. Código es monolítico/servicios REST. |
| RF-AI-02 | Chain-of-Thought (CoT) forzado antes del diagnóstico | ❌ NO IMPLEMENTADO | Prompt agrónomo (`agronomist.yaml:1-17`) y visión (`nvidia_vision_adapter.py:23-55`) no solicitan razonamiento paso a paso. Chat genera respuesta directa. | Requisito no implementado. |
| RF-AI-03 | Model Context Protocol (MCP) para sesión/contexto dinámico | ✅ CUMPLE (flag-gated) | Servidor MCP SSE (`ping`, `get_sensor_context`, `chat`) + pool persistente Django (`mcp_pool.py`, `MCP_POOL_SIZE=3`); safety solo en host; `MCP_ENABLED` default `False` (ADR-0011 §7). REST interno como fallback. Flip condicionado a suite de paridad verde + staging (mcp/07 `ready-for-human`). | Tools `latest_readings`/`get_diagnosis_context` y recurso `session://history` quedan como trabajo futuro, no bloquean el flip. |
| RF-AI-04 | Safety Validators toxicológicos como filtro de salida | ✅ CUMPLE | `SafetyValidator`: `core_backend/apps/core/services/safety_validator.py:125-271`. Catálogos: `safety_rules.yaml`, `docs/safety/agrochemical_limits.json`, `docs/safety/nom059_species.json`. Gates post-inferencia: chat sync `views.py:651-663`, chat async `tasks.py:121-136`, visión `ai_models/tasks.py:87-104`. Audit: `safety_audit.py:18-47`. | Cumple fail-closed para NOM-059, COFEPRIS, NIST AI RMF. |
| RNF-AI-01 | RAG: tasa de alucinaciones <5% comprobable | ❌ NO IMPLEMENTADO | No hay gold set ni harness de evaluación. Mitigaciones heurísticas: anti-alucinación en prompt, router retrieval, SafetyValidator. ADR-0008 lista métricas pendientes. | Cota cuantitativa no medida ni verificable. |
| RNF-AI-02 | MobileNetV2 TFLite <850 ms y batería <4.5%/h | ❌ NO IMPLEMENTADO | Modelo TFLite: `mobile/lib/features/vision/edge_ai.dart:25`. `Stopwatch` mide latencia (`edge_ai.dart:115-127`) pero tests solo verifican `>= 0.0`. Sin medición de batería (`%`/`mAh`). | Cotas cuantitativas no validadas. |

### 2.5 BASES DE DATOS

| ID | Requisito | Estado | Evidencia | Delta (matriz vs. tesis/código) |
|---|---|---|---|---|
| RF-DB-01 | SQLite3 local para historial, imágenes en caché y telemetría offline | ✅ CUMPLE | Esquema: `mobile/lib/core/offline_db.dart:58-62` (`telemetry_cache`, `diag_queue`, `offline_advice`). Operaciones: `mobile/lib/core/offline_store.dart:90-180`. Tests: `mobile/test/offline_test.dart`. | Coincide con tesis §4.3.3-4.3.4. |
| RF-DB-02 | PostgreSQL acoplado a Django para usuarios, parcelas y reglas de negocio | ✅ CUMPLE | Configuración: `core_backend/mole_ai_backend/settings.py:147-182`. Modelos: `apps/authentication/models.py`, `apps/plants/models.py`, `apps/core/models.py`. Compose: `infrastructure/docker-compose.yml:170-172` (`pgvector/pgvector:pg16`). | Coincide con tesis §4.6.1. |
| RF-DB-03 | FAISS/Chroma para embeddings de Web Mining | ❌ NO IMPLEMENTADO | No hay FAISS/Chroma en código activo. Test skipped: `microservices/mole_report/tests/test_smoke.py:14-18`. Vector store real: pgvector (`core_backend/apps/core/models.py:17,62`; `pgvector_store.py`). ADR-0008 y tesis §4.2.1 documentan exclusión de Web Mining. | Discrepancia estructural: FAISS/Chroma vs. pgvector. |
| RNF-DB-01 | SQLite local cifrado con SQLCipher AES-256 | ✅ CUMPLE | `sqflite_sqlcipher` en `mobile/pubspec.yaml:49`. `mobile/lib/core/offline_db.dart:7-12, 47-73, 82-126`. Clave en keystore: `mobile/lib/core/offline_store.dart:20-52`. Tests: `mobile/test/s1_test.dart:22-45`. | Coincide con tesis §4.3.3. Residual documentado: JPEG en cola sin cifrado de fichero. |
| RNF-DB-02 | Anonimización en PostgreSQL para reentrenamiento (LFPDPPP) | ✅ CUMPLE (rotación pendiente) | Tabla espejo `training_dataset_anon` + `KeyProvider/EnvKeyProvider/Anonymizer` HMAC-SHA256 (`apps/training_data/anonymization.py:35-203`); task Celery `export_anonymized_dataset` (`apps/training_data/tasks.py:178-196`); `purge_user_data` anonimiza-antes-de-borrar (`apps/authentication/erasure.py:67`); campo `purged` (migración `0003`). Ver ADR-0012 (enmienda Wave D). | Pendiente post-MVP: rotación de clave con re-derivación + migración de `anonymize_id` legado + `sanitize_original_names` (anonimizacion/05). |

### 2.6 FLUJO DE DATOS Y SINCRONIZACIÓN

| ID | Requisito | Estado | Evidencia | Delta (matriz vs. tesis/código) |
|---|---|---|---|---|
| RF-DF-01 | Captar pasivamente métricas ESP32 → móvil y almacenar en cola local | ⚠️ PARCIAL | ESP32 publica FEE2: `microservices/esp32_node/main/main.c:819-830`, `fee2_frame.c:30-94`. Flutter decodifica: `mobile/lib/features/ble/ble_telemetry.dart:73-137`. Caché local: `mobile/lib/core/offline_db.dart:59` (`telemetry_cache`). Edge gateway: `edge_node/mqtt_local_subscriber.py:86-104`. | No se encontró scan/connect/subscribe a `0xFEE2` en Flutter (`gatt-fee2-spec.md:110-119` dice “sin código en esta fase”). `telemetry_cache` es caché de lectura, no cola de reenvío. |
| RF-DF-02 | Al detectar conectividad, transmitir telemetría y diagnósticos locales hacia la nube | ⚠️ PARCIAL | Móvil drena cola de fotos: `mobile/lib/home_shell.dart:46-62`, `features/vision/vision.dart:165`. Edge node store-and-forward: `edge_node/store_forward_daemon.py:440-472`, `:373-437` (JSON-RPC con cursor). | En móvil solo se sincronizan diagnósticos (fotos), no la `telemetry_cache`. No hay `WorkManager`/scheduler persistente para telemetría móvil. |
| RNF-DF-01 | CRDTs o marcas de tiempo vectoriales para resolución de conflictos | ❌ NO IMPLEMENTADO | ADR-0008: “CRDTs → Store-and-Forward”. Cero referencias a CRDT/vector_clock. Cursor `applied_up_to`: `store_forward_daemon.py:196-223`. Deduplicación por `(device_id, timestamp)`: `edge_ingest.py:24-100`. Server-wins: `core_backend/apps/core/views.py:293-294`. | Discrepancia estructural: requisito ideal vs. Store-and-Forward real. |
| RNF-DF-02 | Payloads empaquetados/comprimidos; latencia total ≤2 s online | ⚠️ PARCIAL | Empaquetado BLE binario 11-31 B: `fee2_frame.c`. JSON compacto edge: `payload_builder.c:13-72`. **Sin compresión** en transporte HTTP (no gzip/deflate/CBOR). **Sin SLO ≤2 s** medido; timeouts actuales 30-120 s. | Empaquetado OK; compresión y latencia RAG+LLM no verificadas. |

---

## 3. Discrepancias estructurales documentadas (requieren decisión humana)

| Requisito | Ideal | Implementado | Decisión pendiente |
|---|---|---|---|
| RF-AI-03 | MCP | REST + Redis/Django sesiones | RESUELTO Wave D: MCP implementado (SSE + pool, `MCP_ENABLED` default `False`); flip pendiente de paridad + staging (ADR-0011 §7, mcp/07). |
| RF-MS-01, RF-MS-02, RNF-MS-02 | Web Mining con scraping ético | Excluido del MVP; ingest manual/S3 de PDFs | ¿Incluir Web Mining en fase posterior o ajustar matriz? |
| RF-DB-03, RF-MS-03 | FAISS/Chroma | pgvector (PostgreSQL) | ¿Migrar a FAISS/Chroma o aceptar pgvector como vector store? |
| RNF-DF-01 | CRDTs / relojes vectoriales | Store-and-Forward + cursor + deduplicación por timestamp | ¿Implementar CRDTs o renombrar requisito a Store-and-Forward? |

---

## 4. Recomendaciones priorizadas

1. **Alta — Decisión arquitectónica:** resolver las 4 discrepancias estructurales actualizando la ficha metodológica/tesis (ADR-0008 ya apunta a esta dirección) **antes** de invertir en refactorizar MCP/FAISS/Web Mining/CRDTs.
2. **Alta — Seguridad perimetral (RESUELTA Wave D):** `SECURE_SSL_REDIRECT` default `True` en prod con exenciones `health/` + `api/schema/` (`settings.py:72-77`, ADR-0014). RNF-BE-02 → ✅.
3. **Alta — LFPDPPP (RESUELTA Wave D):** pipeline de anonimización implementado (espejo + HMAC + export + purga→anonimizar; ADR-0012 enmienda). Resta post-MVP: rotación de clave + `sanitize_original_names`. RNF-DB-02 → ✅ con alcance explícito.
4. **Media — Métricas empíricas:** construir harness para RAG hallucination rate, latencia edge <850 ms y drenaje de batería <4.5%/h; sin ellos los RNF cuantitativos no son comprobables.
5. **Media — Frontend funcional:** implementar recorte ROI, validación de calidad de imagen, heatmaps/bounding boxes y Progressive Disclosure si la matriz ideal prevalece.
6. **Baja — Deuda técnica:** eliminar raw SQL productivo de `admin_views.py` y `tasks.py` para alinearse estrictamente con RNF-BE-01.

---

## 5. Relación con issues generados

Cada uno de los 32 requisitos tiene un issue asociado en `.scratch/traceabilidad/issues/NN-<slug>.md`:
- **Status `ready-for-human`:** requisitos que CUMPLEN (evidencia de auditoría) y discrepancias estructurales (MCP, FAISS/Chroma, Web Mining, CRDTs).
- **Status `ready-for-agent`:** brechas código-normativa o funcionales con solución técnica clara (SSL redirect, anonimización, ROI, validación de captura, etc.).

---

## 6. Addenda 2026-10-02 — Decisiones arquitectónicas ejecutivas

Tras revisión con el arquitecto principal se resuelven las siguientes discrepancias estructurales:

1. **MCP (RF-AI-03):** Se aprueba la refactorización de Django ↔ `mole_chat` a **Model Context Protocol** (Streamable HTTP/SSE). La API pública móvil no cambia. `mole_vision` queda fuera del MVP como servidor MCP, pero el diseño debe permitir añadirlo como tool futura. Ver PRD en `.scratch/mcp-refactor/PRD.md`.
2. **pgvector (RF-DB-03 / RF-MS-03):** Se aprueba como vector store operativo. La matriz se actualizará para reflejar PostgreSQL + pgvector en lugar de FAISS/Chroma.
3. **Store-and-Forward (RNF-DF-01):** Se aprueba como estrategia de sincronización. La matriz se actualizará para reflejar Store-and-Forward + cursor + deduplicación por timestamp en lugar de CRDTs.
4. **Anonimización (RNF-DB-02):** Se aprueba esquema **HMAC-SHA256** con `ANONIMIZACION_KEY` inyectada por env var, tabla espejo `training_dataset_anon` y modificación de `purge_user_data`. Ver PRD en `.scratch/anonimizacion/PRD.md`.
5. **Benchmarks empíricos (RNF-AI-01, RNF-AI-02, RNF-DF-02):** Se aprueba harness de latencia Edge, batería (validación en gama baja) y RAG con gold set de 50 queries + LLM-as-judge. Ver PRD en `.scratch/harness-empirico/PRD.md`.

### Issues de trazabilidad actualizados

- `20-ai-mcp-protocol.md`: pasa a `ready-for-agent` (se implementará MCP).
- `26-db-faiss-chroma.md`: pasa a `wontfix` (pgvector aprobado; se actualiza matriz).
- `15-ms-embeddings-vector-store.md`: pasa a `wontfix` (pgvector aprobado; se actualiza matriz).
- `31-df-crdt-conflict-resolution.md`: pasa a `wontfix` (Store-and-Forward aprobado; se actualiza matriz).
- `12-be-https-tls.md`: permanece `ready-for-agent` (corrección de `SECURE_SSL_REDIRECT`).
- `28-db-anonimization.md`: permanece `ready-for-agent` (ahora parte de Track B).
