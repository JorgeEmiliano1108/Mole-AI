# core_backend — Monolito Django de orquestación Mole.AI

⚠️ **RIESGO CRÍTICO — Shadowing de paquetes**: Los directorios `apps/starlette/` y `apps/pwd/` causan shadowing de paquetes pip/stdlib. Si cualquier dependencia necesita `import starlette` o `import pwd`, la importación resolverá a estos directorios locales (vacíos) en vez de los paquetes reales. Ver TD-01 para mitigación.

## 1. Overview

`core_backend` es el monolito Django que orquesta todos los microservicios de Mole.AI. Gestiona autenticación, dispositivos IoT, telemetría de sensores, control de riego, diagnósticos con IA, reportes, y análisis predictivo para agricultura de precisión.

Actúa como API Gateway interno y backend de administración (Django Admin) para las operaciones del sistema.

## 2. Arquitectura

```
[Nginx Proxy] → [core_backend (Django + DRF)]
                     │
            ┌────────┼────────┬───────────┐
            ↓        ↓        ↓           ↓
       [Celery]  [PostgreSQL] [Redis]   [MinIO]
                     │        (cache)  (objetos)
            ┌────────┼────────┐
            ↓        ↓        ↓
        [mole_vision] [mole_chat] [mole_report]
        (diagnóstico) (chat+RAG)  (reportes)
```

### Dominios principales

| Dominio | Responsabilidad | Apps Django |
|---------|----------------|-------------|
| **Auth & Seguridad** | Autenticación JWT local, registro, perfil, refresh | `authentication` |
| **Plantas & Catálogo** | CRUD de especies, plantas de usuario, búsqueda pública | `plants` |
| **AI & Diagnóstico** | Inferencia CNN, LLM, entrenamiento RAG/Visión | `ai_models` |
| **Training Data** | Upload de documentos e imágenes para fine-tuning | `training_data` |
| **Core (catch-all)** | Telemetría IoT, dispositivos, mapas, chat, diagnósticos, admin | `core` |

## 3. Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Framework | Django ~4.2 + Django REST Framework ~3.14 |
| API | DRF ViewSets + Routers + function-based views |
| Autenticación | JWT local HS256 + Supabase opcional + API Keys por dispositivo |
| Base de datos | PostgreSQL 15 + pgvector |
| Cache | Redis (django-redis + celery) |
| Task Queue | Celery + Redis (broker) |
| Object Storage | MinIO (S3-compatible) via django-storages |
| AI/ML | Celery tasks para invocar mole_vision, mole_chat |
| Reporting | django-storages + S3/MinIO para PDFs generados por mole_report |
| Serialización | DRF Serializers |
| Background | Celery Beat (tareas programadas) |
| Config | python-dotenv + variables de entorno |
| Server | Gunicorn |
| WebSockets | Django Channels + Daphne |
| Monitoring | Logging estructurado por app |
| Testing | pytest-django + Django TestCase (~900+ tests) |

## 4. Apps Django (5)

| App | Rutas | Propósito |
|-----|-------|-----------|
| `authentication` | `/api/v1/auth/` | Login JWT local, registro, perfil, refresh, validación Supabase |
| `ai_models` | `/api/v1/ai/` | Inferencia CNN, LLM, entrenamiento RAG/Visión, performance |
| `training_data` | `/api/v1/training/` | Upload de documentos e imágenes para fine-tuning |
| `core` | `/api/v1/` (catch-all) | Telemetría, dispositivos IoT, mapas, chat, diagnósticos, admin, health |
| `plants` | `/api/v1/plants/`, `/api/v1/user-plants/` | Catálogo de especies, CRUD de plantas de usuario |

**Nota:** Los directorios `apps/starlette/` y `apps/pwd/` NO son apps Django. Son carpetas que causan shadowing de paquetes pip/stdlib (ver ⚠️ al inicio).

## 5. Requisitos Funcionales

### 5.1 Autenticación y Seguridad

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-01 | Login con JWT HS256 (Supabase) | `apps.authentication` |
| RF-02 | Validación de tokens en cada request | `apps.authentication` (middleware) |
| RF-03 | API Keys por dispositivo IoT | `apps.core` (Device.auth_token, HardwareAPIKeyAuthentication) |
| RF-04 | CRUD de usuarios con roles (admin, agricultor, técnico) | `apps.authentication` ⚠️ Solo campo supabase_role, sin vistas CRUD |
| RF-05 | Rate limiting por usuario/IP | `apps.core` (throttles.py — DRF throttles) |

