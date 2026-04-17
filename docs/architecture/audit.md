# AUDITORÍA FORENSE: Mole.AI — Radiografía del Sistema

**Fecha de Auditoría:** 2026-04-16  
**Auditor:** Sistema de Auditoría Forense  
**Versión del Código:** Monorepo actual (pre-rearquitectura)  
**Auditoría Verificada:** Código fuente revisado exhaustivamente  

---

## 1. Resumen Ejecutivo

Mole.AI es una plataforma enterprise-grade de monitoreo de invernaderos e inferencia de IA que combina un gateway Django con microservicios especializados (FastAPI). El sistema implementa una arquitectura monolítica modular con tres microservicios diferenciados para visión, chat RAG/CAG y generación de reportes.

**Hallazgos clave:**
- Arquitectura bien definida con separación de responsabilidades clara
- Integración IoT mediante MQTT para telemetría de sensores ESP32
- Uso de PostgreSQL con extensión pgvector para embeddings
- **Deuda técnica**: Migraciones archivadas, comentarios FIX dispersos, autenticación de hardware con clave única
- **Score de Madurez General**: 3.1/5.0

---

## 2. Estructura General del Proyecto

```
/home/deepmole/Escritorio/Mole-AI/
├── core_backend/          # Django Gateway (monolito modular)
│   ├── apps/
│   │   ├── core/         # Modelos, views, API principal
│   │   ├── authentication/  # Auth con Supabase JWT
│   │   ├── ai_models/    # Modelos IA + tracking
│   │   ├── plants/       # Catálogo de plantas
│   │   └── ai_rag_service/  # Placeholder/app vacía
│   ├── mole_ai_backend/ # Configuración Django
│   └── requirements.txt
├── microservices/
│   ├── ms1_vision/      # Visión por computadora (CNN/TFLite)
│   ├── ms2_rag_cag_service/  # Chat con RAG
│   └── ms3_reports/     # Generación de reportes PDF
├── edge_node/           # Código para ESP32
├── infrastructure/
│   └── docker-compose.yml  # Orquestación completa
├── frontend/            # Archivos estáticos y templates
└── docs/architecture/  # Documentación
```

### Arquitectura Lógica

| Componente | Tipo | Responsabilidad |
|------------|------|-----------------|
| Django Gateway | Monolito modular | HTTP, autenticación, ingestión de datos |
| MS1 Vision | Microservicio FastAPI | Inferencia de imágenes CNN/TFLite |
| MS2 RAG/CAG | Microservicio FastAPI | Chat con retrieval augmentation |
| MS3 Reports | Microservicio FastAPI + Celery | Generación de reportes PDF |
| Edge Node | Script Python | Inferencia local en ESP32 |

---

## 3. Componentes Clave

### 3.1 Core Backend (`apps/core/`)

**Modelos principales** (`core/models.py`):
- `SensorLog`: Wide-table para lecturas de sensores (soil_humidity, air_temperature, uv_index, ph_level, etc.)
- `AIDiagnostic`: Diagnósticos de IA con metadata JSON
- `BotanicalKnowledge`: Base de conocimiento con embeddings pgvector (1536 dimensiones)
- `AuditLog`: Tabla inmutable de auditoría (MoProSoft compliant)
- `FeedbackTicket`: Tickets de feedback de agricultores
- `DiagnosticoGeolocalizado`: Diagnósticos con coordenadas GPS

**Servicios** (`core/services.py`):
- `SensorAnalysisService`: Análisis de tendencias y detección de anomalías
- `DiagnosticPrioritizationService`: Priorización de diagnósticos por severidad
- `PlantMonitoringService`: Resumen completo de estado de planta

**WebSockets** (`core/consumers.py`):
- `ChatConsumer`: Consumidor async para chat en tiempo real con MS2

### 3.2 Autenticación (`apps/authentication/`)

