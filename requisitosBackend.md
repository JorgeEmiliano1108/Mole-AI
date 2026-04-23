# Mole.AI v2.0 — Requisitos del Backend (IEEE 830)

**Fecha:** 2026-04-22
**Versión del Documento:** 2.0.0
**Formato:** IEEE 830-1998

---

## 1. Introducción

### 1.1 Propósito del Documento

Este documento establece los requisitos funcionales y no funcionales del ecosistema backend de Mole.AI v2.0, derivados mediante ingeniería inversa del código fuente existente. Cada requisito refleja una capacidad verificada en el código.

### 1.2 Alcance del Sistema

El backend de Mole.AI v2.0 comprende:
- **Orquestador:** Django 5.2 (Puerto 8000)
- **Microservicios:** 3 servicios FastAPI independientes
- **Colas:** Celery + Redis para tareas asíncronas
- **Base de Datos:** PostgreSQL + pgvector (en producción) / SQLite (desarrollo)
- **Almacenamiento:** MinIO (S3-compatible) para archivos y reportes

---

## 2. Requisitos Funcionales

### REQ-F-BE-001: Gestión de Autenticación y Autorización

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Crítica |
| **Fuente** | `apps/authentication/` |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso |
|----|-------------|--------|------|---------|
| REQ-F-BE-001.1 | Validar token JWT (local o Supabase) | POST | `/api/v1/auth/validate-token/` | AllowAny |
| REQ-F-BE-001.2 | Registrar usuario local (username/password) | POST | `/api/v1/auth/register/` | AllowAny |
| REQ-F-BE-001.3 | Obtener perfil del usuario autenticado | GET | `/api/v1/auth/profile/` | IsAuthenticated |
| REQ-F-BE-001.4 | Actualizar campos mutables del perfil | PATCH | `/api/v1/auth/profile/` | IsAuthenticated |
| REQ-F-BE-001.5 | Eliminar cuenta (Derecho ARCO - Cancelación) | DELETE | `/api/v1/auth/profile/` | IsAuthenticated |
| REQ-F-BE-001.6 | Consultar suscripción activa | GET | `/api/v1/auth/subscription/` | IsAuthenticated |
| REQ-F-BE-001.7 | Consultar metadata JWT de Supabase | GET | `/api/v1/auth/metadata/` | IsAuthenticated |
| REQ-F-BE-001.8 | Logout stateless | POST | `/api/v1/auth/logout/` | IsAuthenticated |

#### Payload — Registro:
```json
{
  "username": "string",
  "password": "string",
  "email": "string (opcional)"
}
```

#### Payload — Validación (Local):
```json
{
  "username": "string",
  "password": "string"
}
```

#### Payload — Validación (Supabase):
```http
Authorization: Bearer <jwt_supabase>
```

---

### REQ-F-BE-002: Gestión de Flora (Catálogo y Colección)

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Crítica |
| **Fuente** | `apps/plants/` |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso |
|----|-------------|--------|------|---------|
| REQ-F-BE-002.1 | Buscar especie en catálogo público | GET | `/api/v1/plants/search/?q=` | AllowAny |
| REQ-F-BE-002.2 | Listar colección de plantas del usuario | GET | `/api/v1/plants/` | IsAuthenticated |
| REQ-F-BE-002.3 | Crear nueva planta (obtener UUID para ESP32) | POST | `/api/v1/plants/` | IsAuthenticated |
| REQ-F-BE-002.4 | Ver detalle de una planta | GET | `/api/v1/plants/<uuid>/` | IsAuthenticated |
| REQ-F-BE-002.5 | Actualizar datos de planta | PATCH | `/api/v1/plants/<uuid>/` | IsAuthenticated |
| REQ-F-BE-002.6 | Eliminar planta | DELETE | `/api/v1/plants/<uuid>/` | IsAuthenticated |
| REQ-F-BE-002.7 | Listar especies (CRUD admin) | GET/POST | `/api/v1/plants/species/` | ReadOnly/Admin |
| REQ-F-BE-002.8 | Detalle/Actualizar/Eliminar especie | GET/PUT/DELETE | `/api/v1/plants/species/<uuid>/` | Admin |

