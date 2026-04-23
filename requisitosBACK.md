# Mole.AI v2.1 — Requisitos Funcionales y No Funcionales del Backend

**Versión del documento:** 2.1.0
**Fecha:** 2026-04-22
**Formato:** IEEE 830-1998
**Alcance:** core_backend/ (Django) + microservices/ (FastAPI)

---

## CONVENCIONES DEL DOCUMENTO

- **REQ-F:** Requisito Funcional
- **REQ-NF:** Requisito No Funcional
- **MUST:** Obligatorio (debe cumplirse)
- **SHOULD:** Recomendado
- **MAY:** Opcional

---

## 1. REQUISITOS FUNCIONALES (REQ-F)

### 1.1 Autenticación y Autorización

#### REQ-F-AUTH-001: Registro de Usuario Local
- **Descripción:** El sistema debe permitir registrar usuarios locales (agricultores, operadores) con username, email y contraseña.
- **Endpoint:** `POST /api/v1/auth/register/`
- **Método HTTP:** POST
- **Permiso:** AllowAny
- **Payload de entrada:**
  ```json
  {
    "username": "string (required, 3-150 chars)",
    "email": "string (required, valid email format)",
    "password": "string (required, min 6 chars, 1 uppercase, 1 lowercase, 1 number)"
  }
  ```
- **Payload de respuesta (201):**
  ```json
  {
    "status": "created",
    "username": "string",
    "email_verification_required": true
  }
  ```
- **Códigos de error:** 400 (datos inválidos), 400 (usuario existe), 400 (email existe)

---

#### REQ-F-AUTH-002: Login Dual (Username o Email)
- **Descripción:** El sistema debe permitir autenticación usando username O email como identificador.
- **Endpoint:** `POST /api/v1/auth/validate-token/`
- **Método HTTP:** POST
- **Permiso:** AllowAny
- **Payload de entrada:**
  ```json
  {
    "username": "string (puede ser username o email)",
    "password": "string (required)"
  }
  ```
- **Payload de respuesta (200):**
  ```json
  {
    "token": "string (JWT)",
    "role": "string (user|superuser)"
  }
  ```
- **Códigos de error:** 401 (credenciales inválidas)
- **Validación:** Case-insensitive para username y email

---

#### REQ-F-AUTH-003: Verificación de Correo Electrónico
- **Descripción:** El sistema debe generar y enviar un token de verificación al email del usuario tras el registro.
- **Endpoint:** `GET /api/v1/auth/verify-email/<token>/`
- **Método HTTP:** GET
- **Permiso:** AllowAny
- **Payload de respuesta (200):**
  ```json
  {
    "status": "verified",
    "message": "Correo electrónico verificado exitosamente."
  }
  ```
- **Códigos de error:** 400 (token inválido), 400 (token expirado, >24h)

---

#### REQ-F-AUTH-004: Obtención de Perfil de Usuario
- **Descripción:** El sistema debe retornar los datos del perfil del usuario autenticado.
- **Endpoint:** `GET /api/v1/auth/profile/`
- **Método HTTP:** GET
- **Permiso:** IsAuthenticated (JWT Bearer)
- **Payload de respuesta (200):**
  ```json
  {
    "id": "integer",
    "email": "string",
    "full_name": "string",
    "first_name": "string",
    "last_name": "string",
    "avatar_url": "string|null",
    "phone_number": "string|null",
    "supabase_uid": "string|null",
    "supabase_role": "string",
    "is_premium": "boolean",
    "data_consent": "boolean",
    "data_consent_date": "datetime|null",
    "is_email_verified": "boolean"
  }
  ```

---

#### REQ-F-AUTH-005: Actualización de Perfil
- **Descripción:** El sistema debe permitir actualizar campos mutables del perfil (first_name, last_name, avatar_url, phone_number).
- **Endpoint:** `PATCH /api/v1/auth/profile/`
- **Método HTTP:** PATCH
- **Permiso:** IsAuthenticated (JWT Bearer)
- **Payload de entrada:**
  ```json
  {
    "first_name": "string (opcional)",
    "last_name": "string (opcional)",
    "avatar_url": "string (opcional)",
    "phone_number": "string (opcional)"
  }
  ```
