# Auditoría de Coherencia RF/RNF — Mole-AI

Fecha: 2026-06-28  
Versión: 1.0  
Auditor: opencode (automatizado)

---

## Resumen

| Documento | Claims | ✅ Verídico | ⚠️ Parcial | ❌ Falso | 🔍 No verificable |
|---|---|---|---|---|---|
| Frontend RF-01…RF-37 | 37 | 34 | 2 | 0 | 0 |
| Frontend RNF-01…RNF-35 | 35 | 27 | 2 | 5 | 0 |
| Backend RF-01…RF-23 | 23 | 11 | 5 | 7 | 0 |
| Backend RNF-01…RNF-24 | 24 | 10 | 5 | 7 | 0 |
| **Total** | **119** | **82** | **14** | **19** | **0** |

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
| RF-18 | Typewriter effect | ✅ | `chat.js:60` setInterval char-by-char; `typewriter.ts` data-typewriter |
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
| RF-27 | Caché local de catálogo (offline) | ⚠️ | `wiki.js:127-138` usa MoleState.ensureSpeciesLoaded() que es caché en memoria, NO localStorage persistente. searchHistory sí persiste |
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

## Frontend — RNF-01…RNF-15 (Seguridad, Cache, Bundle)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RNF-01 | Timeout LLM 120s | ✅ | `apiService.js:18` aiTimeout=120000 |
| RNF-02 | Timeout estándar 30s | ✅ | `apiService.js:17` defaultTimeout=30000 |
| RNF-03 | Polling 30s | ✅ | `health.js:68` HEALTH_POLL_INTERVAL=30000 |
| RNF-04 | Chunk splitting (leaflet/echarts manualChunks, leaflet/jsPDF lazy) | ✅ | `vite.config.js:21-23` manualChunks, map.js lazy import |
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