#### Payload — Crear Planta:
```json
{
  "nickname": "string",
  "species_id": "uuid (opcional)",
  "latitude": "float (opcional)",
  "longitude": "float (opcional)"
}
```

#### Response — Crear Planta:
```json
{
  "status": "created",
  "plant_id": "uuid",
  "nickname": "string",
  "message": "Configura este plant_id en tu ESP32 para iniciar la telemetría."
}
```

---

### REQ-F-BE-003: Ingesta de Telemetría IoT (M2M)

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Crítica |
| **Fuente** | `apps/core/views.py`, `apps/core/api_views.py` |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso | Auth |
|----|-------------|--------|------|---------|------|
| REQ-F-BE-003.1 | Registrar lectura de sensor única | POST | `/api/v1/sensor-data/` | HardwareOnly | X-Hardware-Api-Key |
| REQ-F-BE-003.2 | Registrar lote de lecturas | POST | `/api/v1/sensor-data/batch/` | HardwareOnly | X-Hardware-Api-Key |
| REQ-F-BE-003.3 | Actualizar lectura existente | PATCH | `/api/v1/sensor-data/<id>/` | HardwareOnly | X-Hardware-Api-Key |
| REQ-F-BE-003.4 | Obtener telemetría más reciente | GET | `/api/v1/telemetry/latest/?plant_id=` | IsAuthenticated | JWT |
| REQ-F-BE-003.5 | Ingesta JWT-protegida (nueva) | POST | `/api/v1/sensors/ingest` | IsAuthenticated | JWT |

#### Anti-Replay (ETSI EN 303 645):
- Todas las ingestas verifican `recorded_at` delta ≤ 300 segundos
- Si delta > 300s → HTTP 403 "Replay attack protection"

#### Payload — Lectura Individual:
```json
{
  "plant_id": "uuid",
  "recorded_at": "ISO8601",
  "soil_humidity": "float",
  "air_temperature": "float",
  "uv_index": "float",
  "light_level": "float",
  "ph_level": "float (opcional, inferido por CNN)"
}
```

#### Payload — Lote:
```json
{
  "batch": [
    { "plant_id": "uuid", "recorded_at": "ISO8601", "soil_humidity": 45.2, ... },
    ...
  ]
}
```

---

### REQ-F-BE-004: Diagnósticos de IA y Visión

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Alta |
| **Fuente** | `apps/ai_models/views.py`, `apps/core/views.py` |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso |
|----|-------------|--------|------|---------|
| REQ-F-BE-004.1 | Solicitar análisis de imagen (async) | POST | `/api/v1/ai/vision/analyze/` | IsAuthenticated |
| REQ-F-BE-004.2 | Consultar estado de tarea de visión | GET | `/api/v1/ai/vision/status/<task_id>/` | IsAuthenticated |
| REQ-F-BE-004.3 | Entrenar modelo RAG (admin) | POST | `/api/v1/ai/train/rag/` | IsAdminUser |
| REQ-F-BE-004.4 | Entrenar modelo de visión (admin) | POST | `/api/v1/ai/train/vision/` | IsAdminUser |
| REQ-F-BE-004.5 | Solicitar diagnóstico de planta | POST | `/api/v1/diagnostics/` | IsAuthenticated |
| REQ-F-BE-004.6 | Ver historial de diagnósticos | GET | `/api/v1/diagnostics/history/` | IsAuthenticated |
| REQ-F-BE-004.7 | Descargar PDF de diagnóstico | GET | `/api/v1/diagnostics/<uuid>/download/` | IsAuthenticated |

#### Payload — Analizar Imagen:
```
Content-Type: multipart/form-data
- image: <archivo JPEG/PNG/WebP, max 10MB>
```

#### Response — Estado de Tarea:
```json
{
  "task_state": "PENDING|PROGRESS|SUCCESS|FAILURE",
  "result": { ... },
  "info": "string"
}
```

---

