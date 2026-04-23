# Mole.AI v2.0 — Backend Audit Report

**Fecha de Auditoría:** 2026-04-22
**Versión del Sistema:** 2.0.0
**Auditoría:** Arquitectura Forense de Código Backend

---

## 1. Auditoría de Enrutamiento y Vistas

### 1.1 Orquestador Django (core_backend/)

#### `mole_ai_backend/urls.py` — Mapa de Rutas Principal

| Prefijo | Include | Estado | Observaciones |
|---------|---------|--------|---------------|
| `admin/` | Django Admin | ✅ VIGENTE | Admin panel estándar |
| `api/v1/auth/` | `apps.authentication.urls` | ✅ VIGENTE | Gestión de auth |
| `api/v1/ai/` | `apps.ai_models.urls` | ✅ VIGENTE | Endpoints de IA |
| `api/v1/` (vacío) | `apps.core.urls` | ✅ VIGENTE | Telemetría y sistema |
| `api/v1/plants/` | `apps.plants.urls` | ✅ VIGENTE | Flora y colección |
| `api/schema/` | SpectacularAPIView | ✅ VIGENTE | OpenAPI |
| `api/docs/` | SpectacularSwaggerView | ✅ VIGENTE | Swagger UI |

#### `apps/core/urls.py` — Rutas del Módulo Core

| Ruta | Vista | Método | Permiso | Estado |
|------|-------|--------|---------|--------|
| `sensor-data/` | `sensor_data_view` | POST | HardwareOnly | ✅ VIGENTE |
| `sensor-data/batch/` | `sensor_batch_view` | POST | HardwareOnly | ✅ VIGENTE |
| `sensor-data/<int:pk>/` | `sensor_data_patch_view` | PATCH | HardwareOnly | ✅ VIGENTE |
| `sensor-data/latest/` | `mock_sensor_data` | GET | AllowAny | ⚠️ PLACEHOLDER |
| `telemetry/latest/` | `telemetry_latest_view` | GET | IsAuthenticated | ✅ VIGENTE |
| `sensors/ingest` | `sensors_ingest_view` | POST | JWT | ✅ VIGENTE |
| `sensor-logs/` | `sensor_log_view` | POST | IsAuthenticated | ⚠️ PLACEHOLDER |
| `diagnostics/` | `diagnostic_view` | POST | IsAuthenticated | ✅ VIGENTE |
| `diagnostics/history/` | `diagnostic_history_view` | GET | IsAuthenticated | ✅ VIGENTE |
| `diagnostics/<uuid:id>/download/` | `download_diagnostic_pdf` | GET | IsAuthenticated | ✅ VIGENTE |
| `map/hotspots/` | `map_hotspots_view` | GET | IsAuthenticated | ✅ VIGENTE |
| `diagnosticos/geolocalizados/` | `diagnosticos_geolocalizados_list` | GET | IsAuthenticated | ✅ VIGENTE |
| `diagnosticos/geolocalizados/create/` | `diagnosticos_geolocalizados_create` | POST | IsAuthenticated | ✅ VIGENTE |
| `plant-knowledge/` | `plant_knowledge_view` | GET | IsAuthenticated | ⚠️ PLACEHOLDER |
| `llm/chat/` | `llm_chat_view` | POST | IsAuthenticated | ⚠️ PLACEHOLDER |
| `chat/fallback/` | `chat_fallback_view` | POST | IsAuthenticated | ✅ VIGENTE |
| `chat/history/` | `chat_history_view` | GET | IsAuthenticated | ✅ VIGENTE |
| `health/` | `health_check_view` | GET | AllowAny | ✅ VIGENTE |
| `fichas/` | `fichas_public_view` | GET | AllowAny | ⚠️ PLACEHOLDER |
| `history/` | `consolidated_history_view` | GET | IsAuthenticated | ⚠️ PLACEHOLDER |
| `feedback/` | `feedback_create_view` | POST | IsAuthenticated | ✅ VIGENTE |

#### `apps/plants/urls.py` — Rutas del Módulo Flora

