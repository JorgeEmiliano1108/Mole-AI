# ESPECIFICACIÓN DE REQUISITOS: Mole.AI

**Versión del Documento:** 1.0
**Fecha:** 2026-04-16
**Origen:** Auditoría Forense del Código Fuente

---

## 1. Requisitos Funcionales (RF)

### 1.1 Gestión de Usuarios y Autenticación

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-01 | Registro de usuarios | El sistema permite registrar nuevos usuarios con username y password | `main.js:submitRegistration()` |
| RF-02 | Inicio de sesión | El sistema autentica usuarios y emite tokens JWT via Supabase | `main.js:attemptLogin()`, `authentication.py` |
| RF-03 | Cierre de sesión | El sistema cierra la sesión del usuario, purga tokens y detiene procesos en background | `main.js:logout()` |
| RF-04 | Roles de usuario | El sistema diferencia entre usuarios normales y administradores (`admin`) | `main.js:executeLoginSequence()` |
| RF-05 | Superusuario local | Existe usuario especial `EmiMole` con acceso de emergencia via HS256 fallback | `authentication.py:157-164` |

### 1.2 Gestión de Plantas y Cultivos

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-06 | Catálogo de especies | El sistema almacena información de especies de plantas (nombre científico, común, rangos ideales de humedad, temperatura, pH) | `apps/plants/models.py:SpeciesCatalog` |
| RF-07 | Registro de plantas de usuario | Los usuarios pueden asociar plantas con especies del catálogo | `apps/plants/models.py:UserPlant` |
| RF-08 | Vinculación ESP32 | Cada `UserPlant` genera un UUID que se configura en el ESP32 para telemetría | `apps/plants/models.py:48` |
| RF-09 | Búsqueda de flora mexicana | Los usuarios pueden buscar especímenes botánicos con debounce de 300ms | `main.js:loadFloraSearch()` |
| RF-10 | Wizard IoT | El sistema guía al usuario para vincular hardware ESP32 | `main.js:nextIotStep()` |

### 1.3 Telemetría IoT

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-11 | Ingesta de telemetría individual | ESP32 envía lecturas de sensores (soil_humidity, air_temperature, uv_index, light_level, air_humidity) a `/api/v1/sensor-data/` | `apps/core/views.py:sensor_data_view` |
| RF-12 | Ingesta de lotes | El daemon Store-and-Forward envía lotes de hasta 500 lecturas offline | `apps/core/views.py:sensor_batch_view`, `serializers.py:120-124` |
| RF-13 | Protección Anti-Replay | Se rechazan lecturas con timestamp > 300s de desfase (ETSI EN 303 645) | `apps/core/views.py:82-87`, `serializers.py:43-69` |
| RF-14 | Actualización de pH inferido | MS1 puede actualizar `SensorLog.ph_level` via PATCH authenticated | `apps/core/views.py:sensor_data_patch_view` |
| RF-15 | Consulta de telemetría | Dashboard consulta última lectura por plant_id con validación de propiedad | `apps/core/api_views.py:telemetry_latest_view` |
| RF-16 | Visualización en dashboard | Frontend muestra datos de sensores en tiempo real | `main.js:resetDashboard()` |

### 1.4 Diagnóstico por Inteligencia Artificial

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-17 | Diagnóstico por imagen | El sistema analiza imágenes de plantas para detectar enfermedades y condiciones | `apps/ai_models/utils.py:consultar_phi_vision()`, `08_diagnostico_ia.js` |
| RF-18 | Validación OWASP de imágenes | Se validan magic bytes de imágenes para prevenir executables camuflados | `serializers.py:155-167` |
| RF-19 | Análisis pH por tira reactiva | MS1 puede estimar pH usando colorimetría RGB euclidiana | `ms1_vision/app/routes.py:analyze_ph_strip` |
| RF-20 | Historial de diagnósticos | El sistema guarda y permite consultar diagnósticos por usuario | `apps/core/views.py:diagnostic_history_view` |
| RF-21 | Descarga de PDF de diagnóstico | El usuario puede descargar un PDF con detalles del diagnóstico | `apps/core/views.py:download_diagnostic_pdf` |

