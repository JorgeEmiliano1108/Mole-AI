# Auditoría de Coherencia RF/RNF — Mole-AI

Fecha: 2026-09-14
Versión: 2.0 (supera a v1.0 del 2026-06-28)
Auditor: opencode + verificación por ejecución (pytest unitario, pytest MS en Docker py3.11, E2E compose, `openssl s_client`)
Metodología: cada veredicto cita `ruta:línea` verificada; lo ejecutado indica resultado real.

---

## Resumen v2

| Documento | Claims | ✅ Verídico | ⚠️ Parcial | ❌ Falso |
|---|---|---|---|---|
| Frontend RF-01…RF-37 | 37 | 34 | 3 | 0 |
| Frontend RNF-01…RNF-35 | 35 | 27 | 3 | 5 |
| Backend RF-01…RF-23 | 23 | 12 | 5 | 6 |
| Backend RNF-01…RNF-24 | 24 | 10 | 6 | 8 |
| Microservicios MS1/MS2/MS3 | 18 | 14 | 3 | 1 |
| **Total** | **137** | **97** | **20** | **20** |

Cambios vs v1.0: RF-07 backend y RNF-07 backend pasan a ✅/⚠️ (validación `safe_join` verificada en `core/views.py:267-270`); MS sube a tabla propia con datos ejecutados; counts actualizados (ver §7).

---

## Frontend — RF-01…RF-10 (Autenticación, Sesión, Provisioning)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RF-01 | Login con JWT (username+password, backend retorna JWT) | ✅ | `login.html` form POST a `auth/login/`; `apiService.js` almacena token |
| RF-02 | Registro (username, email, password, confirmación) | ✅ | `login.html` register-form con campos requeridos |
| RF-03 | Logout (limpia JWT, redirect a /login) | ✅ | `sessionManager.js:52-58` cleanupSession() + redirect |
| RF-04 | Refresh automático JWT (>15 min) | ✅ | `sessionManager.js:45` REFRESH_THRESHOLD=15*60*1000, `auth/refresh/` POST |
| RF-05 | Logout por inactividad (>20 min) | ✅ | `sessionManager.js:44` INACTIVITY_LIMIT=20*60*1000, mousedown/keydown listener |
| RF-06 | Guardia de ruta (sin token → /login) | ✅ | `main.js:78` checkAuthGuard redirige a /index.html |
| RF-07 | Recuperación de contraseña | ⚠️ | Existe en `mlops.js:100` forgotPassword(), NO en `admin.js` como documentado |
| RF-08 | KPIs en tiempo real (polling 30s) | ✅ | `health.js:68` HEALTH_POLL_INTERVAL=30000, `dashboard.html` display |
| RF-09 | Vista dual Botánico/SRE | ✅ | `health.js:2,69` toggle botones con localStorage view mode |
| RF-10 | Registro de plantas (modal) | ✅ | `crops.js:71-77` modal add-plant-modal con nombre/especie |

## Frontend — RF-11…RF-20 (Servicios: Health, Chat, Visión)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RF-11 | Health status por ESP32 | ✅ | `health.js` tabla de sensores con estado |
| RF-12 | Gráfica historial sensores | ✅ | `adminDashboard.js` chart de línea temporal |
| RF-13 | Chat LLM (NVIDIA NIM) | ✅ | `chat.js` IA_ENGINES, POST a microservicio chat |
| RF-14 | Chat con visión (subir imagen) | ✅ | `chat.js:254-285` handleChatVisionUpload con FormData |
| RF-15 | Chat estadístico | ✅ | `chat.js:242` sendChatMessage con IA_ENGINES.STATS |
| RF-16 | Historial persistido (localStorage) | ✅ | `chat.js:21-24` loadChatHistory, `:128` saveChatHistory |
| RF-17 | Nueva conversación | ✅ | `chat.js:110` clearChatHistory, nuevo sessionId |
| RF-18 | Typewriter effect | ✅ | `chat.js:60` setInterval char-by-char; `typewriter.js` (JS, no `.ts`) |
| RF-19 | Subir imagen diagnóstico | ✅ | `vision.js:47-72` file input + preview blob + formData |
| RF-20 | Resultado diagnóstico (especie, severidad, pH, confianza) | ✅ | `vision.js:13-21` renderDiagnosisRow con species/severity/ph_predicted/confidence |