| Ruta | Vista | Método | Permiso | Estado |
|------|-------|--------|---------|--------|
| `search/` | `species_search_view` | GET | AllowAny | ✅ VIGENTE |
| `my-collection/` | `my_collection_view` | GET | IsAuthenticated | ✅ VIGENTE |
| `` | `plant_list_view` | GET/POST | IsAuthenticated | ✅ VIGENTE |
| `<uuid:plant_id>/` | `plant_detail_view` | GET/PATCH/DELETE | IsAuthenticated | ✅ VIGENTE |
| `favorites/` | `favorite_plant_list_view` | GET/POST | IsAuthenticated | ⚠️ RIESGO* |
| `favorites/<int:fav_id>/` | `favorite_plant_detail_view` | DELETE | IsAuthenticated | ⚠️ RIESGO* |
| `species/` | `SpeciesViewSet` | CRUD | ReadOnly/Admin | ✅ VIGENTE |

> **RIESGO\***: La vista `favorite_plant_list_view` referencia el modelo `FavoritePlant` en la línea 160 de views.py, pero el modelo está **comentado** en plants/models.py (líneas 78-98). Esto causará `NameError` en tiempo de ejecución.

#### `apps/authentication/urls.py` — Rutas de Autenticación

| Ruta | Vista | Método | Permiso | Estado |
|------|-------|--------|---------|--------|
| `validate-token/` | `validate_token_view` | POST | AllowAny | ✅ VIGENTE |
| `register/` | `register_view` | POST | AllowAny | ✅ VIGENTE |
| `profile/` | `user_profile_view` | GET/PATCH/DELETE | IsAuthenticated | ✅ VIGENTE |
| `subscription/` | `user_subscription_view` | GET/PUT | IsAuthenticated | ✅ VIGENTE |
| `metadata/` | `user_metadata_view` | GET | IsAuthenticated | ✅ VIGENTE |
| `logout/` | `logout_view` | POST | IsAuthenticated | ✅ VIGENTE |
| `health/` | `AuthHealthCheckView` | GET | IsAuthenticated | ✅ VIGENTE |
| `debug/` | `auth_debug_view` | GET | IsAuthenticated | ✅ VIGENTE |

#### `apps/ai_models/urls.py` — Rutas de IA

| Ruta | Vista | Método | Permiso | Estado |
|------|-------|--------|---------|--------|
| `llm/requests/` | `llm_requests_view` | GET | IsAuthenticated | ⚠️ PLACEHOLDER |
| `cnn/inferences/` | `cnn_inferences_view` | GET | IsAuthenticated | ⚠️ PLACEHOLDER |
| `performance/` | `model_performance_view` | GET | IsAuthenticated | ⚠️ PLACEHOLDER |
| `config/` | `ai_model_config_view` | GET | IsAuthenticated | ⚠️ PLACEHOLDER |
| `train/rag/` | `train_rag_view` | POST | IsAdminUser | ✅ VIGENTE |
| `train/vision/` | `train_vision_view` | POST | IsAdminUser | ✅ VIGENTE |
| `health/` | `AIHealthCheckView` | GET | IsAuthenticated | ✅ VIGENTE |
| `vision/analyze/` | `analyze_vision_view` | POST | IsAuthenticated | ✅ VIGENTE |
| `vision/status/<str:task_id>/` | `vision_task_status_view` | GET | IsAuthenticated | ✅ VIGENTE |

### 1.2 Microservicios FastAPI

#### MS1 (mole_vision) — `app/api/routers.py`

| Ruta | Método | Estado | Notas |
|------|--------|--------|-------|
| `/api/v1/vision/analyze` | POST | ✅ VIGENTE | Análisis de planta |
| `/api/v1/vision/analyze-ph-strip` | POST | ✅ VIGENTE | Análisis de pH |
| `/api/v1/vision/health` | GET | ✅ VIGENTE | Health check |
| `/api/v1/vision/healthz` | GET | ✅ VIGENTE | Health check detallado |

**Ruta Nginx → MS1:** `location /api/vision/` → `http://ms1_vision:8001/api/vision/`

