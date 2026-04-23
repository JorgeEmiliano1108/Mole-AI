# databaseCONTEXT.md — Mole.AI v2.0 — Auditoría de Capa de Datos

> **Fecha:** 2026-04-23
> **Versión código analizada:** codebase actual (sin suposiciones)
> **Alcance:** `core_backend/` + `microservices/`

---

## 1. DICCIÓN DE TABLAS Y MODELOS

### `auth_users` — User (AbstractUser)

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | INTEGER | SI | NO | PK hereda de AbstractUser |
| username | VARCHAR(150) | | NO | USERNAME_FIELD |
| email | VARCHAR(254) | | NO | REQUIRED_FIELDS |
| password | VARCHAR(128) | | NO | hashed |
| supabase_uid | VARCHAR(255) | | SI | UNIQUE |
| supabase_role | VARCHAR(50) | | NO | DEFAULT 'authenticated' |
| supabase_app_metadata | JSONB | | NO | default={} |
| supabase_user_metadata | JSONB | | NO | default={} |
| avatar_url | URL | | SI | |
| phone_number | VARCHAR(20) | | SI | |
| is_premium | BOOLEAN | | NO | DEFAULT FALSE |
| subscription_expires | TIMESTAMP | | SI | |
| data_consent | BOOLEAN | | NO | DEFAULT FALSE — LFPDPPP |
| data_consent_date | TIMESTAMP | | SI | |
| is_email_verified | BOOLEAN | | NO | DEFAULT FALSE — NOM-024 |
| email_verification_token | VARCHAR(64) | | SI | |
| email_verification_sent_at | TIMESTAMP | | SI | |
| created_at | TIMESTAMP | | NO | auto_now_add |
| updated_at | TIMESTAMP | | NO | auto_now |

**Relaciones salientes (todas `ON DELETE SET NULL`):**
- `user_plants.user` → `auth_users.id`
- `ai_diagnostics.user` → `auth_users.id`
- `feedback_tickets.user` → `auth_users.id`
- `diagnosticos_geolocalizados.user` → `auth_users.id`
- `llm_requests.user` → `auth_users.id`
- `cnn_inferences.user` → `auth_users.id`

---

### `user_plants` — UserPlant

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | UUID | SI | | NO | default=uuid.uuid4 |
| user_id | INTEGER | | → auth_users.id | SI | SET_NULL |
| species_id | UUID | | → species_catalog.id | SI | SET_NULL |
| nickname | TEXT | | | SI | |
| created_at | TIMESTAMP | | | NO | auto_now_add |

**Índices:** `ordering = ['-created_at']`

---

### `species_catalog` — SpeciesCatalog

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | UUID | SI | NO | default=uuid.uuid4 |
| scientific_name | TEXT | | NO | |
| common_name | TEXT | | SI | |
| ideal_humidity_min | FLOAT | | SI | |
| ideal_humidity_max | FLOAT | | SI | |
| ideal_temp_min | FLOAT | | SI | |
| ideal_temp_max | FLOAT | | SI | |
| image_url | TEXT | | SI | |
| ideal_ph_min | FLOAT | | SI | |
| ideal_ph_max | FLOAT | | SI | |
| ideal_ph_optimal | FLOAT | | SI | |
| description | TEXT | | SI | |
| is_protected_nom059 | BOOLEAN | | NO | DEFAULT FALSE — NOM-059-SEMARNAT |
| protection_category | VARCHAR(20) | | SI | choices: P, T, Pr |

---

### `favorite_plants` — FavoritePlant

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | BIGSERIAL | SI | | NO | |
| user_id | INTEGER | | → auth_users.id | NO | CASCADE |
| plant_id | UUID | | → user_plants.id | NO | CASCADE |
| created_at | TIMESTAMP | | | NO | auto_now_add |

**Constraint:** UNIQUE(user_id, plant_id)

---