## Frontend — RF-21…RF-37 (Mapa, Wiki, Admin, IoT, Privacidad)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RF-21 | Integración diagnóstico→chat | ✅ | `chat.js:254` chat-vision-input envía diagnosis al contexto |
| RF-22 | Mapa Leaflet + CartoDB dark | ✅ | `map.js:2` import L from leaflet, tiles CartoDB |
| RF-23 | Capa meteorológica | ✅ | `map.js:57-61` weather/tile layers (temp, precip) |
| RF-24 | Focos de plaga (hotspots) | ✅ | `map.js:66,188` layers.plagas con fetch a map/hotspots/ |
| RF-25 | Catálogo especies (grilla) | ✅ | `wiki.js:117-130` wiki-grid con imágenes y nombres |
| RF-26 | Búsqueda de especies | ✅ | `wiki.js:86-105` searchInput con historial y filtro |
| RF-27 | Caché local de catálogo (offline) | ⚠️ | `wiki.js:127-138` usa MoleState en memoria, NO localStorage persistente. searchHistory sí persiste. Docs corregidos 2026-09-14 a "memoria" |
| RF-28 | Dashboard KPIs globales | ✅ | `admin.js:52-57` data-card con plantas/alertas/online/nodos |
| RF-29 | Flota IoT (ESP32 radar chart) | ✅ | `admin.js:309` chart-radar-health + grid nodos |
| RF-30 | MLOps (curvas entrenamiento) | ✅ | `admin.js:337-378` ECharts training chart + init training |
| RF-31 | Centro de alertas | ✅ | `admin.js:95-96` alerts data, acknowledge/delete |
| RF-32 | Exportar TXT | ✅ | `adminDashboard.js:123-153` Blob downloadAdminReport |
| RF-33 | Escaneo Bluetooth BLE | ✅ | `iot.js:91-100` navigator.bluetooth requestDevice |
| RF-34 | Provisioning WiFi (SSID/password) | ✅ | `iot.js:142-164` provisionViaBle con CHAR_SSID_UUID |
| RF-35 | Hardware bindings CRUD | ✅ | `bindings.js:24-48` renderBindingRow + binding:delete action |
| RF-36 | Aviso privacidad LFPDPPP | ✅ | `privacy.js:23-34` privacy-banner-lfpdppp con texto legal |
| RF-37 | Consentimiento persistente | ✅ | `privacy.js:14` localStorage.getItem('consent_lfpdppp'), `:55` setItem |