### 5.2 IoT y Telemetría

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-06 | Ingesta de telemetría M2M desde dispositivos | `apps.core` (sensor_batch_view, EdgeNodeIngestView, MQTT listener) |
| RF-07 | Bulk insert de lecturas de sensores | `apps.core` (SensorLog.bulk_create, SoilReading.bulk_create) |
| RF-08 | Downsampling de datos históricos (retención) | `apps.core/tasks.py` (downsample_telemetry Celery task) |
| RF-09 | Geocercas virtuales para parcelas | ❌ No implementado |
| RF-10 | Edge computing: procesamiento en nodo local | ❌ No implementado |

### 5.3 Inteligencia Artificial

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-11 | Diagnóstico de enfermedades por imagen (→ mole_vision) | `apps.ai_models` |
| RF-12 | Chat contextual con RAG (→ mole_chat) | `apps.ai_models` (services.py → ms2_chat:8002) |
| RF-13 | Predicción de rendimiento de cultivos ⚠️ | `apps.ai_models` (model_performance_view — rendimiento del modelo, no de cultivos. No hay predictivo) |
| RF-14 | Modelo hídrico para optimización de riego | ❌ No implementado |

### 5.4 Control de Riego

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-15 | Programación automática de riego por sensor | ❌ No implementado |
| RF-16 | Control PID de válvulas solenoides | ❌ No implementado |
| RF-17 | Alertas de humedad/temperatura fuera de rango | `apps.core/admin_views.py` (live_alerts_view) |

### 5.5 Reportes y Exportación

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-18 | Reportes PDF de historial de cultivo | ❌ Delegado a ms3_reports externo. `apps.core` no genera PDF |
| RF-19 | Exportación XLSX de lecturas de sensores | ❌ Solo CSV export para datos viejos. No hay XLSX |
| RF-20 | Dashboard administrativo con estadísticas | `apps.core` (admin_views.py — admin_stats_view) |

### 5.6 Administración

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-21 | Panel Django Admin para gestión completa | `apps.core/admin.py` (registro parcial de modelos) |
| RF-22 | Logs de auditoría de acciones críticas | `apps.core` (models.py — AuditLog) |
| RF-23 | Gestión de archivos multimedia en MinIO | `apps.training_data` (presigned URLs S3) + `apps.core` |

## 6. Requisitos No Funcionales

### 6.1 Seguridad

| ID | Requisito | Estado |
|----|-----------|--------|
| RNF-01 | JWT HS256 con expiración configurable | ✅ Implementado (`mole_ai_backend/settings.py` JWT_TTL_MINUTES, JWT_ALGORITHM) |
| RNF-02 | API Keys rotables por dispositivo | ⚠️ auth_token existe en Device model, pero sin endpoint de rotación |
| RNF-03 | CORS configurado por orígenes permitidos | ⚠️ Manejado por Nginx (frontend/nginx.conf), no por Django. CORS_ALLOWED_ORIGINS=[] |
| RNF-04 | Rate limiting con django-ratelimit | ⚠️ Usa DRF throttles (UserRateThrottle), no django-ratelimit |
| RNF-05 | Hashing de contraseñas con bcrypt/Auth0 | ⚠️ Usa HS256 JWT. SupabaseAuthentication existe pero no bcrypt |
| RNF-06 | Protección contra SQL injection (ORM) | ✅ Django ORM |
| RNF-07 | Path traversal protection en uploads | ⚠️ Parcial — validate_file solo verifica content-type y tamaño. No sanitiza path |

### 6.2 Resiliencia

| ID | Requisito | Estado |
|----|-----------|--------|
| RNF-08 | Celery con reintentos automáticos (tenacity) | ⚠️ Algunas tasks |
| RNF-09 | Dead-letter queue para tareas fallidas | ❌ No implementado |
| RNF-10 | Graceful degradation si microservicio falla | ⚠️ Parcial |
| RNF-11 | Connection pooling en PostgreSQL | ❌ No implementado (pool vía pgBouncer externo) |

### 6.3 Performance

| ID | Requisito | Estado |
|----|-----------|--------|
| RNF-12 | Redis cache para queries frecuentes | ✅ django-redis (`mole_ai_backend/settings.py`) |
| RNF-13 | Bulk insert optimizado para telemetría | ✅ bulk_create en sensor_batch_view y edge-batch |
| RNF-14 | Downsampling automático de datos viejos | ✅ downsample_telemetry Celery task programada |
| RNF-15 | Paginación en endpoints de listado | ❌ No implementado. Sin DEFAULT_PAGINATION_CLASS en DRF settings |
| RNF-16 | Límite de 30s en requests a microservicios | ✅ httpx.Timeout(30) en MicroserviceClient |