### `sensor_logs` — SensorLog

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | BIGSERIAL | SI | NO | |
| plant_id | UUID | | NO | db_index=True — SIN FK constraint |
| recorded_at | TIMESTAMP | | NO | db_index=True, default=timezone.now |
| soil_humidity | FLOAT | | SI | db_index=True |
| air_humidity | FLOAT | | SI | |
| air_temperature | FLOAT | | SI | db_index=True |
| uv_index | FLOAT | | SI | db_index=True |
| light_level | FLOAT | | SI | |
| ph_level | FLOAT | | SI | db_index=True — CNN-inferred |

**Índices:** compuesto `[plant_id, recorded_at]`
**Ordenamiento:** `ordering = ['-recorded_at']`
**Nota:** `plant_id` no tiene FK constraint a `user_plants` — los logs persisten aunque se borre la planta.

---

### `ai_diagnostics` — AIDiagnostic

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | UUID | SI | | NO | default=uuid.uuid4 |
| user_id | INTEGER | | → auth_users.id | SI | SET_NULL |
| plant_id | UUID | | | NO | db_index=True |
| analyzed_at | TIMESTAMP | | | NO | db_index=True, default=timezone.now |
| image_path | TEXT | | | SI | referencia MinIO |
| diagnosis_label | TEXT | | | SI | |
| confidence_score | FLOAT | | | SI | |
| metadata | JSONB | | | SI | |

**Índices:** `ordering = ['-analyzed_at']`
**Propiedades computed:** `severity`, `condition_name`, `condition_description`, `created_at`

---

### `diagnosticos_geolocalizados` — DiagnosticoGeolocalizado

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | BIGSERIAL | SI | | NO | |
| diagnostic_id | INTEGER | | → ai_diagnostics.id | SI | SET_NULL |
| user_id | INTEGER | | → auth_users.id | SI | SET_NULL |
| condition_name | VARCHAR(200) | | | NO | blank |
| latitude | FLOAT | | | SI | db_index=True |
| longitude | FLOAT | | | SI | db_index=True |
| severity | VARCHAR(10) | | | NO | choices: low/medium/high/critical |
| metadata | JSONB | | | NO | default={} |
| created_at | TIMESTAMP | | | NO | auto_now_add |

**Índices:** `ordering = ['-created_at']`

---

### `botanical_knowledge` — BotanicalKnowledge

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | BIGSERIAL | SI | NO | |
| content | TEXT | | SI | |
| source_url | TEXT | | SI | |
| chunk_metadata | JSONB | | SI | |
| embedding | VECTOR(1536) | | SI | pgvector |

---

### `llm_requests` — LLMRequest

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | BIGSERIAL | SI | | NO | |
| user_id | INTEGER | | → auth_users.id | SI | SET_NULL |
| session_id | VARCHAR(100) | | | NO | db_index=True |
| request_type | VARCHAR(30) | | | NO | choices |
| prompt | TEXT | | | NO | |
| context | JSONB | | | NO | default={} |
| model_name | VARCHAR(50) | | | NO | |
| temperature | FLOAT | | | NO | default=0.7 |
| max_tokens | INTEGER | | | NO | default=1000 |
| response | TEXT | | | NO | blank |
| response_metadata | JSONB | | | NO | default={} |
| token_usage | JSONB | | | NO | default={} |
| processing_time_ms | INTEGER | | | NO | |
| status | VARCHAR(20) | | | NO | choices |
| error_message | TEXT | | | NO | blank |
| user_rating | INTEGER | | | SI | 1-5 |
| feedback | TEXT | | | NO | blank |
| created_at | TIMESTAMP | | | NO | auto_now_add |
| updated_at | TIMESTAMP | | | NO | auto_now |
| completed_at | TIMESTAMP | | | SI | |

**Índices:** `[user, created_at]`, `[session_id, created_at]`, `[request_type, status]`
**Ordenamiento:** `ordering = ['-created_at']`

---