### REQ-F-BE-005: Chat RAG y Conocimiento Botánico

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Alta |
| **Fuente** | `apps/core/views.py`, MS2 mole_chat |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso | Origen |
|----|-------------|--------|------|---------|--------|
| REQ-F-BE-005.1 | Chat con contexto RAG (sensor data) | POST | `/api/v1/chat/fallback/` | IsAuthenticated | Django |
| REQ-F-BE-005.2 | Consultar historial de chat | GET | `/api/v1/chat/history/` | IsAuthenticated | Django |
| REQ-F-BE-005.3 | Motor RAG principal (MS2) | POST | `/api/v1/mole-ai/chat` | IsAuthenticated | MS2 |
| REQ-F-BE-005.4 | Ingestar manual PDF | POST | `/api/v1/knowledge/ingest-pdf` | IsAuthenticated | MS2 |
| REQ-F-BE-005.5 | Eliminar documento del índice | DELETE | `/api/v1/knowledge/pdf/<doc_id>` | IsAuthenticated | MS2 |

#### Payload — Chat RAG (Django):
```json
{
  "question": "string"
}
```

#### Response — Chat RAG (Django):
```json
{
  "answer": "string",
  "disclaimer": "AVISO LEGAL: Información generada por IA..."
}
```

---

### REQ-F-BE-006: Reportes Asíncronos

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Media |
| **Fuente** | MS3 mole_report |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso |
|----|-------------|--------|------|---------|
| REQ-F-BE-006.1 | Solicitar generación de reporte | POST | `/api/v1/reports/generate` | IsAuthenticated |
| REQ-F-BE-006.2 | Consultar estado del job | GET | `/api/v1/reports/<job_id>/status` | IsAuthenticated |
| REQ-F-BE-006.3 | Descargar reporte generado | GET | `/api/v1/reports/<job_id>/download` | IsAuthenticated |

#### Payload — Generar Reporte:
```json
{
  "date_range_days": 90,
  "sensors": ["soil_humidity", "air_temperature"]
}
```

#### Response — Estado:
```json
{
  "job_id": "uuid",
  "status": "PENDING|PROCESSING|SUCCESS|FAILURE",
  "pdf_s3_path": "string (si SUCCESS)"
}
```

---

### REQ-F-BE-007: Sistema y Monitoreo

| Atributo | Descripción |
|----------|-------------|
| **Prioridad** | Media |
| **Fuente** | `apps/core/views.py`, `apps/authentication/views.py`, `apps/ai_models/views.py` |

#### Subrequisitos:

| ID | Descripción | Método | Ruta | Permiso |
|----|-------------|--------|------|---------|
| REQ-F-BE-007.1 | Health check general | GET | `/api/v1/health/` | AllowAny |
| REQ-F-BE-007.2 | Health check de autenticación | GET | `/api/v1/auth/health/` | IsAuthenticated |
| REQ-F-BE-007.3 | Health check de IA | GET | `/api/v1/ai/health/` | IsAuthenticated |
| REQ-F-BE-007.4 | Health check de MS2 (RAG) | GET | `/api/v1/health` | AllowAny |
| REQ-F-BE-007.5 | Health check de MS1 (Vision) | GET | `/api/v1/vision/health` | AllowAny |
| REQ-F-BE-007.6 | Feedback de usuario | POST | `/api/v1/feedback/` | IsAuthenticated |

---

## 3. Requisitos No Funcionales

### REQ-NF-BE-001: Arquitectura de Red y Contenedores

| Atributo | Descripción |
|----------|-------------|
| **Tipo** | Arquitectura |
| **Prioridad** | Crítica |

- El API Gateway (Nginx) es el único punto de entrada público (puerto 8080)
- Todos los servicios backend residen en la red Docker aislada `mole_internal`
- Nginx maneja CORS para todas las peticiones `/api/*`
- No hay comunicación directa entre frontend y servicios backend

**Redes Docker:**
```
mole_public    → nginx (acceso público)
mole_internal  → nginx, django-backend, ms1-3, redis, postgres, minio, mqtt
```

---

### REQ-NF-BE-002: Seguridad Zero-Trust

| Atributo | Descripción |
|----------|-------------|
| **Tipo** | Seguridad |
| **Prioridad** | Crítica |