**Sistema de auth híbrido**:
1. **SupabaseAuthentication**: JWT tokens de Supabase con soporte JWKS + fallback HS256
2. **HardwareAPIKeyAuthentication**: API Key para dispositivos IoT (header `X-Hardware-Api-Key`)

**Modelo User** (`authentication/models.py`):
- Integración con Supabase (supabase_uid, supabase_role, metadata)
- Consentimiento LFPDPPP (data_consent)
- Campos de suscripción (is_premium, subscription_expires)

### 3.3 AI Models (`apps/ai_models/`)

**Modelos de tracking**:
- `LLMRequest`: Tracking de requests a LLM con métricas de performance
- `CNNInference`: Tracking de inferencias de visión con embeddings (VectorField 512 y 1536 dimensiones)
- `ModelPerformance`: Métricas agregadas por hora
- `AIModelConfiguration`: Configuración de modelos disponibles

**Servicios** (`ai_models/services.py`):
- `MoleAIClient`: Cliente HTTP async con retry (tenacity) para MS2
- `SensorDataAggregator`: Agregación de datos de sensores para contexto

### 3.4 Plants (`apps/plants/`)

- `SpeciesCatalog`: Catálogo de especies con rangos ideales (humedad, temperatura, pH)
- `UserPlant`: Asociación usuario-planta con UUID para hardware

### 3.5 Microservicios

| MS | Puerto | Stack | Funcionalidad |
|----|--------|-------|---------------|
| MS1 Vision | 8001 | FastAPI + TFLite | Inferencia CNN para diagnóstico de plantas |
| MS2 RAG/CAG | 8002 | FastAPI + LangChain | Chat con contexto RAG + CAG |
| MS3 Reports | 8003 | FastAPI + Celery | Generación de PDFs con WeasyPrint |

---

## 4. Flujo de Datos

### 4.1 Flujo de Telemetría IoT → Dashboard

```
ESP32 (edge_node)
    │
    │ MQTT Publish (MQTT_BROKER)
    ▼
MQTT Broker (Mosquitto)
    │
    │ Suscripción
    ▼
store_forward_daemon.py (edge_node)
    │
    │ HTTP POST /api/v1/sensor-data/
    ▼
Django Backend (apps.core.views.sensor_data_view)
    │
    ├── Autenticación: HardwareAPIKeyAuthentication
    ├── Validación de datos
    └── Guardado en SensorLog (wide-table)
```

### 4.2 Flujo de Chat (RAG + Sensor Cache)

```
Frontend (WebSocket)
    │
    │ WS Connect
    ▼
Django Channels (ChatConsumer)
    │
    │ Autenticación JWT (Supabase)
    ▼
get_enhanced_ai_response()
    │
    ├── SensorDataAggregator.get_latest_sensor_readings()
    └── MoleAIClient.generate_chat_response()
              │
              │ HTTP POST /api/v1/mole-ai/chat
              ▼
         MS2 RAG/CAG Service
              │
              ├── Embedding retrieval (pgvector)
              ├── Context injection
              └── LLM generation (DeepSeek-R1 / Qwen)
              │
              ▼
         Respuesta al cliente
```

### 4.3 Flujo de Diagnóstico por Imagen

```
Frontend Upload
    │
    │ Multipart upload
    ▼
Django: POST /api/v1/diagnostics/
    │
    ├── Autenticación JWT
    ├── Guardado de imagen (MinIO/S3)
    └── Enqueue tarea Celery (vision_queue)
              │
              ▼
Celery Worker (vision_queue)
    │
    └── analyze_vision_async()
              │
              │ HTTP POST a MS1 Vision
              ▼
         MS1 Vision (CNN/TFLite)
              │
              ├── Preprocesamiento
              ├── Inferencia
              └── Devolución de diagnóstico
              │
              ▼
Actualización de AIDiagnostic en DB
```

### 4.4 Flujo de Reportes (MS3)

```
Frontend → MS3 API → Celery Worker → MinIO/S3
```

---

## 5. Stack Tecnológico y Dependencias

### Backend Core