### `cnn_inferences` — CNNInference

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | BIGSERIAL | SI | | NO | |
| user_id | INTEGER | | → auth_users.id | SI | SET_NULL |
| request_id | VARCHAR(100) | | | NO | db_index=True |
| image_url | URL | | | NO | |
| image_metadata | JSONB | | | NO | default={} |
| model_type | VARCHAR(30) | | | NO | choices |
| model_name | VARCHAR(50) | | | NO | |
| model_version | VARCHAR(20) | | | NO | |
| image_size | JSONB | | | NO | default={} |
| preprocessing_steps | JSONB | | | NO | default=[] |
| predictions | JSONB | | | NO | default=[] |
| confidence_scores | JSONB | | | NO | default=[] |
| top_prediction | JSONB | | | NO | default={} |
| features_vector | VECTOR(512) | | | SI | pgvector |
| embedding_vector | VECTOR(1536) | | | SI | pgvector |
| inference_time_ms | INTEGER | | | NO | |
| memory_usage_mb | FLOAT | | | SI | |
| status | VARCHAR(20) | | | NO | choices |
| error_message | TEXT | | | NO | blank |
| human_verified | BOOLEAN | | | NO | DEFAULT FALSE |
| human_prediction | JSONB | | | NO | default={} |
| verification_accuracy | FLOAT | | | SI | |
| created_at | TIMESTAMP | | | NO | auto_now_add |
| updated_at | TIMESTAMP | | | NO | auto_now |
| completed_at | TIMESTAMP | | | SI | |

**Índices:** `[user, created_at]`, `[model_type, status]`, `[request_id]`

---

### `model_performance` — ModelPerformance

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | BIGSERIAL | SI | NO | |
| model_name | VARCHAR(50) | | NO | |
| model_category | VARCHAR(20) | | NO | choices |
| model_version | VARCHAR(20) | | NO | |
| accuracy | FLOAT | | SI | |
| precision | FLOAT | | SI | |
| recall | FLOAT | | SI | |
| f1_score | FLOAT | | SI | |
| auc_score | FLOAT | | SI | |
| avg_response_time_ms | FLOAT | | NO | |
| p95_response_time_ms | FLOAT | | NO | |
| p99_response_time_ms | FLOAT | | NO | |
| avg_memory_usage_mb | FLOAT | | NO | |
| peak_memory_usage_mb | FLOAT | | NO | |
| cpu_usage_percent | FLOAT | | NO | |
| total_requests | INTEGER | | NO | default=0 |
| successful_requests | INTEGER | | NO | default=0 |
| failed_requests | INTEGER | | NO | default=0 |
| metrics_date | DATE | | NO | |
| metrics_hour | INTEGER | | SI | |
| created_at | TIMESTAMP | | NO | auto_now_add |
| updated_at | TIMESTAMP | | NO | auto_now |

**UNIQUE:** (model_name, model_version, metrics_date, metrics_hour)
**Índices:** [model_category, metrics_date], [model_name, metrics_date]

---

### `ai_model_configurations` — AIModelConfiguration

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | BIGSERIAL | SI | NO | |
| model_name | VARCHAR(50) | | NO | UNIQUE |
| model_type | VARCHAR(20) | | NO | choices |
| model_version | VARCHAR(20) | | NO | |
| description | TEXT | | NO | blank |
| parameters | JSONB | | NO | default={} |
| default_settings | JSONB | | NO | default={} |
| min_memory_mb | INTEGER | | NO | |
| recommended_memory_mb | INTEGER | | NO | |
| gpu_required | BOOLEAN | | NO | DEFAULT FALSE |
| gpu_memory_mb | INTEGER | | SI | |
| endpoint_url | URL | | NO | blank |
| api_key_required | BOOLEAN | | NO | DEFAULT FALSE |
| rate_limit_per_minute | INTEGER | | NO | default=60 |
| is_active | BOOLEAN | | NO | DEFAULT TRUE |
| is_production_ready | BOOLEAN | | NO | DEFAULT FALSE |
| health_check_url | URL | | NO | blank |
| last_health_check | TIMESTAMP | | SI | |
| created_at | TIMESTAMP | | NO | auto_now_add |
| updated_at | TIMESTAMP | | NO | auto_now |

**Índices:** [model_type, is_active], [is_production_ready]

---

### `feedback_tickets` — FeedbackTicket