**Desajuste detectado:** Nginx reenvía a `/api/vision/` pero el router FastAPI espera `/api/v1/vision/`. Esto causará 404 en todas las llamadas a Vision desde el API Gateway.

#### MS2 (mole_chat) — `app/api/routers.py`

| Ruta | Método | Estado | Notas |
|------|--------|--------|-------|
| `/api/v1/mole-ai/chat` | POST | ✅ VIGENTE | Motor principal RAG |
| `/api/v1/knowledge/ingest-pdf` | POST | ✅ VIGENTE | Ingesta de documentos |
| `/api/v1/knowledge/pdf/{doc_id}` | DELETE | ✅ VIGENTE | Eliminar documento |
| `/api/v1/health` | GET | ✅ VIGENTE | Health check |

**Ruta Nginx → MS2:** `location /api/chat/` → `http://ms2_chat:8002/api/chat/`

**Desajuste detectado:** Nginx reenvía a `/api/chat/` pero el router FastAPI espera `/api/v1/mole-ai/chat` o `/api/v1/knowledge/...`. Esto causará 404 en todas las llamadas a Chat desde el API Gateway.

#### MS3 (mole_report) — `app/api/v1/reports.py`

| Ruta | Método | Estado | Notas |
|------|--------|--------|-------|
| `/api/v1/reports/generate` | POST | ✅ VIGENTE | Generar reporte |
| `/api/v1/reports/{job_id}/status` | GET | ✅ VIGENTE | Estado del job |
| `/api/v1/reports/{job_id}/download` | GET | GET | ✅ VIGENTE |

**Ruta Nginx → MS3:** `location /api/reports/` → `http://ms3_reports:8003/api/reports/`

**Desajuste detectado:** El router FastAPI tiene prefix `/api/v1/reports` pero se monta en `reports.router, prefix="/api/v1/reports"`. La combinación completa es `/api/v1/reports/api/v1/reports/generate`. Esto es un bug de doble prefix.

---

## 2. Flujo de Datos

### 2.1 Ciclo de Vida: Telemetría IoT (ESP32 → Postgres)

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌─────────────┐
│ ESP32 HW    │────▶│ Nginx (CORS) │────▶│ Django     │────▶│ Postgres    │
│ (Sensor)    │     │ :8080        │     │ :8000      │     │ :5432       │
└─────────────┘     └──────────────┘     └────────────┘     └─────────────┘
       │                                        │
       │ POST /api/v1/sensor-data/             │ SensorLog.create()
       │ + X-Hardware-Api-Key                   │ ⚠️ Anti-Replay (300s)
       │                                        │
       │                                        ▼
                              ┌────────────────────────────┐
                              │ Celery Worker (async)       │
                              │ cleanup_temp_files (daily)  │
                              └────────────────────────────┘
```

### 2.2 Ciclo de Vida: Diagnóstico de Imagen

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│ Frontend    │────▶│ Nginx        │────▶│ Django     │────▶│ Celery       │
│ (MPA)       │     │ :8080        │     │ :8000      │     │ (vision_queue)│
└─────────────┘     └──────────────┘     └────────────┘     └──────────────┘
                                                                    │
       ┌────────────────────────────────────────────────────────────┘
       │ analyze_vision_async.delay()
       ▼
┌──────────────┐     ┌────────────┐
│ MS1 Vision   │────▶│ MinIO (S3) │
│ :8001        │     │ :9000      │
└──────────────┘     └────────────┘
       │ (TFLite)
       │ CNN Inference
       ▼
┌─────────────────────────┐
│ CNNInference.create()   │
│ (guarda predicción)     │
└─────────────────────────┘
```

### 2.3 Ciclo de Vida: Chat RAG (MS2)

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│ Frontend    │────▶│ Nginx        │────▶│ Django     │────▶│ MS2 Chat     │
│ (MPA)       │     │ :8080        │     │ :8000      │     │ :8002        │
└─────────────┘     └──────────────┘     └────────────┘     └──────────────┘
       │                                                   │ (FAISS/RAG)
       │ POST /api/v1/chat/fallback                       │
       │ + JWT Bearer                                      ▼
       │                              ┌────────────────────────────┐
       │                              │ MoleAIClient (async HTTP)   │
       │                              │ LLMRequest.create()        │
       │                              │ + MoleAIServiceError        │
       │                              └────────────────────────────┘