## Frontend — RNF-01…RNF-35 (Seguridad, Cache, Bundle)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RNF-01 | Timeout LLM 120s | ✅ | `apiService.js:18` aiTimeout=120000 |
| RNF-02 | Timeout estándar 30s | ✅ | `apiService.js:17` defaultTimeout=30000 |
| RNF-03 | Polling 30s | ✅ | `health.js:68` HEALTH_POLL_INTERVAL=30000 |
| RNF-04 | Chunk splitting (leaflet/echarts manualChunks) | ✅ | `vite.config.js:21-23` manualChunks (chart.js dynamic, jsPDF estático — docs corregidos) |
| RNF-05 | Bundle <500KB gzip | ✅ | `scripts/check-bundle.sh` PASS: apiService 101KB, leaflet 144KB |
| RNF-06 | Cache immutable 1 año | ✅ | `nginx.conf:103` "public, immutable" en /assets/ |
| RNF-07 | HTML no cacheable | ✅ | `nginx.conf:93` "no-cache, no-store, must-revalidate" en *.html |
| RNF-08 | JWT en localStorage | ❌ | `config.js:12-17` getItem/setItem mole_jwt/moleia_token — documentado correctamente como ❌ |
| RNF-09 | Anti-XSS (0 innerHTML + DOMPurify) | ✅ | `dom.js:117` safeHTML lazy import; 0 innerHTML en src/js/modules/ |
| RNF-10 | CSP header (script-src 'self') | ✅ | `nginx.conf:39-40` CSP con script-src 'self' |
| RNF-11 | HSTS | ❌ | `nginx.conf:234-235` Comentado (# HSTS...). Documentado correctamente como ❌ |
| RNF-12 | server_tokens off | ✅ | `nginx.conf:30` |
| RNF-13 | X-Content-Type-Options: nosniff | ✅ | `nginx.conf:32` |
| RNF-14 | X-Frame-Options: DENY | ✅ | `nginx.conf:33` |
| RNF-15 | Auth header no logueado | ✅ | `nginx.conf` log format sin $http_authorization |
| RNF-16 | JWT refresh (<15 min edad) | ✅ | `sessionManager.js:45,99-102` |
| RNF-17 | CORS restringido (localhost, mole-ia.com) | ⚠️ | `nginx.conf:52-58` También permite 127.0.0.1 y mole-ia.duckdns.org (no documentados) |
| RNF-18 | Retry exponencial (1s→2s→4s) | ✅ | `apiService.js:437` delay*Math.pow(2, attempt) |
| RNF-19 | AbortController por request | ✅ | `apiService.js:381-382` controller.abort() en timer |
| RNF-20 | Errores HTTP en español | ✅ | `apiService.js:267-268` 429→"Demasiadas solicitudes", 401→"Sesión expirada" |
| RNF-21 | Fallback offline (catálogo en localStorage) | ⚠️ | `wiki.js` usa MoleState en memoria, NO localStorage persistente para especies. searchHistory en localStorage pero no es catálogo |
| RNF-22 | BFCache guard | ✅ | `main.js:131-134` pageshow + event.persisted |
| RNF-23 | Módulos ES6 | ✅ | `src/js/modules/` imports/exports |
| RNF-24 | Dead code zero | ✅ | Solo apiService.js + dashboard-*.js en static/js/ |
| RNF-25 | 30 tests (Vitest + jsdom) | ✅ | `dom.test.js` (24) + `sessionManager.test.js` (6) = 30 |
| RNF-26 | Versiones fijas (lockfile) | ✅ | `pnpm-lock.yaml` presente (`package.json` usa rangos `^`, no pins) |
| RNF-27 | Zero os.getenv | ✅ | Sin process.env / os.getenv en src/ |
| RNF-28 | Contraste WCAG AA | ⚠️ | Pip-Boy OK, Solar no verificado. Sin probes de contraste en CI |
| RNF-29 | Navegación por teclado | ❌ | Sin focus trap, sin skip links, sin Tab management en modales |
| RNF-30 | ARIA landmarks | ❌ | Sin role/aria-label en regiones principales |
| RNF-31 | Docker multi-stage | ✅ | `Dockerfile:6,29` node:22-alpine builder → nginx:1.25-alpine runtime |
| RNF-32 | USER nginx | ✅ | `Dockerfile:45` |
| RNF-33 | HEALTHCHECK | ✅ | `Dockerfile:50` wget cada 30s |
| RNF-34 | Read-only rootfs | ❌ | `docs/docker-hardening.md` NO EXISTE — documentado como existente pero el archivo no está |
| RNF-35 | Capabilities mínimas | ❌ | `docs/docker-hardening.md` NO EXISTE — idem |

---

## Backend — RF-01…RF-23 (Endpoints, Auth, Modelos)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RF-01 | Login JWT HS256 (Supabase) | ✅ | `authentication/views.py:207` login_view local HS256; `local_jwt_auth.py:57-61` decode; Supabase solo validación opcional |
| RF-02 | Validación tokens cada request | ✅ | `authentication/middleware.py:14-18` JwtHttpMiddleware + JwtAuthMiddleware |
| RF-03 | API Keys por dispositivo IoT | ✅ | `core/models.py:253` Device.auth_token; `authentication.py` HardwareAPIKeyAuthentication |
| RF-04 | CRUD usuarios roles (admin/agricultor/técnico) | ⚠️ | `authentication/models.py:25` supabase_role field. Solo alta vía `admin/users/create/`; sin CRUD completo |
| RF-05 | Rate limiting por usuario/IP | ⚠️ | DRF throttles (`core/throttles.py`), NO django-ratelimit. `DiagnosticsThrottle` importado sin aplicar (`views.py:53`) |
| RF-06 | Ingesta telemetría M2M | ✅ | `core/views.py:161-240` sensor_batch_view, EdgeNodeIngestView; `management/commands/mqtt_listener.py` (TLS 8883 verificado 2026-09) |
| RF-07 | Bulk insert sensores | ✅ | `core/views.py:142` SensorLog.objects.bulk_create; `:230` SoilReading.objects.bulk_create |
| RF-08 | Downsampling histórico | ⚠️ | `core/tasks.py:298-299` task existe pero **fuera** de `CELERY_BEAT_SCHEDULE` (corregido en docs 2026-09-14) |
| RF-09 | Geocercas virtuales | ❌ | No hay código de geocercas. App `cultivos` no existe |
| RF-10 | Edge computing nodo local | ❌ | Lo hace `edge_node/` fuera de Django. App `devices` no existe |
| RF-11 | Diagnóstico por imagen (→ mole_vision) | ✅ | `ai_models/views.py:116` analyze_vision_view; `utils.py:40-110` DeepSeek-VL client |
| RF-12 | Chat contextual RAG (→ mole_chat) | ✅ | `ai_models/views.py:63` train_rag_view; `services.py:149-185` chat con mole_chat microservice |
| RF-13 | Predicción rendimiento | ⚠️ | `ai_models/views.py:47` model_performance_view = rendimiento del modelo IA, NO de cultivos. App `predictivo` no existe |
| RF-14 | Modelo hídrico/riego | ❌ | No existe. App `riego` no existe |
| RF-15 | Riego automático por sensor | ❌ | No existe. App `riego` no existe |
| RF-16 | Control PID válvulas | ❌ | No existe. App `riego` no existe |
| RF-17 | Alertas humedad/temp fuera de rango | ⚠️ | `core/admin_views.py:190-198` live_alerts_view solo admin, sin push |
| RF-18 | Reportes PDF historial | ⚠️ | Delegado a MS3 externo (`admin_views.py:124`); ADEMÁS core genera PDFs de diagnósticos (`tasks.py:151`, `services/pdf_generator.py` ReportLab) |
| RF-19 | Exportación XLSX | ❌ | Solo CSV (`tasks.py:388` a S3). App `reports` no existe |
| RF-20 | Dashboard admin estadísticas | ✅ | `core/admin_views.py:23-84` admin_stats_view con SRE metrics |
| RF-21 | Panel Django Admin | ⚠️ | Existe con registro parcial de modelos |
| RF-22 | Logs auditoría acciones críticas | ✅ | `core/models.py:203-228` AuditLog inmutable (creación en `authentication/views.py:70-71`) |
| RF-23 | MinIO/media storage | ✅ | S3-compatible (`settings.py:258-276`); presigned URLs en `training_data/services.py` |

## Backend — RNF-01…RNF-24 (JWT, CORS, Rate-limiting, Logging)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RNF-01 | JWT HS256 expiración configurable | ✅ | `settings.py` JWT_ALGORITHM, JWT_TTL_MINUTES env vars; `local_jwt_auth.py:57-61` decode HS256 |
| RNF-02 | API Keys rotables por dispositivo | ⚠️ | `auth_token` existe + `DELETE devices/<id>/revoke/` (soft-delete); sin rotación ni expiración |
| RNF-03 | CORS por orígenes permitidos | ⚠️ | Nginx lo sirve (`nginx.conf:52-58`); `CORS_ALLOWED_ORIGINS=[]` en settings.py (correcto por diseño) |
| RNF-04 | Rate limiting con django-ratelimit | ⚠️ | `core/throttles.py` DRF throttles (UserRateThrottle), NO django-ratelimit |
| RNF-05 | Hashing bcrypt/Auth0 | ⚠️ | Argon2/PBKDF2 (`settings.py:181-184`); HS256 JWT; Auth0 no referenciado |
| RNF-06 | SQL injection protection (ORM) | ✅ | Django ORM query construction |
| RNF-07 | Path traversal protection uploads | ⚠️ | `ai_models/views.py:27-35` validate_file solo tipo+tamaño; PERO `core/views.py:267-270` sí usa `safe_join` |
| RNF-08 | Celery con tenacity | ✅ | `requirements.txt` tenacity>=8.2; `core/tasks.py:147,242` self.retry countdown |
| RNF-09 | Dead-letter queue | ❌ | No implementado |
| RNF-10 | Graceful degradation | ⚠️ | `middleware/error_handling.py` + `chat_fallback_view`. Cobertura parcial |
| RNF-11 | Connection pooling PostgreSQL | ❌ | Solo `CONN_MAX_AGE=600`; sin pgBouncer ni pool dedicado |
| RNF-12 | Redis cache | ✅ | `settings.py` CACHES django_redis.RedisCache |
| RNF-13 | Bulk insert optimizado | ✅ | `core/views.py:142,230` bulk_create |
| RNF-14 | Downsampling automático | ❌ | Task existe, NO programada (ver RF-08) |
| RNF-15 | Paginación endpoints | ❌ | Sin PageNumberPagination en settings.py ni en views |
| RNF-16 | Timeout 30s microservicios | ⚠️ | Default 30 (`microservices.py:55`); 60 en factory IA y `llm_chat_view`; 120 `MOLE_AI_TIMEOUT` |
| RNF-17 | Type hints funciones públicas | ⚠️ | Mixto; sin medición |
| RNF-18 | Docstrings clases/métodos críticos | ⚠️ | Mixto; sin medición |
| RNF-19 | Tests unitarios | ⚠️ | **32 ficheros / 81 funciones** (contado 2026-09-14), no ~900. `pytest.ini` con ignores documentados |
| RNF-20 | Settings por entorno | ❌ | `mole_ai_backend/settings.py` único, 427 líneas |
| RNF-21 | Logging estructurado por app | ⚠️ | LOGGING + PIIFilter solo en `authentication`/`plants`/`django` |
| RNF-22 | Task Celery en Django Admin | ❌ | `django-celery-results` no en INSTALLED_APPS |
| RNF-23 | OpenTelemetry exports | ❌ | Solo 1 test ignorado; cero producción |
| RNF-24 | Health check endpoint | ✅ | `core/urls.py:50` /health/ + `core/urls.py:24` devices health |

---

## Microservicios — MS-01…MS-18 (verificado por ejecución 2026-09-14)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| MS-01 | MS2 chat: `POST /api/v1/mole-ai/chat`, ingest-pdf, health | ✅ | `mole_chat/app/api/routers.py:44,100,168,183`; E2E chat+disclaimer verde en compose |
| MS-02 | MS2: 122 funciones, 115 passed + 10 skipped | ✅ | Ejecutado en Docker py3.11 2026-09-14 |
| MS-03 | MS2: JWKS ES256 + fallback HS256, PII, circuit-breaker | ✅ | `security.py:66-117`, `pii_sanitizer.py`, `circuit_breaker.py` |
| MS-04 | MS2: `X-API-KEY` obligatorio | ⚠️ | `dependencies.py:15-24` con bypass si `API_KEY` vacío; cableado a `EDGE_API_KEY` 2026-09 |
| MS-05 | MS1 visión: `POST /api/v1/vision/analyze/`, health/healthz, NOM-059 403 | ✅ | `mole_vision/app/api/routers.py:48,122,128`, `nom059.py`; 51 tests passed ejecutados |
| MS-06 | MS1: rate limit 5/min, EXIF strip, 10MiB | ✅ | `routers.py:49`, `dependencies.py:30-46,142` |
| MS-07 | MS1: `SupabaseDiagnosticRepository` persiste | ❌ | Stub: retorna UUID sin persistir (`supabase_adapter.py:32-55`) |
| MS-08 | MS3 reportes: generate/status/download, COFEPRIS, presigned 24h | ✅ | `app/api/v1/reports.py`, `generate_report_use_case.py:73-102`; 26 passed + 6 failed pre-existentes en `test_api_reports` |
| MS-09 | MS3: `ms3_*` env + JWT HS256 | ✅ | `app/config.py:6-30`; `from_env()` con genéricos (`DB_URL`, `LLM_*`, `IDP_*`) desde 2026-09 |
| MS-10 | ESP32: IDF 5.x, BLE 0xFEE0, LTR390 0x53, DHT20 0x38, trama edge 512B | ✅ | `ble_provisioning.c:36`, `mole_config.h:25-26`, `payload_builder.c:61-63`, `transport_layer.c` POST edge-batch |
| MS-11 | ESP32: FSM/estados documentados | ⚠️ | `state_machine.h` 13 estados vs "12" en README de esp32 |
| MS-12 | Edge: Store&Forward SQLite + M2M + batch 200 | ✅ | `store_forward_daemon.py:174-296`; `EDGE_SYNC_URL` → edge-batch desde 2026-09 |
| MS-13 | MQTT TLS 8883 operativo local | ✅ | Broker 2.1.2 con CA Mole.AI (SAN mqtt_broker/localhost); `openssl s_client` return 0; `test_8883_with_tls_should_succeed` PASSED |
| MS-14 | MQTT 1883 plano cerrado | ❌ | Abierto legacy para flota ESP32 (tests RED 1 y 3 pendientes a propósito; cierre fase 2) |
| MS-15 | E2E sistema: jwt + nom059 + chat | ✅ | `tests/system/*.sh` verdes 2026-09-14 (CI `.github/workflows/system-tests.yml`) |
| MS-16 | `docker-compose.e2e.yml` incluye Django | ❌ | Django excluido por `ModuleNotFoundError` histórico; fix aplicado (`models.py` import defensivo) pero no reintegrado al compose |
| MS-17 | Vars genéricas `DB_*/LLM_*/IDP_*/EDGE_*` con fallback legacy | ✅ | `settings.py:_env_first`, `AliasChoices` chat/visión, `from_env()` report, daemon `_env_first`; `tests/test_settings_env_generic.py` 9/9 |
| MS-18 | `.env` único + template público | ✅ | `.env` genérico + `.env.production.template` sin secretos; `ca.crt` trackeada (pública), `server.key` ignorada |

---

## Deltas v1.0 → v2.0 (qué cambió y por qué)

1. Counts: backend `~900` → **32/81**; chat `113` → **122 funciones**; visión 51; report 34.
2. Seguridad MQTT: 8883 TLS verificado operativo (nuevo MS-13); 1883 abierto documentado como riesgo aceptado (MS-14).
3. Configuración: `.env` único genérico + PG local (MS-17/MS-18); `ALLOWED_HOSTS` vs `DJANGO_ALLOWED_HOSTS` corregido.
4. Harness: baseline HEAD ejecutaba **0 tests** (crash setup); rama actual 55+ ejecutables en backend.
5. Docs corregidas 2026-09-14: README raíz, backend README+requisitos, frontend README+requisitos (§7 rutas reales), system 02/04/06, gate `check-docs-consistency.sh` en CI (`.github/workflows/system-tests.yml:docs-consistency`).
6. Pendientes que siguen ❌: riego/PID/geocercas/XLSX/paginación/beat-downsampling/OTEL/results/pgBouncer/JWKS/rotación/BLE-seguridad (`SECURITY_0`)/`allow_anonymous`/verify-email-frontend/mapa-offline.

---

## Recomendaciones (priorizadas)

1. **Alta**: `HardwareOnlyPermission` en `EdgeNodeIngestView` (sigue `AllowAny`) + throttles faltantes (S09).
2. **Alta**: rotar password RDS viva en `.env.bak` y borrar el backup (el `.env` actual ya es local).
3. **Alta**: reincorporar Django al `docker-compose.e2e.yml` (MS-16) ahora que el import es defensivo.
4. **Media**: programar `downsample_telemetry` en beat o reclasificar RF-08 a ❌.
5. **Media**: `mobile-contract.md` + snapshot OpenAPI (S12) antes de cualquier Dart.
6. **Baja**: alinear counts ESP32 (12 vs 13) y `requirements` de chat (`pytest-mock` presente vs "0% MagicMock").

---

## Adenda 2026-09-17 — Móvil 100% (Fases A–G, verificado por ejecución)

1. **Recomendación 5 CERRADA**: `docs/mobile-contract.md` + snapshot `docs/contracts/openapi.yml`
   (76 paths v1 + `/api/schema/`) + gate CI `mobile-contract` (job en
   `.github/workflows/system-tests.yml`, script `scripts/check-mobile-contract.sh`;
   verificado GREEN en reposo, RED ante cambio, GREEN tras protocolo).
2. **Paginación (pendiente v2.0) CERRADA**: `DEFAULT_PAGINATION_CLASS=PageNumberPagination`
   + `PAGE_SIZE=50` (`settings.py:204-209`); única vista afectada `GET plants/species/`
   (web tolerante `main.js:46`); test `tests/test_mobile_contract_fase1.py` (3 passed).
3. **MS3 reparado**: el router no tenía prefijo y ambos nginx + el proxy Django
   (`admin_views.py:124-146`) llaman `/api/v1/reports/*` → 404. Prefijo
   `prefix="/api/v1/reports"` (`mole_report/app/main.py:41`) + tests alineados
   (`test_api_reports.py` usa `P="/api/v1/reports"`). El APK consume MS3 por el
   mismo gateway (rutas exactas sin `/`, escape `enforceSlash:false` documentado).
4. **Correcciones de veredicto**: `GET map/hotspots/` es `IsAuthenticated`
   (`core/views.py:401-402`, no `AllowAny`); `Species` 22 campos (no 20);
   `GET /api/v1/health/` ahora `AllowAny` explícito (ping pre-login móvil);
   `favorites/` reordenado antes de `<uuid>/` (`urls_user.py:22-27`).
5. **APK**: `mobile/` Flutter 3.44 (Dio+Riverpod+secure_storage+image_picker+
   flutter_map+url_launcher+connectivity_plus+path_provider):
   `flutter analyze` 0 issues, `flutter test` 39 passed, `app-release.apk` 53.9MB
   firmado release (`apksigner verify` OK, SHA-256 `fd3f2b0b…a7574e`).
   Offline real: caché TTL (especies/colección/telemetría) + cola de fotos con
   auto-subida al recuperar red. Backend verificado sobre HTTP real
   (health/login/JWT/colección/búsqueda). Suite Django: 64 passed.
6. **Sigue abierto (usuario/infra)**: rotación RDS + borrar `.env.bak`; cierre 1883
   (fase 2 firmware); staging `mole-ia.duckdns.org` inalcanzable al 2026-09-17
   (deploy pendiente); respaldar `/home/paul/.mole-android/` + `key.properties`;
   rebuild APK con URL real para prueba en teléfono; MS-16; tests Redis/PG-down.

---

## Adenda 2026-09-21 — Retiro web + Django Admin RBAC (pivot V2, RNF03)

1. **Purgado**: `frontend/` íntegro + `scripts/run-e2e.sh` + `scripts/sanitize.{js,py}`
   eliminados (cero Node/pnpm/vitest/Playwright en el repo). `privacy.html`
   rescatada a `core_backend/templates/privacy.html` + ruta pública `/privacy/`.
2. **Compose sin build Node**: servicio `frontend` → imagen `nginx:1.25-alpine`
   con `infrastructure/nginx/nginx.conf` montado; `location /` → 302 `/admin/`;
   bloque `/static/` legacy eliminado (admin estáticos vía proxy Django).
3. **RBAC**: registros admin (`AIDiagnostic`, `Device`, `AmbientReading`,
   `SoilReading`, `SensorLog`, `LLMRequest` readonly, `AuditLog` append-only sin
   add/delete) + migración `0014` grupo **Botánico** (6 view-perms exactos) +
   helper idempotente `apps/core/services/rbac.py`. SuperAdmin = is_superuser.
4. **E2E nativo**: `test_auth_flow_e2e.py` (JWT completo + ARCO) en pytest;
   `mobile/integration_test/auth_flow_test.dart` (repos reales, teardown ARCO).
   Issues 01-08/PRD/CONTEXT reescritos al paradigma Python/Dart; job CI
   `docs-consistency` retirado (su objeto — docs web — ya no existe).
5. **Hallazgo ambiental**: Django 4.2 no renderiza templates en Python 3.14
   (`Context.__copy__`; verificado OK en 3.12 de CI/compose) → tests de render
   admin con `skipif`, permisos validados sin render en local.
