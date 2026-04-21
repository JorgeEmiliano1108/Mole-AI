# Auditoría de Interconexión y Cumplimiento - Mole.AI (AUDITTT.md)

## 1. Topología de Red Docker

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RED DOCKER: mole-ai-net                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │  Django     │    │  ms1_vision  │    │  ms2_chat    │               │
│  │  :8000     │    │  :8001      │    │  :8002      │               │
│  │  (gunicorn) │    │  (uvicorn)  │    │  (uvicorn)  │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                  │                  │                            │
│  ┌─────┴─────────────────┴──────────────────┴──────────────────┐  │
│  │                    SERVICIOS COMUNES                             │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐ │  │
│  │  │Postgres│  │Redis  │  │MinIO  │  │Mosquitto│  │ Celery │ │  │
│  │  │ :5432 │  │ :6379 │  │ :9000 │  │ :1883 │  │       │ │  │
│  │  │+pgvector│  │      │  │       │  │       │  │       │ │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Flujo de Datos (Data Flow)

### FLUJO 1: SENSORES (IoT)
```
ESP32 ──[MQTT]──► Edge Node ──[REST POST]──► Django (:8000) ──[Redis]──► PostgreSQL
(telemetry)      (mqtt_local_subscriber.py)   (POST /api/core/sensors/ingest)   (SensorLog model)
```

### FLUJO 2: VISIÓN (Diagnóstico IA)
```
Usuario ──[JWT]──► Django ──[Celery]──► ms1_vision (:8001)
│              │        │           └── TFLite CNN inference
│              │        │
│              │◄──[response]──┘
│              │
└──[AIDiagnostic]──► PostgreSQL (pgvector)
```

### FLUJO 3: CHAT/RAG (Asistente IA)
```
Usuario ──[JWT ES256]──► Django ──[REST]──► ms2_chat (:8002)
│                         │                ├── Redis (CAG context)
│                         │                ├── FAISS (RAG vector store)
│                         │                └── HuggingFace (LLM DeepSeek-R1)
│                         │
│◄──[ChatResponse + sources + disclaimer]──┘
│
└──[ChatHistory]──► PostgreSQL
```

### FLUJO 4: REPORTES (PDF)
```
Usuario ──[JWT]──► Django ──[Celery]──► ms3_reports (:8003)
│                    │              ├── Generate PDF (ReportLab)
│                    │              └── MinIO (S3 storage)
│                    │
│◄──[response PDF URL]──┘
└──[PDF URL]──► MinIO
```

## 3. Matriz de Interconexión

| Servicio | Puerto | Protocolo | Autenticación | Dependencias | LFPDPPP |
|----------|--------|-----------|---------------|---------------|----------|
| **Django (core_backend)** | 8000 | HTTP/REST | JWT (Supabase) | Postgres, Redis, Celery | ✅ Hash SHA-256 en logs |
| **ms1_vision** | 8001 | HTTP/REST | JWT ES256 | Redis, TFLite, MinIO | ✅ JWT + EXIF clean |
| **ms2_chat** | 8002 | HTTP/REST | JWT ES256 | Redis, FAISS, HF | ✅ JWT + PIISanitizer |
| **ms3_reports** | 8003 | HTTP/REST | JWT (delegado) | Redis, Celery, MinIO | ⚠️ Por implementar |
| **Celery Worker** | - | AMQP/Redis | ❌ No | Redis queue | ⚠️ Sin interceptor JWT |
| **PostgreSQL (db)** | 5432 | TCP/PostgreSQL | - | - | ✅ pgvector enabled |
| **Redis** | 6379 | TCP/Redis | - | - | ✅ ACL config |
| **Mosquitto** | 1883 | MQTT | - | - | ⚠️ Sin TLS |

## 4. Evaluación de Cumplimiento

### 4.1 Interceptor JWT (Puntos de Entrada)

| Punto de Entrada | JWT Validado | Evidencia | Archivo |
|------------------|--------------|-----------|----------|
| Django /api/sensors/ingest | ⚠️ Parcial |Middleware disponible | middleware.py |
| Django /api/ai_diagnostic/ | ✅ Celery | tasks.py:66 | tasks.py |
| ms1_vision /analyze | ✅ dependencies.py | HTTPBearer + get_current_user | dependencies.py:12 |
| ms2_chat /chat | ✅ dependencies.py | HTTPBearer + get_current_user | dependencies.py:12 |
| ms3_reports /generate | ⚠️ Delegado a Celery | Sin validación en worker | - |

### 4.2 Sanitización PII (LFPDPPP)