```

### 2.4 Ciclo de Vida: Reportes Asíncronos (MS3)

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│ Frontend    │────▶│ Nginx        │────▶│ MS3 Report│────▶│ Redis        │
│ (MPA)       │     │ :8080        │     │ :8003      │     │ (job store) │
└─────────────┘     └──────────────┘     └────────────┘     └──────────────┘
       │                                                   │
       │ POST /api/reports/generate                        │ Celery Task
       │ + JWT Bearer                                      ▼
       │                              ┌────────────────────────────┐
       │                              │ ms3_celery_worker          │
       │                              │ (reports_queue)            │
       │                              │ generate_report_task()     │
       │                              └────────────────────────────┘
       │                                            │
       │                                            │ PDF + S3
       ▼                                            ▼
┌──────────────┐                          ┌─────────────────────┐
│ Descarga     │                          │ MinIO (S3)          │
│ /api/reports/│                          │ /static/reports/    │
│ {job}/download                        └─────────────────────┘
```

---

## 3. Seguridad y Cumplimiento Normativo

### 3.1 LFPDPPP (Ley Federal de Protección de Datos Personales)

| Control | Implementación | Estado | Archivo |
|---------|---------------|--------|---------|
| **Consentimiento explícito** | `User.data_consent` + `data_consent_date` | ✅ CUMPLE | `authentication/models.py:36-44` |
| **Derecho de cancelación (ARCO)** | Anonimización de PII + `user.delete()` | ✅ CUMPLE | `authentication/views.py:49-74` |
| **Anonimización** | Email → `deleted_{id}@anonimizado.mole.ai` | ✅ CUMPLE | `authentication/views.py:55` |
| **Conservación científica** | FK con `on_delete=SET_NULL` | ✅ CUMPLE | `authentication/models.py` |
| **Auditoría inmutable** | `AuditLog.delete()` prohibido | ✅ CUMPLE | `core/models.py:202-207` |
| **Hash de user_id en Celery** | `_hash_user_id()` SHA-256 | ✅ CUMPLE | `core/tasks.py:20-22` |

### 3.2 ETSI EN 303 645 (IoT Cybersecurity)

| Control | Implementación | Estado | Archivo |
|---------|---------------|--------|---------|
| **Anti-Replay (Sensor)** | Delta 300s en `sensor_data_view` | ✅ CUMPLE | `core/views.py:82-87` |
| **Anti-Replay (Batch)** | Delta 300s en `sensor_batch_view` | ✅ CUMPLE | `core/views.py:117-121` |
| **Anti-Replay (Ingest)** | Delta 300s en `sensors_ingest_view` | ✅ CUMPLE | `core/api_views.py:130-143` |
| **Hardware API Key** | `HardwareAPIKeyAuthentication` | ✅ CUMPLE | `authentication/infrastructure/` |

### 3.3 NOM-059 (Protección de Flora)

| Control | Implementación | Estado | Observación |
|---------|---------------|--------|-------------|
| **Restricción de especies** | `SpeciesCatalog` con descripción | ⚠️ INCOMPLETO | No hay validación de especie protegida |
| **Auditoría de extracción** | No implementado | ❌ NO CUMPLE | No hay logging de consultas a especies |
| **Geolocalización** | `DiagnosticoGeolocalizado` model | ✅ CUMPLE | Modelo presente |

### 3.4 MoProSoft / DevSecOps

| Control | Implementación | Estado | Archivo |
|---------|---------------|--------|---------|
| **Logs inmutables** | `AuditLog` append-only | ✅ CUMPLE | `core/models.py:182-207` |
| **Trazabilidad** | `AuditLog` con user_id, action, IP | ✅ CUMPLE | `core/models.py:188-192` |
| **Seguridad por capas** | CORS en Nginx, JWT en Django | ✅ CUMPLE | `nginx.conf`, `settings.py` |

---

## 4. Deuda Técnica