### 6.4 Mantenibilidad

| ID | Requisito | Estado |
|----|-----------|--------|
| RNF-17 | Type hints en funciones públicas | ⚠️ Parcial |
| RNF-18 | Docstrings en clases y métodos críticos | ⚠️ Parcial |
| RNF-19 | Tests unitarios por app | ❌ ~83 tests en 31 archivos. No 900+ |
| RNF-20 | Separación de settings por entorno | ❌ Settings monolítico |

### 6.5 Observabilidad

| ID | Requisito | Estado |
|----|-----------|--------|
| RNF-21 | Logging estructurado por app | ✅ Implementado (LOGGING config con PIIFilter, formato verbose) |
| RNF-22 | Tracking de tareas Celery en Django Admin | ❌ No implementado (django-celery-results no en INSTALLED_APPS) |
| RNF-23 | OpenTelemetry exports (referencias en código) | ❌ Solo 1 test file referencia OTEL. Sin producción |
| RNF-24 | Health check endpoint | ✅ `/health/` (público) + `/api/v1/health/` (JWT) |

## 7. Deuda Técnica

| ID | Deuda | Impacto | Módulo |
|----|-------|---------|--------|
| TD-01 | **Shadowing de paquetes pip**: directorios `apps/starlette/` y `apps/pwd/` causan `ImportError` al querer usar los paquetes pip reales (`import starlette`, `import pwd`) | **Crítico** — Rompe imports en producción si se instalan esas dependencias | `apps/starlette`, `apps/pwd` |
| TD-02 | **Variables de entorno duplicadas**: `SUPABASE_URL`, `SUPABASE_DB_URL`, `DATABASE_URL` coexisten sin validación cruzada | **Alto** — Inconsistencia silenciosa en cadena de conexión | `mole_ai_backend/settings.py` |
| TD-03 | **Settings monolítico**: `settings.py` de ~389 líneas sin split por entorno (dev/staging/prod) | **Medio** — Dificulta cambios específicos por entorno | `mole_ai_backend/settings.py` |
| TD-04 | **Views sin type hints**: ~70% de views carecen de tipos en parámetros/retorno | **Medio** — Menor legibilidad y peor IDE support | Varias apps |
| TD-05 | **Código legacy no referenciado**: varias vistas y serializers parecen no usarse en rutas activas | **Medio** — Ruido que dificulta navegación | `chat/`, posibles otras |
| TD-06 | **Test coverage sin métrica central**: no hay `coverage` configurado ni umbral en CI | **Medio** — No se puede medir regresión | `pyproject.toml` |
| TD-07 | **Dependencias no fijadas**: `requirements.txt` sin versiones pinneadas | **Alto** — Riesgo de rotura silenciosa en deploy | `requirements/*.txt` |
| TD-08 | **Sin pre-commit hooks**: formateo/linting no estandarizados | **Bajo** — Inconsistencias de estilo entre apps | — |
| TD-09 | **Uso inconsistente de `os.getenv` vs `decouple.config`**: mezcla ambos patrones | **Medio** — Dificulta auditoría de configuración | Varias apps |

## 8. Bugs Identificados

| ID | Bug | Severidad | Módulo | Detalle |
|----|-----|-----------|--------|---------|
| BUG-01 | **Import collision**: `import starlette` desde `apps/starlette/views.py` resuelve al directorio local en vez del paquete pip | **Crítica** | `apps/starlette/` | Si alguna dependencia pip necesita `import starlette`, se rompe |
| BUG-02 | **Import collision**: `import pwd` desde `apps/pwd/` resuelve al directorio local | **Alta** | `apps/pwd/` | Idem, cualquier script que necesite `pwd` de stdlib falla |
| BUG-03 | **Inconsistencia DB URL**: 3+ variables de entorno para DB sin validación cruzada | **Alta** | `settings.py` | Cambiar una sin actualizar las demás causa conexiones caídas |
| BUG-04 | **DecoupleValueError sin manejo**: si falta env var, `decouple.config()` lanza excepción no capturada al arranque | **Media** | Varias apps | Mejorable con validación al startup |

## 9. Cumplimiento Normativo