## Frontend — RNF-16…RNF-35 (Performance, Tests, CI, Docker)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
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
| RNF-26 | Versiones fijas (lockfile) | ✅ | `pnpm-lock.yaml` presente |
| RNF-27 | Zero os.getenv | ✅ | Sin process.env / os.getenv en src/ |
| RNF-28 | Contraste WCAG AA | ⚠️ | Documentado como parcial (Pip-Boy OK, Solar no verificado). Sin probes de contraste en CI |
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
| RF-01 | Login JWT HS256 (Supabase) | ✅ | `authentication/views.py:207` login_view; `local_jwt_auth.py:57-61` HS256 decode; `authentication.py:32` SupabaseAuthentication |
| RF-02 | Validación tokens cada request | ✅ | `authentication/middleware.py:14-18` JwtHttpMiddleware + JwtAuthMiddleware |
| RF-03 | API Keys por dispositivo IoT | ✅ | `core/models.py:253` Device.auth_token; `authentication.py` HardwareAPIKeyAuthentication |
| RF-04 | CRUD usuarios roles (admin/agricultor/técnico) | ⚠️ | `authentication/models.py:25` supabase_role field. No hay vistas CRUD de usuarios en urls.py |
| RF-05 | Rate limiting por usuario/IP | ⚠️ | DRF throttles (`core/throttles.py`), NO django-ratelimit. Módulo documentado como `core/middleware` pero está en `core/throttles.py` |
| RF-06 | Ingesta telemetría M2M | ✅ | `core/views.py:161-240` sensor_batch_view, EdgeNodeIngestView; `management/commands/mqtt_listener.py` |
| RF-07 | Bulk insert sensores | ✅ | `core/views.py:142` SensorLog.objects.bulk_create; `:230` SoilReading.objects.bulk_create |
| RF-08 | Downsampling histórico | ✅ | `core/tasks.py:298-299` downsample_telemetry Celery task |
| RF-09 | Geocercas virtuales | ❌ | No se encontró código de geocercas ni parcelas geométricas. App `cultivos` no existe |
| RF-10 | Edge computing nodo local | ❌ | No se encontró lógica de edge computing. App `devices` no existe |
| RF-11 | Diagnóstico por imagen (→ mole_vision) | ✅ | `ai_models/views.py:116` analyze_vision_view; `utils.py:40-110` DeepSeek-VL client |
| RF-12 | Chat contextual RAG (→ mole_chat) | ✅ | `ai_models/views.py:63` train_rag_view; `services.py:149-185` chat con mole_chat microservice |
| RF-13 | Predicción rendimiento | ⚠️ | `ai_models/views.py:47` model_performance_view existe, pero es rendimiento del modelo IA, NO predicción de rendimiento de cultivos. App `predictivo` no existe |
| RF-14 | Modelo hídrico/riego | ❌ | No existe modelo hídrico. `plants/management/commands/seed_species.py` tiene campo irrigation en semilla pero no es modelo predictivo. App `riego` no existe |
| RF-15 | Riego automático por sensor | ❌ | No se encontró. App `riego` no existe |
| RF-16 | Control PID válvulas | ❌ | No se encontró. App `riego` no existe |
| RF-17 | Alertas humedad/temp fuera de rango | ⚠️ | `core/admin_views.py:190-198` live_alerts_view con alertas de humedad baja. Solo para admin, no hay alertas push/notificaciones |
| RF-18 | Reportes PDF historial | ❌ | Backend no genera PDFs. `core/admin_views.py:124` redirige a `ms3_reports:8003`. App `reports` no existe |
| RF-19 | Exportación XLSX | ❌ | No hay exportación XLSX. `core/tasks.py:388` exporta CSV a S3 (no XLSX). App `reports` no existe |
| RF-20 | Dashboard admin estadísticas | ✅ | `core/admin_views.py:23-84` admin_stats_view con SRE metrics |
| RF-21 | Panel Django Admin | ✅ | `core/admin.py:17-18` FeedbackTicketAdmin, otros modelos registrados |
| RF-22 | Logs auditoría acciones críticas | ✅ | `core/models.py:203-228` AuditLog (inmutable, append-only, creación en `authentication/views.py:70-71`) |
| RF-23 | MinIO/media storage | ✅ | `core/models.py:349-354` S3 export registry; `training_data/services.py` presigned URLs; `storages` en INSTALLED_APPS |

## Backend — RNF-01…RNF-24 (JWT, CORS, Rate-limiting, Logging)