- **Payload de respuesta (200):**
  ```json
  {
    "status": "updated",
    "fields": ["array de campos actualizados"]
  }
  ```

---

#### REQ-F-AUTH-006: Eliminación de Cuenta (Derecho ARCO)
- **Descripción:** El sistema debe anonimizar los datos personales del usuario antes de eliminarlo (LFPDPPP Art. 26).
- **Endpoint:** `DELETE /api/v1/auth/profile/`
- **Método HTTP:** DELETE
- **Permiso:** IsAuthenticated (JWT Bearer)
- **Comportamiento:**
  1. Anonimizar: email → `deleted_{user_id}@anonimizado.mole.ai`
  2. Limpiar: first_name, last_name, phone_number, avatar_url, supabase_uid = null/empty
  3. Desactivar: is_active = False
  4. Eliminar usuario (FK con SET_NULL preserva datos científicos)
  5. Crear AuditLog de la acción
- **Payload de respuesta:** 204 No Content
- **Auditoría:** AuditLog.append-only con action="DELETE_ACCOUNT_ARCO"

---

### 1.2 Gestión de Flora y Plantas

#### REQ-F-PLANT-001: Búsqueda de Especies en Catálogo
- **Descripción:** El sistema debe buscar especies por nombre común o científico. Si la especie está protegida por NOM-059, debe incluir advertencia legal.
- **Endpoint:** `GET /api/v1/plants/search/?q=<query>`
- **Método HTTP:** GET
- **Permiso:** AllowAny
- **Query params:** `q` (required, string)
- **Payload de respuesta (200) — Especie NO protegida:**
  ```json
  {
    "id": "uuid",
    "nombre": "string",
    "nombre_cientifico": "string",
    "descripcion": "string|null",
    "humedad": "string|null (ej: 40-60%)",
    "temperatura": "string|null (ej: 18-25°C)",
    "ph": "string|null",
    "uv": "string",
    "recomendacion": "string"
  }
  ```
- **Payload de respuesta (200) — Especie PROTEGIDA (NOM-059):**
  ```json
  {
    "id": "uuid",
    "nombre": "string",
    "nombre_cientifico": "string",
    "is_protected_nom059": true,
    "protection_warning": "string (contiene NOM-059-SEMARNAT)",
    "protection_category": "P|T|Pr"
  }
  ```
- **Códigos de error:** 400 (q requerido), 404 (especie no encontrada)

---

#### REQ-F-PLANT-002: Listar Colección de Plantas del Usuario
- **Descripción:** El sistema debe retornar todas las plantas asociadas al usuario autenticado.
- **Endpoint:** `GET /api/v1/plants/`
- **Método HTTP:** GET
- **Permiso:** IsAuthenticated
- **Payload de respuesta (200):**
  ```json
  {
    "results": [
      {
        "id": "uuid",
        "nickname": "string|null",
        "species_id": "uuid|null",
        "created_at": "datetime"
      }
    ],
    "count": "integer"
  }
  ```

---

#### REQ-F-PLANT-003: Crear Planta
- **Descripción:** El sistema debe crear una nueva planta y retornar un UUID (plant_id) para configurar en ESP32.
- **Endpoint:** `POST /api/v1/plants/`
- **Método HTTP:** POST
- **Permiso:** IsAuthenticated
- **Payload de entrada:**
  ```json
  {
    "nickname": "string (opcional)",
    "species_id": "uuid (opcional)",
    "latitude": "float (opcional)",
    "longitude": "float (opcional)"
  }
  ```
- **Payload de respuesta (201):**
  ```json
  {
    "status": "created",
    "plant_id": "uuid",
    "nickname": "string",
    "message": "Configura este plant_id en tu ESP32 para iniciar la telemetría."
  }
  ```

---

#### REQ-F-PLANT-004: Ver/Actualizar/Eliminar Planta
- **Descripción:** CRUD completo para una planta específica del usuario.
- **Endpoint:** `GET|PATCH|DELETE /api/v1/plants/<uuid>/`
- **Método HTTP:** GET, PATCH, DELETE
- **Permiso:** IsAuthenticated
- **Validación:** La planta debe pertenecer al usuario autenticado
- **Códigos de error:** 404 (planta no encontrada o no pertenece al usuario)