| Campo | Tipo DB | PK | FK | Nullable | Notas |
|---|---|---|---|---|---|
| id | BIGSERIAL | SI | | NO | |
| user_id | INTEGER | | → auth_users.id | SI | SET_NULL |
| topic | VARCHAR(20) | | | NO | bug/suggestion/ai_error/other |
| message | TEXT | | | NO | |
| status | VARCHAR(20) | | | NO | open/in_progress/closed |
| created_at | TIMESTAMP | | | NO | auto_now_add |

**Ordenamiento:** `ordering = ['-created_at']`

---

### `audit_logs` — AuditLog

| Campo | Tipo DB | PK | Nullable | Notas |
|---|---|---|---|---|
| id | BIGSERIAL | SI | NO | |
| user_id | INTEGER | | SI | |
| action | VARCHAR(255) | | NO | |
| timestamp | TIMESTAMP | | NO | auto_now_add |
| ip_address | GenericIPAddress | | SI | |
| details | TEXT | | NO | blank |

**Ordenamiento:** `ordering = ['-timestamp']`
**RESTRICCIONES INMUTABLES (a nivel app):**
- `save()`: lanza `PermissionError` si `pk is not None` (append-only)
- `delete()`: lanza `PermissionError` (no se puede borrar)

---

## 2. MAPEO DE ENDPOINTS A BASE DE DATOS

### 2.1 Telemetría IoT

#### `POST /api/v1/sensor-data/` → `sensor_data_view`
**Auth:** `HardwareAPIKeyAuthentication` + `HardwareOnlyPermission`
**Throttle:** `SensorDataThrottle`
**Payload JSON:**
```json
{
  "plant_id": "UUID",
  "recorded_at": "ISO8601 (opcional)",
  "soil_humidity": 45.5,
  "air_humidity": 60.0,
  "air_temperature": 25.0,
  "uv_index": 3.5,
  "light_level": 800.0,
  "ph_level": 6.5
}
```
**Validaciones:**
- Serializer `SensorReadingSerializer` valida: al menos 1 sensor presente
- `ph_level`: 0.0 ≤ valor ≤ 14.0
- `recorded_at`: anti-replay ±65s del reloj UTC (ETSI EN 303 645)
- Verifica `UserPlant.objects.filter(id=plant_id).exists()` → 404 si no existe

**Acción DB:** `INSERT INTO sensor_logs (plant_id, recorded_at, soil_humidity, air_temperature, uv_index, light_level, ph_level)`
**Respuesta:** `{"status": "success", "registered": 1}` (201)

---

#### `POST /api/v1/sensor-data/batch/` → `sensor_batch_view`
**Auth:** `HardwareAPIKeyAuthentication` + `HardwareOnlyPermission`
**Payload JSON:**
```json
{
  "batch": [
    { "plant_id": "UUID", "recorded_at": "ISO8601", "soil_humidity": 45.5, ... }
  ]
}
```
**Validaciones:** 1 ≤ len(batch) ≤ 500; sin anti-replay (Store-and-Forward)
**Acción DB:** `SensorLog.objects.bulk_create(logs)` — bulk INSERT

---

#### `POST /api/v1/sensors/ingest` → `sensors_ingest_view`
**Auth:** `SupabaseAuthentication` + `IsAuthenticated` (JWT — Zero-Trust)
**Async:** sí (ASGI)
**Payload:** idéntico a `sensor_data_view`
**Validaciones:** anti-replay ±300s
**Acción DB:** `INSERT INTO sensor_logs` (equivalente a sensor_data_view)

---

#### `PATCH /api/v1/sensor-data/<int:pk>/` → `sensor_data_patch_view`
**Auth:** `HardwareAPIKeyAuthentication` + `HardwareOnlyPermission`
**Payload JSON:**
```json
{ "ph_level": 6.8 }
```
**Validaciones:** `ph_level` ∈ [0.0, 14.0]; al menos 1 campo
**Acción DB:** `UPDATE sensor_logs SET ph_level=X WHERE id=pk`

---

#### `GET /api/v1/telemetry/latest/?plant_id=<uuid>` → `telemetry_latest_view`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT * FROM sensor_logs WHERE plant_id=? ORDER BY recorded_at DESC LIMIT 1`
**Verificación:** `UserPlant.objects.get(id=plant_id, user=request.user)` → 404 si no pertenece