### 1.5 Chat Asistentes Agronómicos (RAG + CAG)

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-22 | Chat con contexto de sensores | El chat recibe telemetría actual de Redis (CAG) como contexto | `ms2_rag_cag_service/application/chat_usecase.py:62` |
| RF-23 | Retrieval Augmented Generation | El chat busca en base de conocimiento FAISS (RAG) | `ms2_rag_cag_service/application/chat_usecase.py:63` |
| RF-24 | Fallback a Trefle.io | Si RAG local falla, se consulta API externa de botánica | `ms2_rag_cag_service/application/chat_usecase.py:70` |
| RF-25 | Disclaimer obligatorio | Toda respuesta de IA incluye disclaimer legal COFEPRIS | `ms2_rag_cag_service/domain/models.py`, `apiService.js:177-181` |
| RF-26 | Prevención de alucinaciones | El LLM está configurado para no inventar información si no hay contexto suficiente | `ms2_rag_cag_service/application/chat_usecase.py:28-34` |
| RF-27 | Historial de chat | El sistema guarda el historial de conversación en localStorage | `03_asistente_botanico.js:loadChatHistory()` |
| RF-28 | Tres motores de IA | El sistema soporta 3 motores: Chat (conversacional), Vision (diagnóstico por foto), Stats (análisis de gráficas) | `03_asistente_botanico.js:IA_ENGINES` |

### 1.6 Geolocalización y Mapas

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-29 | Hotspots de enfermedades | El sistema muestra mapa de calor con hotspots de enfermedades | `apps/core/views.py:map_hotspots_view` |
| RF-30 | Diagnósticos geolocalizados | Los usuarios pueden crear diagnósticos asociados a coordenadas GPS | `apps/core/views.py:diagnosticos_geolocalizados_create` |

### 1.7 Reportes y Exportación

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-31 | Generación de reportes consolidados | MS3 genera reportes PDF de hasta 90 días de datos de sensores | `ms3_reports/app/api/v1/reports.py:GenerateRequest` |
| RF-32 | Generación asíncrona con Celery | Los reportes se generan en background para no bloquear requests | `ms3_reports/app/api/v1/reports.py:26` |
| RF-33 | Descarga de reportes | El usuario puede consultar estado y descargar PDF generado | `ms3_reports/app/api/v1/reports.py:38` |
| RF-34 | Almacenamiento en S3/MinIO | Los PDFs se almacenan en object storage compatible S3 | `docker-compose.yml:186-197` |

### 1.8 Sistema de Feedback

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-35 | Tickets de feedback | Los usuarios pueden reportar bugs, sugerencias, errores de IA | `apps/core/views.py:feedback_create_view` |
| RF-36 | Categorización de tickets | Los tickets tienen topics: bug, suggestion, ai_error, other | `apps/core/models.py:140-151` |

### 1.9 Auditoría y Compliance

| ID | Requisito | Descripción | Fuente |
|----|-----------|-------------|--------|
| RF-37 | Logs de auditoría inmutables | El sistema registra acciones críticas en `AuditLog` que no se pueden modificar ni eliminar | `apps/core/models.py:182-207` |
| RF-38 | Trazabilidad de requests AI | Todo request a LLM se guarda con tokens_used, processing_time, modelo usado | `apps/ai_models/models.py:LLMRequest` |

---

## 2. Requisitos No Funcionales (RNF)

### 2.1 Rendimiento

| ID | Restricción | Valor | Fuente |
|----|-------------|-------|--------|
| RNF-01 | Timeout requests normales | 30 segundos | `apiService.js:17` |
| RNF-02 | Timeout requests AI/LLM | 120 segundos | `apiService.js:18` |
| RNF-03 | Timeout Mole-AI (backend) | 120 segundos configurable | `apps/ai_models/services.py:95` |
| RNF-04 | Retry exponencial en cliente | 3 intentos con backoff 1s, 2s, 4s | `apiService.js:19-20, 321` |
| RNF-05 | Límite de lecturas por lote | Máximo 500 lecturas | `serializers.py:123` |
| RNF-06 | Ventana anti-replay | 300 segundos (±5s tolerancia clock skew) | `apps/core/views.py:85` |