---

#### REQ-F-PLANT-005: Favoritos de Plantas
- **Descripción:** El sistema debe permitir listar, agregar y eliminar plantas favoritas del usuario.
- **Endpoints:**
  - `GET /api/v1/plants/favorites/` — Listar favoritos
  - `POST /api/v1/plants/favorites/` — Agregar a favoritos
  - `DELETE /api/v1/plants/favorites/<int:fav_id>/` — Eliminar favorito
- **Permiso:** IsAuthenticated
- **Constraint:** unique_together(user, plant) — no duplicados

---

### 1.3 Telemetría IoT (M2M)

#### REQ-F-IOT-001: Ingesta de Sensor Individual
- **Descripción:** El sistema debe registrar lecturas de sensores desde dispositivos ESP32 con protección anti-replay.
- **Endpoint:** `POST /api/v1/sensor-data/`
- **Método HTTP:** POST
- **Permiso:** HardwareOnly (X-Hardware-Api-Key)
- **Payload de entrada:**
  ```json
  {
    "plant_id": "uuid (required, debe existir en UserPlant)",
    "recorded_at": "datetime ISO8601 (required)",
    "soil_humidity": "float (optional, 0-100)",
    "air_temperature": "float (optional, °C)",
    "uv_index": "float (optional, 0-11)",
    "light_level": "float (optional, lux)",
    "ph_level": "float (optional, 0-14)"
  }
  ```
- **Anti-Replay:** Si `abs(now - recorded_at) > 300 segundos` → HTTP 403
- **Payload de respuesta (201):**
  ```json
  {
    "status": "success",
    "registered": 1
  }
  ```

---

#### REQ-F-IOT-002: Ingesta de Lote de Sensores
- **Descripción:** El sistema debe registrar múltiples lecturas de sensores en una sola transacción.
- **Endpoint:** `POST /api/v1/sensor-data/batch/`
- **Método HTTP:** POST
- **Permiso:** HardwareOnly
- **Payload de entrada:**
  ```json
  {
    "batch": [
      {
        "plant_id": "uuid",
        "recorded_at": "datetime",
        "soil_humidity": "float",
        "air_temperature": "float"
      }
    ]
  }
  ```
- **Implementación:** bulk_create() para eficiencia
- **Anti-Replay:** Validación en primer registro del lote

---

#### REQ-F-IOT-003: Telemetría Más Reciente (JWT)
- **Descripción:** El sistema debe retornar la última lectura de telemetría para una planta del usuario.
- **Endpoint:** `GET /api/v1/telemetry/latest/?plant_id=<uuid>`
- **Método HTTP:** GET
- **Permiso:** IsAuthenticated
- **Validación:** La planta debe pertenecer al usuario autenticado
- **Payload de respuesta (200):**
  ```json
  {
    "plant_id": "uuid",
    "recorded_at": "datetime",
    "soil_humidity": "float|null",
    "air_humidity": "float|null",
    "air_temperature": "float|null",
    "uv_index": "float|null",
    "ph_level": "float|null"
  }
  ```

---

### 1.4 Inteligencia Artificial y Diagnósticos

#### REQ-F-AI-001: Solicitar Diagnóstico de Imagen (Async)
- **Descripción:** El sistema debe procesar imágenes de plantas de forma asíncrona via Celery y retornar un task_id para polling.
- **Endpoint:** `POST /api/v1/diagnostics/`
- **Método HTTP:** POST
- **Permiso:** IsAuthenticated
- **Payload:** multipart/form-data con campo `image` (JPEG/PNG/WebP, max 10MB)
- **Flujo:**
  1. Guardar imagen temporalmente
  2. Encolar `analyze_vision_async.delay(file_path, auth_token, user_id, plant_id)`
  3. Retornar task_id inmediatamente (no bloquear)
- **Payload de respuesta (202):**
  ```json
  {
    "status": "processing",
    "task_id": "string (Celery task ID)",
    "message": "Diagnóstico en cola. Consulta /api/v1/ai/vision/status/{task_id} para ver el resultado."
  }
  ```

---

