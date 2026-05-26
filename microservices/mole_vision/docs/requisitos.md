# Requisitos del Microservicio mole_vision

## 1. Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Framework API | FastAPI | 0.110.0 |
| Servidor ASGI | Uvicorn | 0.29.0 |
| Runtime ML | TensorFlow Lite | 2.14.0 |
| Cache/Pub-Sub | Redis | 5.0.3 (asyncio) |
| Autenticación | Supabase JWT (ES256) | - |
| Serialización | Pydantic | >=2.7 |
| Configuración | pydantic-settings | >=2.0 |
| Logging | structlog | >=24.0 |
| Procesamiento Imágenes | Pillow | 10.2.0 |
| Computación Numérica | NumPy | 1.26.4 |
| Criptografía | hashlib (SHA-256) | Built-in |

## 2. Diagrama Textual de Arquitectura Hexagonal

```
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA API (INPUT)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ main.py      │  │ routers.py   │  │ dependencies.py       │ │
│  │ (FastAPI)    │  │ (Endpoints)  │  │ (DI + EXIF Sanitization)│ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   CAPA APPLICATION                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AnalyzePlantUseCase                         │   │
│  │  - vision_client: VisionClientPort                       │   │
│  │  - event_publisher: EventPublisherPort                   │   │
│  │  - diagnostic_repository: DiagnosticRepositoryPort      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PUERTOS (Ports)                                         │   │
│  │ - VisionClientPort (analyze async)                      │   │
│  │ - EventPublisherPort (publish async)                   │   │
│  │ - DiagnosticRepositoryPort (save sync)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   CAPA INFRASTRUCTURE                           │
│  ┌────────────────┐ ┌─────────────────┐ ┌──────────────────┐      │
│  │ tflite_adapter │ │redis_publisher  │ │supabase_adapter │      │
│  │ (Vision)       │ │ (Events)        │ │ (Persistence)   │      │
│  │ run_in_thread  │ │ redis.asyncio   │ │                 │      │
│  └────────────────┘ └─────────────────┘ └──────────────────┘      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      CAPA DOMAIN                                 │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐      │
│  │ entities.py   │  │ schemas.py     │  │ enums.py         │      │
│  │ DiagnosticRes │  │ Pydantic Models│  │ SeverityLevel   │      │
│  └───────────────┘  └────────────────┘  └──────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Requisitos Funcionales (RF)

### RF-01: Autenticación JWT
- Validar tokens JWT de Supabase mediante криптоасимметричная validación ES256
- Descargar llaves públicas desde JWKS endpoint de Supabase
- Cache en memoria con TTL configurables (default 300s)
- Pseudo-anonimización de PII en logs mediante SHA-256

### RF-02: Inferencia de Diagnóstico
- Recepcinar imagen sanitizada (EXIF limpio)
- Ejecutar inferencia CNN (TFLite) en ThreadPool
- Retornar resultado con especie, condición, severidad, confianza, pH

### RF-03: Publicación de Eventos
- Publicar evento diagnostic.completed en Redis (canal: mole_vision:diagnostics)
- Manejar fallo de Redis con warning (no blocking)

### RF-04: Persistencia de Diagnóstico
- Guardar resultado en Supabase (DiagnosticRepository)

### RF-05: Sanitización EXIF
- Limpiar metadatos GPS/EXIF de imagen cargada
- Usar Pillow + run_in_threadpool

## 4. Requisitos No Funcionales (RNF)

### RNF-01: Latencia (SLA)
| Endpoint | Latencia Máx |
|----------|-------------|
| POST /analyze | ≤1000ms |
| POST /analyze-ph-strip | ≤1000ms |
| GET /health | ≤50ms |
| GET /healthz | ≤200ms |

### RNF-02: Throughput
- Capacidad: 5 requests/segundo (sin batch)

### RNF-03: Seguridad
- Autenticación: ES256 + JWKS (Zero-Trust)
- CORS: Configurable via ORIGEN_PERMITIDO
- Sanitización EXIF: Obligatoria
- Pseudo-anonimización PII: SHA-256 en logs (LFPDPPP)

### RNF-04: Disponibilidad
- Health checks: /health (básico), /healthz (completo)
- Modelo TFLite pre-cargado en startup

### RNF-05: Compliance LFPDPPP
- Hash SHA-256 de identificadores de usuario en logs
- Limpiar metadatos EXIF (GPS)
- No registrar emails, nombres, IPs en logs

## 5. Endpoints Actuales

| Método | Path | Descripción | Auth |
|--------|------|-------------|------|
| POST | /api/v1/vision/analyze | Diagnóstico fitosanitario | JWT |
| POST | /api/v1/vision/analyze-ph-strip | Análisis pH tira reactiva | JWT |
| GET | /api/v1/vision/health | Health básico | Público |
| GET | /api/v1/vision/healthz | Health completo | Público |

## 6. Consideraciones de Despliegue

- **Modelo ML**: Volumen Docker estático (`/app/models/cnn.tflite`, `/app/models/labels.json`)
- **Redis**: Conexión via `redis://redis:6379/0`
- **Supabase**: Auth via `https://osmhchhvdutkmimrclyq.supabase.co`
- **ThreadPool**: 4 threads para inferencia TFLite