### 2.2 Seguridad

| ID | Restricción | Descripción | Fuente |
|----|-------------|-------------|--------|
| RNF-07 | Algoritmos JWT | HS256 para fallback local, RS256/JWKS para Supabase | `authentication.py:152` |
| RNF-08 | Leeway de expiración JWT | 30 segundos configurable para clock skew | `authentication.py:105` |
| RNF-09 | Autenticación M2M IoT | Header `X-Hardware-Api-Key` con HMAC compare | `authentication.py:294` |
| RNF-10 | Validación de tamaño de imagen | Máximo 10MB | `serializers.py:143` |
| RNF-11 | Validación de tipos de imagen | Solo JPEG, PNG, WEBP con magic bytes | `serializers.py:158-163` |
| RNF-12 | Throttling de Chat LLM | Configurable por throttle class | `apps/core/throttles.py` |
| RNF-13 | Throttling de Diagnósticos | Configurable por throttle class | `apps/core/throttles.py` |
| RNF-14 | Throttling de Telemetría | Configurable por throttle class | `apps/core/throttles.py` |
| RNF-15 | Tokens JWT enmascarados en logs | Nunca se expone token completo | `authentication.py:73-82` |

### 2.3 Disponibilidad y Arquitectura

| ID | Restricción | Descripción | Fuente |
|----|-------------|-------------|--------|
| RNF-16 | Stack tecnológico | Django 4.2+, FastAPI, PostgreSQL 16 + pgvector, Redis 7, Celery | `requirements.txt`, `docker-compose.yml` |
| RNF-17 | WebSockets | Django Channels + Daphne para chat en tiempo real | `requirements.txt:6-8` |
| RNF-18 | Base de datos vectorial | pgvector para embeddings de 1536 dimensiones | `apps/core/models.py:57` |
| RNF-19 | Broker de mensajes | MQTT Mosquitto para telemetría IoT | `docker-compose.yml:171-182` |
| RNF-20 | Redes aisladas | Docker compose con red `mole-ai-net` interna | `docker-compose.yml:1-3` |
| RNF-21 | Puertos expuestos | Solo Django (8000) expuesto al host; microservicios internos | `docker-compose.yml:107-108` |

### 2.4 Integración con Servicios Externos

| ID | Servicio | Uso | Fuente |
|----|----------|-----|--------|
| RNF-22 | Supabase | Autenticación JWT, base de datos principal | `authentication.py`, settings |
| RNF-23 | HuggingFace Inference API | Modelo DeepSeek-VL para visión | `apps/ai_models/utils.py` |
| RNF-24 | Ollama/LLM | Modelo DeepSeek-R1-Distill-Qwen-7B para chat | `ms2_rag_cag_service/application/chat_usecase.py:21` |
| RNF-25 | Trefle.io API | Fallback de conocimiento botánico | `ms2_rag_cag_service/application/chat_usecase.py:37-56` |

### 2.5 Modelos de Inteligencia Artificial

| ID | Modelo | Tipo | Dimensiones | Fuente |
|----|--------|------|-------------|--------|
| RNF-26 | CNN TFLite | Clasificación de enfermedades, regresión pH | TFLite | `ms1_vision/app/dependencies.py:116` |
| RNF-27 | Embeddings | sentence-transformers/all-mpnet-base-v2 | 768 | `apps/ai_models/services.py:247` |
| RNF-28 | Vector store | FAISS | 1536 | `apps/core/models.py:57` |
| RNF-29 | pH colorimetría | HSV Euclidean RGB | N/A | `ms1_vision/app/routes.py:17` |

### 2.6 Almacenamiento y Caching