#### REQ-F-AI-002: Consultar Estado de Diagnóstico
- **Descripción:** El sistema debe permitir polling del estado de una tarea Celery.
- **Endpoint:** `GET /api/v1/ai/vision/status/<task_id>/`
- **Método HTTP:** GET
- **Permiso:** IsAuthenticated
- **Estados de Celery:** PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, REVOKED
- **Payload de respuesta (200):**
  ```json
  {
    "task_state": "string (SUCCESS|PENDING|FAILURE)",
    "result": {
      "condition": "string",
      "confidence": "float",
      "species": "string",
      "severity": "string",
      "ph_predicted": "float|null",
      "diagnostic_id": "uuid"
    },
    "info": "string|null"
  }
  ```

---

#### REQ-F-AI-003: Historial de Diagnósticos
- **Descripción:** El sistema debe retornar el historial de diagnósticos del usuario.
- **Endpoint:** `GET /api/v1/diagnostics/history/`
- **Método HTTP:** GET
- **Permiso:** IsAuthenticated
- **Query params:** `limit` (default: 20)
- **Payload de respuesta (200):**
  ```json
  {
    "results": [
      {
        "id": "uuid",
        "plant_id": "uuid",
        "condition": "string",
        "analyzed_at": "datetime"
      }
    ]
  }
  ```

---

#### REQ-F-AI-004: Chat RAG con Contexto de Sensores
- **Descripción:** El sistema debe generar respuestas de IA con contexto de sensores y RAG.
- **Endpoint:** `POST /api/v1/chat/fallback/`
- **Método HTTP:** POST
- **Permiso:** IsAuthenticated
- **Throttle:** 60 requests/minuto (LLMChatThrottle)
- **Payload de entrada:**
  ```json
  {
    "question": "string (required)"
  }
  ```
- **Payload de respuesta (200):**
  ```json
  {
    "answer": "string",
    "disclaimer": "AVISO LEGAL: Información generada por IA..."
  }
  ```

---

### 1.5 Reportes y Microservicios

#### REQ-F-REPORT-001: Solicitar Generación de Reporte
- **Descripción:** El sistema debe encolar la generación de un reporte asíncrono via Celery.
- **Endpoint:** `POST /api/v1/reports/generate` (via MS3/nginx)
- **Método HTTP:** POST
- **Permiso:** IsAuthenticated (JWT)
- **Payload de entrada:**
  ```json
  {
    "date_range_days": "integer (default: 90)",
    "sensors": ["array de strings (opcional)"]
  }
  ```
- **Payload de respuesta (202):**
  ```json
  {
    "job_id": "uuid",
    "status": "queued"
  }
  ```
- **Seguridad:** user_id hasheado (SHA-256) antes de transitar por Redis

---

#### REQ-F-REPORT-002: Consultar Estado de Reporte
- **Descripción:** El sistema debe permitir consultar el estado de un job de reporte.
- **Endpoint:** `GET /api/v1/reports/<job_id>/status`
- **Método HTTP:** GET
- **Permiso:** IsAuthenticated ( ownership check )
- **Payload de respuesta (200):**
  ```json
  {
    "job_id": "uuid",
    "status": "PENDING|PROCESSING|SUCCESS|FAILURE",
    "pdf_s3_path": "string|null"
  }
  ```

---

### 1.6 Sistema y Monitoreo

#### REQ-F-SYS-001: Health Check Global
- **Descripción:** El sistema debe exponer endpoints de salud para monitoreo.
- **Endpoints:**
  - `GET /api/v1/health/` — AllowAny
  - `GET /api/v1/auth/health/` — IsAuthenticated
  - `GET /api/v1/ai/health/` — IsAuthenticated
- **Payload de respuesta (200):**
  ```json
  {
    "status": "healthy",
    "timestamp": "datetime"
  }
  ```

---

#### REQ-F-SYS-002: Feedback de Usuario
- **Descripción:** El sistema debe permitir a usuarios enviar feedback sobre errores de IA o sugerencias.
- **Endpoint:** `POST /api/v1/feedback/`
- **Método HTTP:** POST
- **Permiso:** IsAuthenticated
- **Payload de entrada:**
  ```json
  {
    "topic": "string (bug|suggestion|ai_error|other)",
    "message": "string (required)"
  }
  ```

---