- JWT (Supabase HS256/ES256) para autenticación de usuarios
- API Key para dispositivos IoT hardware
- Rate limiting: 60 req/min (llm_chat), 30 req/min (diagnostics), 200 req/min (sensor_data)
- Axes (Django) para protección contra brute-force
- CORS strict en Nginx (solo localhost en desarrollo)
- Headers de seguridad en Nginx: X-Content-Type-Options, X-Frame-Options, Referrer-Policy

---

### REQ-NF-BE-003: Protección de Datos Personales (LFPDPPP)

| Atributo | Descripción |
|----------|-------------|
| **Tipo** | Cumplimiento Normativo |
| **Prioridad** | Crítica |

- Consentimiento explícito requerido (`data_consent = True`)
- Anonimización de PII en eliminación de cuenta
- user_id hasheado (SHA-256) en tareas Celery que transitan por Redis
- Logs de auditoría inmutables (append-only, no delete)
- Modelo de usuario con FK `on_delete=SET_NULL` para preservar datos científicos

---

### REQ-NF-BE-004: Rendimiento de Microservicios

| Atributo | Descripción |
|----------|-------------|
| **Tipo** | Rendimiento |
| **Prioridad** | Alta |

- MS1 Vision: Modelo TFLite cargado en memoria al startup
- MS2 Chat: FAISS vector store con TTL de cache en Redis
- MS3 Reports: Tareas Celery en cola dedicada `reports_queue`
- Tiempo máximo de respuesta LLM: 120s (configurable)
- Retries automáticos con backoff exponencial (1-10s, max 3 intentos)

---

### REQ-NF-BE-005: Persistencia y Almacenamiento

| Atributo | Descripción |
|----------|-------------|
| **Tipo** | Almacenamiento |
| **Prioridad** | Alta |

- PostgreSQL con extensión pgvector para embeddings
- MinIO (S3) para imágenes, PDFs y reportes
- Redis para cache y job metadata
- Archivos temporales limpiados automáticamente cada 24h (Celery Beat)
- Static files servidos por WhiteNoise con compression

---

### REQ-NF-BE-006: Compatibilidad y Testing

| Atributo | Descripción |
|----------|-------------|
| **Tipo** | Compatibilidad |
| **Prioridad** | Media |

- Django 5.2 con soporte hasta 2026
- FastAPI 0.100+ con Pydantic v2
- Python 3.11+
- Endpoints documentados con OpenAPI (drf-spectacular, FastAPI auto)
- Tests de integración en `core_backend/tests/integration/`

---

## 4. Matriz de Flujos de API

### 4.1 Flujo: Alta de Usuario → Telemetría

```
[1] POST /api/v1/auth/register/
    → { "username": "...", "password": "..." }
    ← { "status": "created", "username": "..." }

[2] POST /api/v1/auth/validate-token/
    → { "username": "...", "password": "..." }
    ← { "token": "eyJ...", "role": "user" }

[3] POST /api/v1/plants/
    Headers: Authorization: Bearer eyJ...
    → { "nickname": "Mi Tomate" }
    ← { "plant_id": "uuid", "status": "created" }

[4] POST /api/v1/sensor-data/
    Headers: X-Hardware-Api-Key: <key>
    → { "plant_id": "uuid", "soil_humidity": 45.2, "recorded_at": "..." }
    ← { "status": "success", "registered": 1 }
```

### 4.2 Flujo: Diagnóstico de Imagen

```
[1] POST /api/v1/ai/vision/analyze/
    Headers: Authorization: Bearer eyJ...
    Content-Type: multipart/form-data
    → image: <file>
    ← { "status": "accepted", "task_id": "uuid" }

[2] GET /api/v1/ai/vision/status/<task_id>/
    Headers: Authorization: Bearer eyJ...
    ← { "task_state": "SUCCESS", "result": { ... } }

[3] POST /api/v1/feedback/
    Headers: Authorization: Bearer eyJ...
    → { "topic": "ai_error", "message": "..." }
    ← { "status": "created", ... }
```

### 4.3 Flujo: Solicitud de Reporte