| ID | Restricción | Valor | Fuente |
|----|-------------|-------|--------|
| RNF-30 | Redis como cache | Sensores en tiempo real (CAG) | `ms2_rag_cag_service/application/chat_usecase.py:16` |
| RNF-31 | Redis pub/sub | Notificaciones de diagnósticos | `ms1_vision/app/dependencies.py:96-101` |
| RNF-32 | Persistencia local | Edge node SQLite para store-and-forward | `edge_node/store_forward_daemon.py` |

### 2.7 Compliance y Normativas

| ID | Norma | Descripción | Fuente |
|----|-------|-------------|--------|
| RNF-33 | ETSI EN 303 645 | Cybersecurity for IoT devices (anti-replay) | `serializers.py:18-21` |
| RNF-34 | MoProSoft | Auditoría inmutable de acciones críticas | `apps/core/models.py:203-207` |
| RNF-35 | OWASP | Validación de magic bytes en uploads | `serializers.py:155-167` |

---

## 3. Matriz de Trazabilidad: Requisito → Implementación

| RF | Componente Backend | Componente MS | Endpoint/API | Frontend |
|----|-------------------|---------------|--------------|----------|
| RF-01 | `apps/authentication/` | - | POST `/auth/register/` | `main.js:submitRegistration()` |
| RF-02 | `authentication.py` | - | POST `/auth/login/` | `main.js:attemptLogin()` |
| RF-06 | `apps/plants/models.py` | - | - | - |
| RF-11 | `apps/core/views.py:sensor_data_view` | - | POST `/sensor-data/` | - |
| RF-12 | `apps/core/views.py:sensor_batch_view` | - | POST `/sensor-data/batch/` | - |
| RF-17 | `apps/ai_models/utils.py` | - | POST `/diagnostics/` | `08_diagnostico_ia.js` |
| RF-19 | - | `ms1_vision/app/routes.py` | POST `/vision/analyze-ph-strip` | - |
| RF-22-26 | `apps/core/infrastructure/clients/microservices.py` | `ms2_rag_cag_service/application/` | POST `/mole-ai/chat` | `03_asistente_botanico.js` |
| RF-31-33 | - | `ms3_reports/app/api/v1/reports.py` | POST/GET `/reports/` | - |
| RF-35 | `apps/core/views.py:feedback_create_view` | - | POST `/feedback/` | - |

---

## 4. Reglas de Negocio Implícitas

### 4.1 Validaciones de Dominio

| Regla | Descripción | Código |
|-------|-------------|--------|
| RB-01 | pH válido | 0.0 ≤ ph_level ≤ 14.0 |
| RB-02 | Humedad válida | 0.0 ≤ soil_humidity ≤ 100.0 |
| RB-03 | Temperatura crítica alta | > 35°C |
| RB-04 | Temperatura crítica baja | < 5°C |
| RB-05 | Humedad crítica baja | < 10% |
| RB-06 | Humedad crítica alta | > 90% |
| RB-07 | pH crítico ácido | < 4.0 |
| RB-08 | pH crítico alcalino | > 9.0 |

### 4.2 Lógica de Priorización

| Condición | Score | Prioridad |
|-----------|-------|-----------|
| Severity: CRITICAL | +100 | INMEDIATA |
| Severity: HIGH | +75 | ALTA |
| Severity: MEDIUM | +50 | MEDIA |
| Severity: LOW | +25 | BAJA |
| Confidence > 80% | +16 (80×0.2) | Bonus |
| requires_immediate_action() | +50 | Urgente |

### 4.3 Estados de Tickets de Feedback

| Estado | Transiciones válidas |
|--------|---------------------|
| open | → in_progress, → closed |
| in_progress | → closed, → open |
| closed | (terminal) |

---

## 5. Dependencias y Versiones Mínimas

```
Django~=4.2
channels~=4.0
daphne~=4.1
channels-redis~=4.2
psycopg2-binary~=2.9
pgvector~=0.3
PyJWT~=2.8
aiohttp~=3.9
celery>=5.3.6
redis>=5.0.0
djangorestframework~=3.14
django-cors-headers~=4.3
argon2-cffi>=23.1
django-axes>=6.1
tenacity>=8.2
bleach>=6.1
```