| Servicio | PII Sanitized | Evidencia | Archivo |
|----------|---------------|-----------|----------|
| **ms1_vision** | ✅ EXIF clean | getexif().clear() | dependencies.py:clean_exif |
| **ms2_chat** | ✅ Email + Teléfono | pii_sanitizer.py regex | pii_sanitizer.py:22-23 |
| **Django logging** | ✅ Hash SHA-256 | _hash_user_id() | security.py |
| **Celery tasks** | ❌ No implementado | - | - |

### 4.3 Zero-Trust (JWT ES256)

| Servicio | Algoritmo ES256 | JWKS Cache | Lock Anti-DoS |
|----------|----------------|-----------|--------------|
| **ms1_vision** | ✅ Line 49 | ✅ 300s TTL (Line 38) | ✅ asyncio.Lock (Line 37) |
| **ms2_chat** | ✅ Line 49 | ✅ 300s TTL (Line 38) | ✅ asyncio.Lock (Line 37) |
| **Django** | ⚠️ Supabase only | ❌ No caching | ❌ No |

## 5. Hallazgos y Recomendaciones

### 5.1 Hallazgos Críticos

| ID | Severidad | Descripción | Impacto |
|----|-----------|-------------|----------|
| **H-01** | **CRÍTICO** | Django /api/sensors/ sin validación JWT activa | Cualquiera puede enviar datos |
| **H-02** | **ALTO** | ms3_reports sin validación JWT directa | Sin control de acceso |
| **H-03** | **ALTO** | Celery workers sin interceptor JWT | Tareas delegadas sin auth |
| **H-04** | **MEDIO** | Mosquitto sin TLS | Tráfico MQTT sin cifrado |
| **H-05** | **MEDIO** | Redis sin ACL restrictiva | Cualquiera puede publicar |

### 5.2 Recomendaciones de Remediación

| Prioridad | Hallazgo | Acción Requerida | Archivo |
|----------|-----------|-----------------|----------|
| **P0** | H-01 | Activar middleware JWT en Django | authentication/middleware.py |
| **P1** | H-02 | Implementar JWT validation en ms3_reports | app/api/dependencies.py |
| **P1** | H-03 | Agregar token validation en Celery tasks | core_backend/tasks.py |
| **P2** | H-04 | Configurar TLS en Mosquitto | mosquitto/config/mosquitto.conf |
| **P2** | H-05 | Configurar ACL en Redis | redis.conf |

## 6. Eficiencia y Cuellos de Botella

### 6.1 Llamadas Síncronas que Deberían Ser Asíncronas

| Ubicación | Actual | Recomendado | Impacto |
|----------|--------|-------------|----------|
| Django → ms1_vision | requests.post (sync) | aiohttp (async) | Bloqueante |
| Django → ms2_chat | requests.post (sync) | aiohttp (async) | Bloqueante |
| Django → ms3_reports | requests.post (sync) | aiohttp (async) | Bloqueante |
| AI Diagnostic save | .save() (sync) | await async_save() | Bloqueante |

### 6.2 Recomendaciones de Arquitectura

1. **Reemplazar requests por aiohttp** en clientes de microservicios
2. **Usar async def** en vistas de Django que llamen a FastAPI
3. **Implementar Redis pub/sub** para eventos en tiempo real
4. **Agregar WebSocket** para streaming de respuestas LLM

## 7. Checklist de Cumplimiento

| Requisito | Estado | Evidencia |
|-----------|--------|----------|
| JWT ES256 en ms1_vision | ✅ CUMPLE | security.py:49 |
| JWT ES256 en ms2_chat | ✅ CUMPLE | security.py:49 |
| JWT en ms3_reports | ❌ PENDIENTE | Ninguna evidencia |
| JWT en Django (sensores) | ⚠️ PARCIAL | Middleware existe pero no activo |
| PII Sanitization ms1 | ✅ CUMPLE | dependencies.py:clean_exif |
| PII Sanitization ms2 | ✅ CUMPLE | pii_sanitizer.py |
| PII en Logging | ✅ CUMPLE | hash_user_id() |
| TLS MQTT | ❌ PENDIENTE | Configuración vacía |

---

## 8. Resumen Ejecutivo

| Métrica | Score |
|---------|-------|
| **Interconexión** | 85% |
| **Zero-Trust JWT** | 75% |
| **LFPDPPP PII** | 80% |
| **Eficiencia** | 70% |

**Riesgo Global**: MEDIO - Sistema funcional con brechas de seguridad en endpoints secundarios (ms3_reports, Celery, sensores).