### 4.1 Código Muerto / Placeholders

| ID | Ubicación | Descripción | Severidad | Estado |
|----|-----------|-------------|-----------|--------|
| DT-001 | `core/views.py:227` | `llm_chat_view` retorna placeholder | MEDIA | ⚠️ RIESGO |
| DT-002 | `core/views.py:237` | `fichas_public_view` retorna `[]` | BAJA | ⚠️ PLACEHOLDER |
| DT-003 | `core/views.py:251` | `consolidated_history_view` retorna `[]` | BAJA | ⚠️ PLACEHOLDER |
| DT-004 | `core/views.py:256` | `plant_knowledge_view` retorna `[]` | BAJA | ⚠️ PLACEHOLDER |
| DT-005 | `core/views.py:260` | `sensor_log_view` solo retorna success | BAJA | ⚠️ PLACEHOLDER |
| DT-006 | `ai_models/views.py:37-53` | Monitoreo endpoints retornan placeholder | MEDIA | ⚠️ PLACEHOLDER |
| DT-007 | `plants/models.py:78-98` | `FavoritePlant` comentado | ALTA | ❌ RIESGO |
| DT-008 | `apps/core/domain/entities.py` | Entidades de dominio no utilizadas | BAJA | ⚠️ INCOMPLETO |

### 4.2 Problemas de Integración

| ID | Descripción | Severidad | Archivo |
|----|-------------|-----------|---------|
| INT-001 | Nginx `/api/vision/` → MS1 espera `/api/v1/vision/` | ALTA | `nginx.conf:102-107` |
| INT-002 | Nginx `/api/chat/` → MS2 espera `/api/v1/mole-ai/chat` | ALTA | `nginx.conf:109-114` |
| INT-003 | MS3 router con doble prefix `/api/v1/reports/` | ALTA | `mole_report/app/main.py:37` |
| INT-004 | `FavoritePlant` referenciado en views pero no existe | ALTA | `plants/views.py:160` |

### 4.3 Importaciones No Utilizadas

| Archivo | Importación | Uso |
|---------|------------|-----|
| `core/views.py:10` | `from typing import List` | `List` no utilizado |
| `ai_models/services.py:14` | `import asyncio` | No utilizado directamente |
| `ai_models/services.py:19` | `from tenacity import retry...` | Decoradores no aplicados |

### 4.4 Cuellos de Botella Asíncronos

| Ubicación | Problema | Impacto | Recomendación |
|-----------|----------|--------|--------------|
| `ai_models/services.py` | `mole_ai_client` usa aiohttp pero se llama con `async_to_sync` | Bloqueante en Django | Mover a Celery task |
| `apps/core/views.py:148-153` | `consultar_phi_vision` es síncrono en vista asíncrona | Potencial bloqueo | Mover a task |

---

## 5. Resumen Ejecutivo

### Estado General: ⚠️ REQUIERE CORRECCIÓN CRÍTICA

| Categoría | CUMPLE | PARCIAL | NO CUMPLE |
|-----------|--------|---------|-----------|
| **Enrutamiento** | 42 | 13 | 4 |
| **Seguridad LFPDPPP** | 7 | 0 | 0 |
| **Seguridad IoT** | 4 | 0 | 0 |
| **Cumplimiento NOM-059** | 1 | 1 | 1 |
| **Deuda Técnica** | - | 8 | 2 |

### Issues Críticos para Producción

1. **[CRÍTICO]** Desajuste de rutas Nginx → Microservicios (INT-001, INT-002, INT-003)
2. **[CRÍTICO]** Modelo `FavoritePlant` comentado pero referenciado (DT-007)
3. **[ALTO]** Múltiples endpoints retornan placeholders (DT-001, DT-006)
4. **[ALTO]** NOM-059: Sin validación de especies protegidas

### Recomendaciones de Fix Prioritario

```bash
# 1. Corregir rutas de Nginx para alinearlas con los routers FastAPI
# 2. Descomentar FavoritePlant y crear migración
# 3. Implementar validación de especies protegidas en species_search_view
# 4. Reemplazar placeholders con lógica real o eliminar endpoints
```