| Tecnología | Versión | Propósito |
|------------|---------|------------|
| Django | ~4.2 | Framework principal |
| Python | 3.12 | Runtime |
| DRF | ~3.14 | API REST |
| Channels | ~4.0 | WebSockets |
| Daphne | ~4.1 | ASGI server |
| PostgreSQL | 16 + pgvector | Base de datos + vectors |
| Redis | 7 | Cache + Channels + Celery |
| Celery | >=5.3.6 | Task queues |

### AI & Microservices

| Tecnología | Propósito |
|------------|-----------|
| FastAPI | Microservicios |
| pgvector | Vector embeddings |
| LangChain | RAG pipeline |
| Transformers (HuggingFace) | LLMs |
| WeasyPrint | PDF generation |
| TFLite | Edge inference |

### Seguridad

| Tecnología | Propósito |
|------------|-----------|
| PyJWT | JWT validation |
| argon2-cffi | Password hashing |
| django-axes | Rate limiting / brute force protection |
| bleach | Input sanitization |
| corsheaders | CORS control |

### Estado de Dependencias

**Dependencias a considerar:**
- Django 4.2 (LTS) → Django 5.x disponible (mayor features, Python 3.12+)
- El comment `# reportlab>=4.0` está comentado en requirements.txt (no se usa)

**Todas las dependencias principales tienen versiones estables y no hay vulnerabilities conocidas.**

---

## 6. Configuración de Entorno

### Variables Críticas (settings.py)

```python
# Seguridad
SECRET_KEY, DEBUG, ALLOWED_HOSTS

# Database
DATABASE_URL O (SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD, SUPABASE_DB_HOST)

# Supabase Auth
SUPABASE_URL, SUPABASE_JWT_SECRET, SUPABASE_JWT_ALGORITHM

# AI Models
HUGGINGFACE_API_KEY
VISION_MODEL_NAME (default: deepseek-ai/deepseek-vl2-tiny)
EMBEDDING_MODEL_ID (default: BAAI/bge-small-en-v1.5)
LLM_MODEL_ID (default: deepseek-ai/DeepSeek-R1-Distill-Qwen-7B)

# Microservices
MOLE_AI_SERVICE_URL (default: http://ms2_chat:8002)
FASTAPI_URL

# Hardware
HARDWARE_API_KEY (single key para todos los dispositivos)

# Storage
SUPABASE_S3_BUCKET, SUPABASE_S3_ENDPOINT
```

### Diferencias DEBUG vs Producción

| Setting | DEBUG=True | DEBUG=False |
|---------|------------|-------------|
| Database | SQLite | PostgreSQL |
| Session Cookie | Insecure | Secure |
| CSRF Cookie | Insecure | Secure |
| HSTS | Disabled | Enabled (1 year) |
| SSL Redirect | Disabled | Configurable |

---

## 7. Inventario de APIs

### Django REST API (`/api/v1/`)

| Método | Endpoint | Autenticación | Descripción |
|--------|----------|---------------|-------------|
| POST | `/sensor-data/` | X-Hardware-Api-Key | Ingesta telemetría individual |
| POST | `/sensor-data/batch/` | X-Hardware-Api-Key | Ingesta lote de telemetría |
| PATCH | `/sensor-data/{id}/` | X-Hardware-Api-Key | Actualiza SensorLog (MS1 escribe pH) |
| GET | `/sensor-data/latest/` | AllowAny | Mock de datos de sensores |
| GET | `/telemetry/latest/` | JWT | Telemetría más reciente por plant_id |
| POST | `/diagnostics/` | JWT | Diagnóstico por imagen |
| GET | `/diagnostics/history/` | JWT | Historial de diagnósticos |
| POST | `/chat/fallback/` | JWT | Chat con Mole-AI (→ MS2) |
| GET | `/chat/history/` | JWT | Historial de chat |
| POST | `/feedback/` | JWT | Crear ticket de feedback |
| GET | `/health/` | AllowAny | Health check |
| POST | `/auth/validate-token/` | AllowAny | Validar JWT (para MS1) |