---

### 2.2 Plantas

#### `POST /api/v1/plants/` → `plant_list_view` (POST)
**Auth:** `IsAuthenticated`
**Payload JSON:**
```json
{ "nickname": "Mi tomate", "species_id": "UUID" }
```
**Acción DB:** `INSERT INTO user_plants (user_id, species_id, nickname, created_at)`
**Respuesta:** `{"status": "created", "plant_id": "UUID", ...}`

---

#### `GET /api/v1/plants/` → `plant_list_view` (GET)
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT * FROM user_plants WHERE user_id=?`

---

#### `GET /api/v1/plants/<uuid:plant_id>/` → `plant_detail_view`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT * FROM user_plants WHERE id=? AND user_id=?`
**Métodos:** GET / PATCH / DELETE

---

#### `PATCH /api/v1/plants/<uuid:plant_id>/`
**Payload JSON:** `{"nickname": "...", "species_id": "UUID"}`
**Acción DB:** `UPDATE user_plants SET ... WHERE id=? AND user_id=?`

---

#### `DELETE /api/v1/plants/<uuid:plant_id>/`
**Acción DB:** `DELETE FROM user_plants WHERE id=? AND user_id=?`

---

#### `GET /api/v1/plants/my-collection/`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT * FROM user_plants WHERE user_id=?`

---

#### `GET /api/v1/plants/search/?q=<nombre>` → `species_search_view`
**Auth:** AllowAny (público)
**Acción DB:** `SELECT * FROM species_catalog WHERE scientific_name ILIKE '%q%' OR common_name ILIKE '%q%' LIMIT 1`
**Respuesta:** ficha pública + advertencia NOM-059 si `is_protected_nom059=True`

---

#### SpeciesViewSet (DefaultRouter — CRUD)
| Método | Endpoint | Auth | Acción DB |
|---|---|---|---|
| GET | `/api/v1/plants/species/` | AllowAny | `SELECT * FROM species_catalog` |
| POST | `/api/v1/plants/species/` | Staff/Superuser | `INSERT INTO species_catalog` |
| GET | `/api/v1/plants/species/<id>/` | AllowAny | `SELECT * FROM species_catalog WHERE id=?` |
| PATCH | `/api/v1/plants/species/<id>/` | Staff/Superuser | `UPDATE` |
| DELETE | `/api/v1/plants/species/<id>/` | Staff/Superuser | `DELETE` |

---

#### `GET /api/v1/plants/favorites/` → `favorite_plant_list_view`
**Auth:** `IsAuthenticated`
**GET:** `SELECT * FROM favorite_plants WHERE user_id=?`
**POST:** `INSERT INTO favorite_plants (user_id, plant_id, created_at)`

#### `DELETE /api/v1/plants/favorites/<int:fav_id>/` → `favorite_plant_detail_view`
**Auth:** `IsAuthenticated`
**Acción DB:** `DELETE FROM favorite_plants WHERE id=? AND user_id=?`

---

### 2.3 IA y Diagnósticos

#### `POST /api/v1/diagnostics/` → `diagnostic_view`
**Auth:** `IsAuthenticated`
**Input:** `multipart/form-data`
```json
{
  "plant_id": "UUID (opcional)",
  "model_type": "disease_detection|plant_identification|pest_detection|nutrient_deficiency|growth_stage",
  "image": "<binario>"
}
```
**Validaciones de imagen (Serializer):**
- Tamaño ≤ 10MB
- Content-type: image/jpeg, image/png, image/webp
- Magic bytes: `\xff\xd8\xff` (JPEG), `\x89PNG\r\n\x1a\n` (PNG), `RIFF...WEBP` (WebP)
- Rechaza si contiene `MZ` o `\x7fELF`

**Acción DB:** invoca `consultar_phi_vision()` → mole_vision (microbial)
**Respuesta:** `{"status": "success", "analysis": "..."}`

---

#### `GET /api/v1/diagnostics/history/`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT id, plant_id, diagnosis_label, analyzed_at FROM ai_diagnostics WHERE user_id=? ORDER BY analyzed_at DESC LIMIT 20`