| Norma | Ámbito | Estado en core_backend |
|-------|--------|----------------------|
| **LFPDPPP** (Ley Federal de Protección de Datos Personales) | México — Protección de datos personales | ⚠️ Parcial: PII en logs no sanitizada consistentemente; no hay política de retención explícita |
| **NOM-059-SEMARNAT** | México — Protección de especies en riesgo | ✅ Implementado en mole_vision (double layer: prompt + regex); core_backend no tiene endpoint directo de visión |
| **MoProSoft** (MMX-I-059-NYCE) | México — Modelo de procesos de software | ⚠️ Parcial: hay trazabilidad en CI/CD pero faltan procesos formales documentados |
| **ISO 25000** (SQuaRE) | Internacional — Calidad de software | ⚠️ Parcial: cobertura de tests >70% pero sin métricas de mantenibilidad, eficiencia, portabilidad |

## 10. Endpoints Clave

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login/` | Público | Login local con credenciales → JWT |
| POST | `/api/v1/auth/register/` | Público | Registro de nuevo usuario |
| POST | `/api/v1/auth/refresh/` | JWT | Refresh de token |
| GET | `/api/v1/auth/profile/` | JWT | Perfil del usuario actual |
| POST | `/api/v1/auth/logout/` | JWT | Cierre de sesión (stateless) |
| GET | `/api/v1/health/` | JWT | Health check del backend |
| GET | `/health/` | Público | Health check público (lambda) |
| GET | `/api/v1/plants/species/` | JWT | Catálogo de especies (CRUD) |
| GET | `/api/v1/plants/search/` | Público | Búsqueda pública de especies |
| POST | `/api/v1/plants/` | JWT | Crear planta de usuario |
| GET | `/api/v1/sensor-data/latest/` | Público | Datos mock de sensores (legacy) |
| GET | `/api/v1/telemetry/latest/` | JWT | Últimas lecturas de telemetría |
| POST | `/api/v1/sensors/ingest` | JWT | Ingesta de sensores (Zero-Trust) |
| GET | `/api/v1/devices/<uuid:id>/health/` | API Key | Health de dispositivo IoT |
| GET | `/api/v1/devices/<uuid:id>/bindings/` | API Key | Listar bindings de dispositivo |
| POST | `/api/v1/devices/<uuid:id>/bindings/` | API Key | Crear binding |
| GET | `/api/v1/map/hotspots/` | JWT | Hotspots de plagas en mapa |
| GET | `/api/v1/weather/current/` | Público | Clima actual (OpenWeather proxy) |
| POST | `/api/v1/llm/chat/` | JWT | Chat LLM local |
| POST | `/api/v1/iot/nodes/` | JWT | Crear nodo IoT |
| GET | `/api/v1/ai/performance/` | JWT | Métricas de modelos ML |
| GET | `/api/v1/diagnostics/` | JWT | Historial de diagnósticos |
| GET | `/api/v1/admin/statistics` | Admin | Estadísticas del sistema |
| GET | `/api/v1/admin/live-alerts` | Admin | Alertas en vivo |
| POST | `/api/v1/admin/reports/generate` | Admin | Generar reporte maestro |
| POST | `/api/v1/ai/train/rag/` | Admin | Entrenar modelo RAG |
| POST | `/api/v1/ai/train/vision/` | Admin | Entrenar modelo de visión |
| GET | `/api/v1/tasks/status/<str:task_id>/` | JWT | Estado de tareas asíncronas |

## 11. Flujos Críticos

### 11.1 Ingesta de sensores

```
[Sensor] → POST /api/v1/sensors/ingest (JWT)
             → Valida JWT o API Key
             → Bulk insert en SensorLog (PostgreSQL)
             → Dispara Celery task de downsampling
             → Actualiza cache Redis (última lectura)
             → Evalúa reglas de alerta (humedad < umbral)
```

### 11.2 Diagnóstico de planta con IA

```
[Usuario] → POST /api/v1/ai/vision/analyze/ (imagen + metadata)
              → Valida JWT
              → Celery task → mole_vision (diagnóstico)
              → mole_vision retorna diagnóstico
              → Guarda resultado en PostgreSQL
              → Opcional: mole_chat para recomendaciones
              → Retorna diagnóstico al usuario
```

## 12. Tests

- **Total estimado**: ~900+ tests entre todas las apps
- **Framework**: pytest + Django TestCase
- **Problema conocido**: shadowing de `starlette/` y `pwd/` puede causar falsos negativos en tests que importen esos paquetes

## 13. Licencias

core_backend es software privativo (closed source). Queda prohibido integrar dependencias con licencias GPL, LGPL, AGPL o cualquier licencia que obligue a liberar el código fuente derivado. Verificar con `pip-licenses --fail-on="GPL;LGPL;AGPL"` en CI.