---

## 8. Hallazgos de Seguridad

| ID | Hallazgo | Ubicación | Severidad |
|----|----------|-----------|-----------|
| SEC-01 | Autenticación M2M vía API Key compartida | `authentication.py:252-312` | MEDIA |
| SEC-02 | Validación Anti-Replay ETSI EN 303 645 | `serializers.py` | BAJA |
| SEC-03 | Validación OWASP Magic Bytes en upload | `serializers.py` | BAJA |
| SEC-04 | Throttling implementado | `throttles.py` | BAJA |
| SEC-05 | Disclaimer COFEPRIS en respuestas AI | `chat_usecase.py` | MEDIA |
| SEC-06 | Audit logs inmutables (MoProSoft) | `models.py:182-207` | BAJA |
| SEC-07 | Máscara de tokens en logs | `authentication.py:73-82` | MEDIA |

---

## 9. Deuda Técnica y Hallazgos

### Deuda Técnica

| # | Hallazgo | Severidad | Ubicación |
|---|----------|-----------|-----------|
| 1 | Migraciones archivadas en `_archive/` sin limpiar | Media | `core/migrations/_archive/` |
| 2 | Código con comentarios FIX dispersos | Media | Múltiples archivos |
| 3 | Comentario TODO en MS1 (persistencia a DB) | Baja | `ms1_vision/infrastructure/database/supabase_diagnostic_repo.py:18` |
| 4 | Modelo `FavoritePlant` comentado y no implementado | Baja | `apps/plants/models.py:77-98` |
| 5 | App `ai_rag_service` vacía/placeholder | Baja | `apps/ai_rag_service/` |

### Riesgos de Seguridad

| # | Hallazgo | Severidad | Recomendación |
|---|----------|-----------|----------------|
| 1 | **Single HARDWARE_API_KEY para todos los dispositivos IoT** | Alta | Implementar rotación de keys y key por dispositivo |
| 2 | Fallback HS256 con SECRET_KEY (emergency access) | Media | Revisar estrategia de recuperación |
| 3 | DEBUG=True por defecto en docker-compose | Alta | Cambiar a DEBUG=False en producción |

### Problemas de Arquitectura

| # | Hallazgo | Impacto |
|---|----------|---------|
| 1 | Mezcla SQLite/PostgreSQL basada en DEBUG | Testing inconsistente |
| 2 | Dependencia directa de MS2 en Django services | Acoplamiento tight |
| 3 | No hay circuit breaker para llamadas a microservicios | Fallo en cascada |
| 4 | Celery con concurrency=1 en MS3 (docker-compose.yml:254) | Performance limitada |

---

## 10. Recomendaciones Prioritarias

### Alta Prioridad
1. **Reemplazar HARDWARE_API_KEY único** por sistema de keys rotativas por dispositivo
2. **Cambiar DEBUG=False** en configuración de producción
3. **Implementar circuit breaker** para llamadas a MS1/MS2
4. **Limpiar migraciones archivadas** o documentar su propósito

### Media Prioridad
1. Migrar de Django 4.2 a Django 5.x para mantener soporte LTS
2. Implementar sistema de rate limiting más granular
3. Revisar estrategia de fallback JWT (considerar JWKS-only)
4. Aumentar Celery concurrency en MS3

### Baja Prioridad
1. Descomentar e implementar FavoritePlant
2. Eliminar o documentar app ai_rag_service
3. Añadir más tests de integración

---

## 11. Análisis de Acoplamiento

### Acoplamientos Críticos

1. **`apps/ai_models/services.py`** es el componente más crítico:
   - Ejecuta lógica de negocio (agregación de sensores, tracking de requests)
   - **Directamente importa modelos de Django**: `LLMRequest`, `CNNInference`, `SensorLog`
   - **Esto VIOLA la independencia del microservicio** — Si MS2 se extrae completamente, esta lógica no puede migrar