---

#### `GET /api/v1/diagnostics/<uuid:id>/download/`
**Auth:** `IsAuthenticated`
**Acción DB:** consulta `AIDiagnostic` por id → `generate_diagnostic_pdf(id)` → PDF

---

### 2.4 Mapas y Geolocalización

#### `GET /api/v1/map/hotspots/`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT latitude, longitude, severity FROM diagnosticos_geolocalizados LIMIT 100`
**Respuesta:** `{"hotspots": [{"lat": ..., "lng": ..., "severity": "..."}]}`

#### `GET /api/v1/diagnosticos/geolocalizados/`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT id, condition_name FROM diagnosticos_geolocalizados WHERE user_id=? LIMIT 50`

#### `POST /api/v1/diagnosticos/geolocalizados/create/`
**Auth:** `IsAuthenticated`
**Stub:** retorna 201 sin escribir en BD (implementación pendiente)

---

### 2.5 Chat y RAG

#### `POST /api/v1/chat/fallback/` → `chat_fallback_view`
**Auth:** `IsAuthenticated`
**Throttle:** `LLMChatThrottle`
**Payload JSON:**
```json
{ "question": "texto de pregunta" }
```
**Acción DB (implícita):** `MoleAIClient.generate_chat_response()` → RAG con embeddings
**Respuesta:** `{"answer": "...", "disclaimer": "..."}`

#### `GET /api/v1/chat/history/`
**Auth:** `IsAuthenticated`
**Acción DB:** `SELECT prompt, response FROM llm_requests WHERE user_id=? ORDER BY created_at DESC LIMIT 50`

---

### 2.6 Feedback

#### `POST /api/v1/feedback/` → `feedback_create_view`
**Auth:** `IsAuthenticated`
**Payload JSON:**
```json
{ "topic": "bug|suggestion|ai_error|other", "message": "texto (10-5000 chars)" }
```
**Acción DB:** `INSERT INTO feedback_tickets (user_id, topic, message, status, created_at)`
**Respuesta:** serializer `FeedbackTicketResponseSerializer`

---

### 2.7 Microservicio mole_vision (FastAPI)

#### `POST /api/v1/vision/analyze`
**Auth:** JWT (get_current_user dependency)
**Input:** `image_bytes` via `Depends(get_image_file)`
**Acción:** `AnalyzePlantUseCase.execute()` → CNN (TFLite) + Redis event publish
**Output schema:**
```json
{
  "id": "string",
  "plant_id": "string",
  "species": "string",
  "condition": "string",
  "condition_category": "healthy|disease|nutrient_deficiency|pest|environmental_stress|unknown",
  "severity": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "ph_predicted": 0.0-14.0,
  "timestamp": "ISO8601",
  "disclaimer": "Aviso: Diagnóstico IA..."
}
```

#### `POST /api/v1/vision/analyze-ph-strip`
**Auth:** JWT
**Input:** `image_bytes`
**Acción:** `ColorimetricAdapter.estimate_ph()` — Euclidean RGB
**Output:** `{"estimated_ph": 6.5, "method": "Colorimetry_Euclidean_RGB", "disclaimer": "..."}`

#### `GET /api/v1/vision/health` / `healthz`
**Auth:** ninguna
**Acción:** verifica TFLite model loaded + Redis health

---

### 2.8 Microservicio mole_chat (FastAPI)

#### `POST /api/v1/mole-ai/chat`
**Auth:** JWT
**Payload JSON:**
```json
{ "user_id": "string", "message": "string" }
```
**Validación Zero-Trust:** `request.user_id != current_user_id` → 403
**Acción:** `MoleAIChatUseCase.ainvoke()` → RAG FAISS embeddings
**Output:** `{"respuesta": "...", "sources": [...], "disclaimer": "COFEPRIS..."}`

#### `POST /api/v1/knowledge/ingest-pdf`
**Auth:** JWT
**Input:** multipart/form-data (PDF)
**Validaciones:** extensión `.pdf` obligatoria
**Acción:** `FAISSVectorStore.ingest_pdf()` → vectoriza chunks → embeddings en FAISS
**Output:** `{"success": true, "doc_id": "...", "message": "..."}`