## 2. REQUISITOS NO FUNCIONALES (REQ-NF)

### 2.1 Seguridad

#### REQ-NF-SEC-001: Autenticación JWT
- **Descripción:** El sistema debe usar JWT (HS256 o ES256) para autenticación de usuarios.
- **Implementación:** Supabase JWT Secret o SECRET_KEY de Django como signing key
- **Expiry:** 1 día (24 horas)
- **Leeway:** 30 segundos para clock skew

---

#### REQ-NF-SEC-002: Protección Anti-Brute-Force
- **Descripción:** El sistema debe bloquear direcciones IP tras 5 intentos fallidos de login.
- **Implementación:** Django-axes
- **Lockout params:** username, ip_address
- **Cooloff time:** 1 hora

---

#### REQ-NF-SEC-003: Protección Anti-Replay (IoT)
- **Descripción:** Los endpoints de telemetría deben rechazar lecturas con timestamp > 300 segundos de delta.
- **Implementación:** Validación en sensor_data_view, sensor_batch_view, sensors_ingest_view
- **Error:** HTTP 403 "Replay attack protection"

---

#### REQ-NF-SEC-004: Rate Limiting por Tipo de Request
- **Descripción:** El sistema debe aplicar rate limits diferenciados según el tipo de endpoint.
- **Límites:**
  - Anónimo: 100 requests/hora
  - Autenticado: 10,000 requests/minuto
  - LLM Chat: 60 requests/minuto
  - Diagnostics: 30 requests/minuto
  - Sensor Data: 200 requests/minuto

---

#### REQ-NF-SEC-005: CORS Gestionado por Nginx
- **Descripción:** El API Gateway (Nginx) debe manejar CORS, no Django ni FastAPI.
- **Orígenes permitidos:** localhost:*, 127.0.0.1:* (desarrollo)
- **Métodos:** GET, POST, PUT, PATCH, DELETE, OPTIONS
- **Headers:** Accept, Authorization, Content-Type, X-CSRFToken, X-Requested-With, X-Hardware-Api-Key

---