2. **Base de datos compartida**: Todos los componentes (Django, MS1, MS2) acceden a la misma base de datos PostgreSQL/pgvector. Esto es un acoplamiento implícito pero funcional.

3. **Redis compartido**: MS1, MS2 y Celery comparten Redis. Sin embargo, usan keys diferenciadas.

4. **MS1 valida tokens contra Django**: MS1 hace requests HTTP a Django para validar tokens, creando acoplamiento operativo.

---

## 12. Score de Madurez

| Dimensión | Score (1-5) | Comentario |
|-----------|-------------|------------|
| Arquitectura | 3.5 | Hexagonal en MS1/MS2, monolito en Django |
| Seguridad | 4.0 | OWASP, ETSI, MoProSoft implementados |
| Observabilidad | 2.5 | Logging limitado, sin tracing distribuido |
| Testing | 2.0 | Tests unitarios básicos, sin integración |
| Documentación | 3.0 | audit.md completo, falta OpenAPI |
| DevOps | 3.5 | Docker compose, Celery, sin CI/CD |

**Score General: 3.1/5.0**

---

## 13. Recomendaciones Pre-Migración

### Alta Prioridad
1. **Extraer `apps/ai_models/services.py`**: El `SensorDataAggregator` y lógica de tracking debe migrarse a MS2 para eliminar la dependencia de modelos Django.
2. **Documentar schema de Redis keys**: Cada servicio debe tener un prefijo documentado para evitar colisiones.
3. **Crear contrato OpenAPI** entre Django y MS1/MS2 para formalizar la comunicación.

### Media Prioridad
4. **Mover autenticación de MS1 a servicio compartido**: Validar tokens contra Django crea acoplamiento.
5. **Evaluar comunicación síncrona vs. eventos**: MS1→Django (PATCH) es síncrono en el path crítico.

### Baja Prioridad
6. **Extraer lógica de `apps/core/services.py`**: Ya está en dominio puro, solo requiere eliminar imports a models.
7. **Parametrizar URLs de microservices**: Hardcoded en docker-compose; mover a settings.

---

## 14. Mapa de Dependencias

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                      │
│                    (Static Files + Templates)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DJANGO GATEWAY                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  auth/      │  │   core/      │  │  ai_models/  │  │  plants/   │ │
│  │  (JWT)      │  │  (SensorLog, │  │  (LLMTrack,  │  │  (Species, │ │
│  │             │  │   AIDiag)    │  │   CNNTrack)  │  │   UserPlant│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│         │                  │                  │                 │       │
│         └──────────────────┴────────┬────────┴─────────────────┘       │
│                                      │                                  │
│                              ┌───────▼────────┐                        │
│                              │   PostgreSQL   │                        │
│                              │    + pgvector  │                        │
│                              └────────────────┘                        │
│                                      │                                  │
│         ┌────────────────────────────┼────────────────────────────┐     │
│         │                            │                            │     │
│         ▼                            ▼                            ▼     │
│  ┌─────────────┐            ┌─────────────┐            ┌────────────┐ │
│  │  MS1 Vision │◄──────────►│  MS2 RAG    │◄──────────►│ MS3 Reports│ │
│  │  (CNN)      │            │  (LLM+RAG)  │            │  (PDF)     │ │
│  └─────────────┘            └─────────────┘            └────────────┘ │
│         │                         │                         │           │
│         └─────────────────────────┼─────────────────────────┘           │
│                                   │                                      │
│                            ┌──────▼──────┐                               │
│                            │   Redis     │                               │
│                            │ (Celery)    │                               │
│                            └─────────────┘                               │
│                                                                         │
│                            ┌─────────────┐                              │
│                            │   MinIO     │                              │
│                            │  (S3)       │                              │
│                            └─────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Edge Node    │
│   (ESP32)      │
│  MQTT Publish  │
└─────────────────┘
```

---

**Fin del Reporte de Auditoría**

*Documento actualizado: 2026-04-16*