```
[1] POST /api/v1/reports/generate
    Headers: Authorization: Bearer eyJ...
    → { "date_range_days": 30, "sensors": ["soil_humidity"] }
    ← { "job_id": "uuid", "status": "queued" }

[2] GET /api/v1/reports/<job_id>/status
    Headers: Authorization: Bearer eyJ...
    ← { "status": "PROCESSING" }

[3] GET /api/v1/reports/<job_id>/status (polling)
    ← { "status": "SUCCESS", "pdf_s3_path": "..." }

[4] GET /api/v1/reports/<job_id>/download
    Headers: Authorization: Bearer eyJ...
    ← { "download_url": "/static/reports/<job_id>.pdf" }
```

---

## 5. Endpoints por Servicio

### 5.1 Django (Orquestador) — Puerto 8000

| Prefix | Método | Ruta | Descripción |
|--------|--------|------|-------------|
| `/api/v1/auth/` | POST | `validate-token/` | Validación de JWT |
| `/api/v1/auth/` | POST | `register/` | Registro local |
| `/api/v1/auth/` | GET | `profile/` | Perfil de usuario |
| `/api/v1/auth/` | PATCH | `profile/` | Actualizar perfil |
| `/api/v1/auth/` | DELETE | `profile/` | Eliminar cuenta (ARCO) |
| `/api/v1/plants/` | GET | `search/?q=` | Búsqueda de especies |
| `/api/v1/plants/` | GET/POST | `` | Colección de plantas |
| `/api/v1/plants/` | GET/PATCH/DELETE | `<uuid>/` | Detalle de planta |
| `/api/v1/sensor-data/` | POST | `` | Ingesta M2M |
| `/api/v1/sensor-data/batch/` | POST | `` | Lote de lecturas |
| `/api/v1/chat/fallback/` | POST | `` | Chat RAG |
| `/api/v1/diagnostics/` | POST | `` | Diagnóstico de IA |
| `/api/v1/feedback/` | POST | `` | Feedback de usuario |
| `/api/v1/health/` | GET | `` | Health check |

### 5.2 MS1 Vision — Puerto 8001

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/api/v1/vision/analyze` | POST | Análisis de planta |
| `/api/v1/vision/analyze-ph-strip` | POST | Análisis de pH |
| `/api/v1/vision/health` | GET | Health check |

### 5.3 MS2 Chat — Puerto 8002

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/api/v1/mole-ai/chat` | POST | Motor RAG principal |
| `/api/v1/knowledge/ingest-pdf` | POST | Ingestar documento |
| `/api/v1/knowledge/pdf/{doc_id}` | DELETE | Eliminar documento |
| `/api/v1/health` | GET | Health check |

### 5.4 MS3 Reports — Puerto 8003

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/api/v1/reports/generate` | POST | Generar reporte |
| `/api/v1/reports/{job_id}/status` | GET | Estado del job |
| `/api/v1/reports/{job_id}/download` | GET | Descargar reporte |

---

## 6. Dependencias Externas

| Servicio | Propósito | Variables de Entorno |
|----------|-----------|---------------------|
| Supabase | Auth, Database | `SUPABASE_URL`, `SUPABASE_JWT_SECRET` |
| HuggingFace | Modelos de IA | `HUGGINGFACE_API_KEY` |
| MinIO | Almacenamiento S3 | `SUPABASE_S3_*` |

---

## 7. Notas de Implementación

### 7.1 Autenticación Híbrida

El sistema soporta dos mecanismos:
1. **Local:** Username/password → JWT local generado con `SECRET_KEY`
2. **Supabase:** Bearer token → Validado contra `SUPABASE_JWT_SECRET`

### 7.2 Cola de Tareas Celery

| Cola | Tareas | Worker |
|------|--------|--------|
| `default` | `cleanup_temp_files`, `refresh_admin_stats_task` | `django_celery_worker` |
| `vision_queue` | `analyze_vision_async`, `train_vision_async` | `django_celery_worker` |
| `reports_queue` | `generate_report_task` | `ms3_celery_worker` |

### 7.3 Bases de Datos

- **Desarrollo:** SQLite (`DEBUG=True`)
- **Producción:** PostgreSQL con pgvector (`DEBUG=False`)