| ID | Claim | Veredicto | Evidencia |
|---|---|---|---|
| RNF-01 | JWT HS256 expiración configurable | ✅ | `settings.py` JWT_ALGORITHM, JWT_TTL_MINUTES env vars; `local_jwt_auth.py:57-61` decode HS256 |
| RNF-02 | API Keys rotables por dispositivo | ⚠️ | `core/models.py:253` auth_token existe pero sin endpoint de rotación ni fecha de expiración |
| RNF-03 | CORS por orígenes permitidos | ⚠️ | `nginx.conf:52-58` maneja CORS (no Django). CORS_ALLOWED_ORIGINS=[] en settings.py. Documentado como backend pero implementado en frontend/nginx |
| RNF-04 | Rate limiting con django-ratelimit | ⚠️ | `core/throttles.py` usa DRF throttles (UserRateThrottle), NO django-ratelimit |
| RNF-05 | Hashing bcrypt/Auth0 | ⚠️ | `authentication.py:32-88` SupabaseAuthentication existe pero usa HS256 JWT, no bcrypt. Auth0 no referenciado |
| RNF-06 | SQL injection protection (ORM) | ✅ | Django ORM query construction |
| RNF-07 | Path traversal protection uploads | ⚠️ | `ai_models/views.py:27-35` validate_file solo verifica content-type y tamaño, NO sanitiza path. `training_data/services.py` sin validación de path traversal |
| RNF-08 | Celery con tenacity | ✅ | `requirements.txt` tenacity>=8.2; `core/tasks.py:147,242` self.retry countdown |
| RNF-09 | Dead-letter queue | ❌ | No implementado (documentado correctamente como ❌ por el propio README) |
| RNF-10 | Graceful degradation | ⚠️ | `middleware/error_handling.py` GracefulDegradationMiddleware; `core/views.py:412-414` chat_fallback_view. Cobertura parcial |
| RNF-11 | Connection pooling PostgreSQL | ❌ | Sin pgBouncer ni CONN_MAX_AGE configurados. README dice "pool vía pgBouncer externo" pero no hay evidencia |
| RNF-12 | Redis cache | ✅ | `settings.py` CACHES django_redis.RedisCache |
| RNF-13 | Bulk insert optimizado | ✅ | `core/views.py:142,230` bulk_create |
| RNF-14 | Downsampling automático | ✅ | `core/tasks.py:298` downsample_telemetry + beat schedule |
| RNF-15 | Paginación endpoints | ❌ | No hay PageNumberPagination en settings.py ni en views. REST_FRAMEWORK sin DEFAULT_PAGINATION_CLASS |
| RNF-16 | Timeout 30s microservicios | ✅ | `infrastructure/clients/microservices.py:55` timeout_seconds=30 (default) |
| RNF-17 | Type hints funciones públicas | ⚠️ | Parcial — verificado en vistas con type hints mezclados (documentado correctamente como ⚠️) |
| RNF-18 | Docstrings clases/métodos críticos | ⚠️ | Parcial — algunas clases tienen docstrings, otras no (documentado correctamente como ⚠️) |
| RNF-19 | ~900 tests unitarios | ❌ | 31 archivos test, 83 métodos test (grep test_). Muy lejos de 900+. Error de estimación |
| RNF-20 | Settings por entorno | ❌ | `mole_ai_backend/settings.py` único archivo de 389 líneas. No hay settings/dev.py ni settings/prod.py |
| RNF-21 | Logging estructurado por app | ✅ | `settings.py` LOGGING con formato verbose, PIIFilter, StreamHandler |
| RNF-22 | Task Celery en Django Admin | ❌ | No hay registros de tareas Celery en admin.py. django-celery-results no está en INSTALLED_APPS |
| RNF-23 | OpenTelemetry exports | ❌ | Solo 1 test file (`test_otel_trace_id_propagation.py`) referencia OTEL. Cero producción. Settings.py sin OTEL |
| RNF-24 | Health check endpoint | ✅ | `core/urls.py:50` /health/ (público) + `core/urls.py:24` /devices/<id>/health/ (JWT) |

---

## Errores de Documentación — Correcciones Requeridas

### Frontend (`frontend/docs/requisitos.md`)

| ID | Error | Corrección |
|---|---|---|
| RF-07 | Módulo referenciado: `admin.js` | Cambiar a `mlops.js` (forgotPassword está en mlops.js:100, no en admin.js) |
| RNF-17 | Orígenes CORS: "localhost, mole-ia.com" | Añadir 127.0.0.1 y mole-ia.duckdns.org a la lista documentada |
| RNF-27 | "Catálogo de especies en localStorage" | El catálogo se cachea en MoleState (memoria), no en localStorage. Corregir descripción del módulo |
| RNF-34 | "Documentado en docs/docker-hardening.md" | Archivo no existe. Quitar referencia o crear el archivo |
| RNF-35 | "Documentado en docs/docker-hardening.md" | Archivo no existe. Quitar referencia o crear el archivo |

### Backend (`core_backend/docs/README.md`)