#### `DELETE /api/v1/knowledge/pdf/<doc_id>`
**Auth:** JWT
**Acción:** `FAISSVectorStore.delete_pdf_by_id()` → elimina del índice vectorial
**Output:** `{"success": true, "message": "..."}`

---

### 2.9 Microservicio mole_report (FastAPI)

#### `POST /api/v1/reports/generate`
**Auth:** JWT (Supabase)
**Payload JSON:**
```json
{ "date_range_days": 90, "sensors": [] }
```
**Acción DB:** `JobMetadataStore.create_job()` → encola Celery `generate_report_task`
**Acción DB (Redis):** hash de user_id en metadata (LFPDPPP — no se almacena UID real)
**Output:** `{"job_id": "UUID", "status": "queued"}`

#### `GET /api/v1/reports/{job_id}/status`
**Auth:** JWT
**Validación:** `hashed_user_id` en token debe coincidir con `hashed_user_id` del job
**Acción DB (Redis):** `JobMetadataStore.get_job(job_id)`

#### `GET /api/v1/reports/{job_id}/download`
**Auth:** JWT
**Validación:** ownership check + `status == "SUCCESS"`
**Acción DB (Redis):** consulta `pdf_s3_path`
**Output:** `{"download_url": "/static/reports/{job_id}.pdf"}`

---

## 3. FLUJOS DE DATOS COMPLEJOS (Data Lineage)

### 3.1 Flujo Telemetría IoT (ESP32 → BD)

```
ESP32
  │
  │ POST /api/v1/sensor-data/
  │ HardwareAPIKeyAuthentication
  ▼
┌─────────────────────┐
│ SensorReading       │
│ Serializer          │
│ ├─ Al menos 1 sensor?│
│ ├─ ph_level [0,14]   │────────── Error 400
│ └─ recorded_at ±65s  │────────── Error 403 (anti-replay)
│     (ETSI EN 303 645)│
└──────────┬──────────┘
           │ validated_data
           ▼
┌─────────────────────┐
│ sensor_data_view    │
│ ├─ UserPlant.exists()│
│ │   (plant_id válido?)│─── Error 404
│ └─ SensorLog.create()│
└──────────┬──────────┘
           │
           ▼
    INSERT sensor_logs
    (plant_id, recorded_at,
     soil_humidity, air_temp,
     uv_index, light_level, ph_level)
```

**Variante batch:** mismo flujo con `bulk_create()` — sin anti-replay, Store-and-Forward.
**PATCH asíncrono (Two-Stream Merge):** mole_vision → `PATCH /api/v1/sensor-data/<id>/` → actualiza `ph_level` en `sensor_logs`.

---

### 3.2 Flujo IA/Visión (Imagen → pgvector + MinIO)

```
Frontend/Mobile
  │
  │ multipart POST /api/v1/diagnostics/
  │ IsAuthenticated (JWT)
  ▼
┌─────────────────────────┐
│ DiagnosticRequestSerializer │
│ ├─ image.size ≤ 10MB    │─────── Error 400
│ ├─ content-type          │─────── Error 400
│ ├─ Magic bytes (OWASP)  │─────── Error 400
│ └─ MZ/ELF signature     │─────── Error 400
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ consultar_phi_vision()   │
│ → mole_vision microservice│
│ POST /api/v1/vision/     │
│   analyze                │
└──────────┬──────────────┘
           │ image_bytes
           ▼
┌─────────────────────────┐
│ AnalyzePlantUseCase     │
│ ├─ TFLite CNN inference │
│ ├─ DiagnosticResult      │
│ │   (species, condition,│
│ │    severity, ph_pred) │
│ └─ Redis event publish   │
└──────────┬──────────────┘
           │
           │ event
           ▼
┌─────────────────────────┐
│ RedisEventPublisher     │
│ → diagnostico_geoloc    │
│   (INSERT en BD)        │
└─────────────────────────┘

── Vectores (pgvector) ──

Tabla: cnn_inferences
  ├─ features_vector   → VECTOR(512) — CNN features extraídos
  └─ embedding_vector  → VECTOR(1536) — CLIP embeddings de imagen

Tabla: botanical_knowledge
  └─ embedding → VECTOR(1536) — chunks de manuales PDF (RAG)

── MinIO ──
  └─ image_path en ai_diagnostics → referencia blob en MinIO
     (imagen original almacenada como objeto MinIO)
```