#### REQ-NF-SEC-006: Headers de Seguridad en Nginx
- **Descripción:** El API Gateway debe agregar headers de seguridad a todas las respuestas.
- **Headers:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-XSS-Protection: 1; mode=block`

---

### 2.2 Protección de Datos (LFPDPPP)

#### REQ-NF-DP-001: Consentimiento Explícito
- **Descripción:** El sistema debe requerir consentimiento explícito del usuario para tratamiento de datos.
- **Campo:** User.data_consent (boolean)
- **Timestamp:** User.data_consent_date

---

#### REQ-NF-DP-002: Derecho de Cancelación (ARCO)
- **Descripción:** El sistema debe anonimizar PII antes de eliminar usuarios.
- **Anonimización:** email → `deleted_{id}@anonimizado.mole.ai`
- **Preservación:** Datos científicos con FK SET_NULL

---

#### REQ-NF-DP-003: Hash de user_id en Colas
- **Descripción:** El user_id real no debe transitar por Redis en tareas Celery.
- **Implementación:** SHA-256 hash antes de enviar a cola
- **Archivos:** apps/core/tasks.py (_hash_user_id)

---

#### REQ-NF-DP-004: Inmutabilidad de Logs de Auditoría
- **Descripción:** Los registros de AuditLog no deben poder modificarse ni eliminarse.
- **Implementación:** Override de save() y delete() en modelo AuditLog
- **Excepción:** PermissionError("MoProSoft Compliance: Audit logs are immutable...")

---

### 2.3 Cumplimiento Normativo

#### REQ-NF-NOM-001: Identificación de Flora Protegida
- **Descripción:** El sistema debe identificar y advertir sobre especies protegidas por NOM-059.
- **Campo:** SpeciesCatalog.is_protected_nom059
- **Categorías:** P (peligro), T (amenazada), Pr (protección especial)

---

### 2.4 Rendimiento

#### REQ-NF-PERF-001: Procesamiento Asíncrono de IA
- **Descripción:** Los endpoints de diagnóstico de imagen no deben bloquear el hilo de Django.
- **Implementación:** Celery con tasks.delay() para analyze_vision_async
- **Timeout MS1:** 30 segundos

---

#### REQ-NF-PERF-002: Bulk Insert para Lotes de Sensores
- **Descripción:** La ingesta de lotes debe usar bulk_create() para eficiencia.
- **Implementación:** SensorLog.objects.bulk_create(logs)

---

#### REQ-NF-PERF-003: Índices de Base de Datos
- **Descripción:** El sistema debe mantener índices para consultas frecuentes.
- **Índices definidos:**
  - SensorLog: plant_id, recorded_at, (plant_id, recorded_at)
  - AIDiagnostic: user, analyzed_at, plant_id
  - DiagnosticoGeolocalizado: latitude, user
  - SpeciesCatalog: scientific_name, common_name

---

### 2.5 Arquitectura

#### REQ-NF-ARC-001: API Gateway como Único Punto de Entrada
- **Descripción:** Todo el tráfico HTTP externo debe pasar por Nginx (puerto 8080).
- **Redes Docker:** mole_public (nginx), mole_internal (todos los servicios)

---

#### REQ-NF-ARC-002: Aislamiento de Microservicios
- **Descripción:** Los microservicios deben comunicarse solo a través de Nginx o Celery.
- **Endpoints internos:** ms1_vision:8001, ms2_chat:8002, ms3_reports:8003
- **Nginx routes:**
  - `/api/v1/vision/*` → ms1_vision
  - `/api/v1/mole-ai/*` → ms2_chat
  - `/api/v1/knowledge/*` → ms2_chat
  - `/api/v1/reports/*` → ms3_reports

---

#### REQ-NF-ARC-003: Tareas Celery con Colas Dedicadas
- **Descripción:** Las tareas deben usar colas específicas para distribución de carga.
- **Colas definidas:**
  - default: cleanup_temp_files, refresh_admin_stats_task
  - vision_queue: analyze_vision_async, train_vision_async
  - reports_queue: generate_report_task

---

### 2.6 Persistencia

#### REQ-NF-PERS-001: Supervivencia de Datos Científicos
- **Descripción:** Los datos de telemetría y diagnósticos deben sobrevivir a la eliminación de usuarios o plantas.
- **Implementación:**
  - SensorLog.plant_id: UUIDField (no FK) — independientes
  - AIDiagnostic.user: FK con on_delete=SET_NULL

---

#### REQ-NF-PERS-002: Almacenamiento de Archivos
- **Descripción:** El sistema debe soportar almacenamiento local (MEDIA_ROOT) o S3 (MinIO).
- **Configuración:** DEFAULT_FILE_STORAGE en settings.py
- **Limpieza automática:** cleanup_temp_files (daily, >24h)

---

### 2.7 Monitoreo

#### REQ-NF-MON-001: Logs Estandarizados
- **Descripción:** El sistema debe usar logging estructurado (structlog en FastAPI, logging en Django).
- **Niveles:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Handler:** console (stdout) para Docker

---

#### REQ-NF-MON-002: Métricas de Rendimiento de IA
- **Descripción:** El sistema debe registrar tiempo de respuesta y éxito/fallo de modelos.
- **Modelo:** ModelPerformance (apps/ai_models/models.py)
- **Métricas:** avg_response_time_ms, p95, p99, total_requests, successful_requests, failed_requests

---

## 3. MATRIZ DE RUTAS VS REQUISITOS

| Ruta | Método | REQ-F Asociado | Permiso |
|------|--------|----------------|--------|
| `/api/v1/auth/register/` | POST | REQ-F-AUTH-001 | AllowAny |
| `/api/v1/auth/validate-token/` | POST | REQ-F-AUTH-002 | AllowAny |
| `/api/v1/auth/verify-email/<token>/` | GET | REQ-F-AUTH-003 | AllowAny |
| `/api/v1/auth/profile/` | GET/PATCH/DELETE | REQ-F-AUTH-004/005/006 | IsAuthenticated |
| `/api/v1/auth/subscription/` | GET | — | IsAuthenticated |
| `/api/v1/auth/metadata/` | GET | — | IsAuthenticated |
| `/api/v1/auth/logout/` | POST | — | IsAuthenticated |
| `/api/v1/auth/health/` | GET | REQ-F-SYS-001 | IsAuthenticated |
| `/api/v1/plants/search/` | GET | REQ-F-PLANT-001 | AllowAny |
| `/api/v1/plants/` | GET/POST | REQ-F-PLANT-002/003 | IsAuthenticated |
| `/api/v1/plants/<uuid>/` | GET/PATCH/DELETE | REQ-F-PLANT-004 | IsAuthenticated |
| `/api/v1/plants/favorites/` | GET/POST | REQ-F-PLANT-005 | IsAuthenticated |
| `/api/v1/plants/favorites/<id>/` | DELETE | REQ-F-PLANT-005 | IsAuthenticated |
| `/api/v1/plants/species/` | GET/POST | — | ReadOnly/Admin |
| `/api/v1/sensor-data/` | POST | REQ-F-IOT-001 | HardwareOnly |
| `/api/v1/sensor-data/batch/` | POST | REQ-F-IOT-002 | HardwareOnly |
| `/api/v1/sensor-data/<pk>/` | PATCH | — | HardwareOnly |
| `/api/v1/telemetry/latest/` | GET | REQ-F-IOT-003 | IsAuthenticated |
| `/api/v1/sensors/ingest` | POST | REQ-F-IOT-003 | JWT |
| `/api/v1/diagnostics/` | POST | REQ-F-AI-001 | IsAuthenticated |
| `/api/v1/diagnostics/history/` | GET | REQ-F-AI-003 | IsAuthenticated |
| `/api/v1/ai/vision/analyze/` | POST | REQ-F-AI-001 | IsAuthenticated |
| `/api/v1/ai/vision/status/<task_id>/` | GET | REQ-F-AI-002 | IsAuthenticated |
| `/api/v1/chat/fallback/` | POST | REQ-F-AI-004 | IsAuthenticated |
| `/api/v1/chat/history/` | GET | — | IsAuthenticated |
| `/api/v1/reports/generate` | POST | REQ-F-REPORT-001 | IsAuthenticated |
| `/api/v1/reports/<job_id>/status` | GET | REQ-F-REPORT-002 | IsAuthenticated |
| `/api/v1/health/` | GET | REQ-F-SYS-001 | AllowAny |
| `/api/v1/feedback/` | POST | REQ-F-SYS-002 | IsAuthenticated |
| `/api/v1/map/hotspots/` | GET | — | IsAuthenticated |
| `/api/v1/diagnostics/geolocalizados/` | GET/POST | — | IsAuthenticated |

---

## 4. FLUJOS PRINCIPALES

### 4.1 Flujo: Registro → Diagnóstico de Planta

```
[1] POST /api/v1/auth/register/          → 201 (user_id, email_verification_required)
[2] GET  /api/v1/auth/verify-email/<token>/ → 200 (is_email_verified=true)
[3] POST /api/v1/auth/validate-token/   → 200 (token JWT)
[4] POST /api/v1/plants/                → 201 (plant_id UUID)
[5] POST /api/v1/diagnostics/           → 202 (task_id)
[6] GET  /api/v1/ai/vision/status/<task_id>/ → 200 (result)
```

### 4.2 Flujo: Telemetría IoT

```
[1] POST /api/v1/sensor-data/           → 201 (X-Hardware-Api-Key, Anti-Replay check)
    └── SensorLog.create() → PostgreSQL
```

### 4.3 Flujo: Solicitud de Reporte

```
[1] POST /api/v1/reports/generate       → 202 (job_id, hashed_user_id en Redis)
[2] GET  /api/v1/reports/<job_id>/status → 200 (polling)
[3] GET  /api/v1/reports/<job_id>/download → 200 (PDF URL)
```

---

## 5. DEPENDENCIAS EXTERNAS

| Servicio | Propósito | Variables de Entorno Requeridas |
|----------|-----------|-------------------------------|
| Supabase | Auth, Database | `SUPABASE_URL`, `SUPABASE_JWT_SECRET` |
| PostgreSQL | Primary DB | `SUPABASE_DB_*` o `DATABASE_URL` |
| Redis | Cache, Celery Broker | `REDIS_URL` |
| MinIO | Object Storage | `SUPABASE_S3_*` |
| HuggingFace | Modelos de IA | `HUGGINGFACE_API_KEY` |