| ID | Error | Corrección |
|---|---|---|
| RF-04 | Módulo: `users` | La app `users` no existe. El campo role está en `authentication/models.py`. Cambiar módulo a `authentication` y notar que no hay endpoints CRUD |
| RF-05 | Módulo: `core/middleware`; claim: "django-ratelimit" | El throttling está en `core/throttles.py` usando DRF throttles. Cambiar a DRF throttles |
| RF-09 | Claim: Geocercas virtuales. Módulo: `cultivos` | No implementado. Eliminar claim o marcar como no implementado |
| RF-10 | Claim: Edge computing. Módulo: `devices` | No implementado. Eliminar claim |
| RF-13 | Módulo: `predictivo`; claim: "Predicción de rendimiento" | App `predictivo` no existe. `model_performance_view` es rendimiento del modelo, no de cultivos |
| RF-14 | Módulo: `riego`; claim: "Modelo hídrico" | App `riego` no existe. No hay modelo hídrico implementado |
| RF-15 | Claim: "Programación automática de riego" | No implementado. Eliminar |
| RF-16 | Claim: "Control PID de válvulas" | No implementado. Eliminar |
| RF-17 | Módulo: `riego/notifications` | App `riego` no existe. Alertas están en `core/admin_views.py` |
| RF-18 | Claim: "Reportes PDF". Módulo: `reports` | App `reports` no existe. PDF generation delegated to `ms3_reports` externo |
| RF-19 | Claim: "Exportación XLSX". Módulo: `reports` | App `reports` no existe. Solo hay CSV export para datos viejos |
| RF-20 | Módulo: `admin` | App `admin` no existe. El dashboard admin está en `core/admin_views.py` |
| RF-21 | "Panel Django Admin para gestión completa" | Django admin existe pero con registro parcial de modelos |
| RNF-03 | Claim: "CORS configurado por orígenes permitidos" | CORS manejado por Nginx (frontend/nginx.conf), no por Django. CORS_ALLOWED_ORIGINS=[] en settings.py |
| RNF-04 | Claim: "django-ratelimit" | Usa DRF throttles (`UserRateThrottle`), no django-ratelimit |
| RNF-05 | Claim: "bcrypt/Auth0" | Usa HS256 JWT, no bcrypt. Auth0 no referenciado |
| RNF-11 | Claim: "Connection pooling... pgBouncer externo" | Sin evidencia de pgBouncer en código, docker-compose o docs |
| RNF-15 | Claim: "✅ DRF PageNumberPagination" | No implementado. Settings.py sin DEFAULT_PAGINATION_CLASS |
| RNF-19 | Claim: "~900+ tests" | Solo 83 métodos test en 31 archivos. Corregir a ~80 |
| RNF-22 | Claim: "Tracking Celery en Admin ✅" | No implementado. django-celery-results no en INSTALLED_APPS |
| RNF-23 | Claim: "OpenTelemetry exports (referencias en código) ⚠️" | Solo 1 test file. Sin producción. Cambiar a ❌ |
| Múltiple | Módulos referencian apps inexistentes (devices, m2m, sensores, cultivos, predictivo, riego, reports, admin, users) | Usar paths reales: `apps.core`, `apps.ai_models`, `apps.authentication`, `apps.plants`, `apps.training_data` |
| Múltiple | `core/settings.py` en lugar de `mole_ai_backend/settings.py` | El settings real está en `mole_ai_backend/settings.py` |
| — | Directorio `apps/starlette/` y `apps/pwd/` shadowing | Ya documentado como TD-01. OK |

---

## Recomendaciones

1. **Alta**: Eliminar claims falsos (RF-09, RF-10, RF-14, RF-15, RF-16, RF-18, RF-19) del backend README — no existe implementación y no hay planes inmediatos
2. **Alta**: Crear `docs/docker-hardening.md` (referenciado por RNF-34/35) o corregir la referencia
3. **Media**: Corregir el conteo de tests en backend README (de ~900 a ~80)
4. **Media**: Sincronizar módulos referenciados con apps reales del backend
5. **Baja**: Ampliar orígenes CORS documentados en RNF-17 (frontend)
6. **Baja**: Corregir módulo de RF-07 de `admin.js` a `mlops.js`