---

### 3.3 Flujo Auth / LFPDPPP / ARCO

```
Registro
  ├─ POST /auth/signup (Supabase)
  └─ INSERT auth_users
       ├─ supabase_uid ────────────，唯一
       ├─ data_consent ──────────── DEFAULT FALSE
       ├─ data_consent_date ─────── NULL
       ├─ is_email_verified ─────── DEFAULT FALSE
       └─ created_at

Borrado de usuario (Anonymization/Borrado en cascada)
  └─ ON DELETE SET_NULL en todas las FK:
       ├─ ai_diagnostics.user_id ────→ NULL
       ├─ feedback_tickets.user_id ───→ NULL
       ├─ diagnosticos_geolocalizados.user_id → NULL
       ├─ llm_requests.user_id ───────→ NULL
       ├─ cnn_inferences.user_id ────→ NULL
       └─ user_plants.user_id ─────────→ NULL (planta huérfana)

sensor_logs: plant_id NO tiene FK constraint — logs persisten tras borrar usuario
botanical_knowledge: sin FK a usuario — datos RAG no se borran en cascada
AuditLog: inmutable — delete() lanza PermissionError
```

---

## 4. RESUMEN DE RELACIONES

```
auth_users (1)───(*) user_plants
auth_users (1)───(*) ai_diagnostics
auth_users (1)───(*) llm_requests
auth_users (1)───(*) cnn_inferences
auth_users (1)───(*) feedback_tickets
auth_users (1)───(*) diagnosticos_geolocalizados
auth_users (1)───(*) favorite_plants

user_plants (1)───(1) species_catalog

user_plants.id (UUID) ═══ sensor_logs.plant_id (UUID, sin FK constraint)

ai_diagnostics (1)───(*) diagnosticos_geolocalizados

favorite_plants: M2M user ↔ user_plants

── pgvector ──
botanical_knowledge.embedding → Vector(1536) → FAISS index (mole_chat)
cnn_inferences.features_vector → Vector(512)
cnn_inferences.embedding_vector → Vector(1536)

── MinIO ──
ai_diagnostics.image_path → blob en MinIO
```

---

## 5. NOTAS TÉCNICAS PARA EL EQUIPO DE BD

| # | Tema | Detalle |
|---|---|---|
| 1 | pgvector obligatorio | `VectorField` en `botanical_knowledge`, `cnn_inferences` requiere extensión `CREATE EXTENSION vector` |
| 2 | FK orphan en sensor_logs | `plant_id` es UUID puro sin constraint — logs sobreviven al borrado de planta/usuario |
| 3 | AuditLog inmutable | `save()` y `delete()` overriden a nivel app — considerar constraint DB (READ ONLY) |
| 4 | Límite batch: 500 | `SensorBatchSerializer` valida `max_length=500` |
| 5 | MinIO | imágenes de diagnóstico almacenadas como blobs — `image_path` es la referencia |
| 6 | Sensitive JSONB | `supabase_app_metadata`, `supabase_user_metadata` en `auth_users` contienen datos de identidad Supabase |
| 7 | Token usage | `llm_requests.token_usage` es JSONB — puede crecer con `usage.total_tokens`, etc. |
| 8 | NOM-059 | `species_catalog.is_protected_nom059` y `protection_category` — cumplimiento legal de flora mexicana |
| 9 | LFPDPPP | `auth_users.data_consent` debe ser TRUE antes de procesar datos personales |
| 10 | Redis job store | `mole_report` usa Redis para metadata de jobs — no guarda user_id real, solo hash |
| 11 | FavoritePlant CASCADE | `ON DELETE CASCADE` — al borrar usuario o planta se eliminan favoritos relacionados |
| 12 | SpeciesViewSet | CRUD completo — writes restringidos a staff/superuser |