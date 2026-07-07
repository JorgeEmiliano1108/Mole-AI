# Requisitos del Microservicio mole_vision (MS-1)

## 1. Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Framework API | FastAPI | 0.110.0 |
| Servidor ASGI | Uvicorn | 0.29.0 |
| Motor de visión | NVIDIA NIM (Llama 3.2 Vision‑Instruct) | OpenAI-compatible |
| Fallback CI/dev | MockVisionAdapter | — |
| Cache/Pub-Sub | Redis | 5.0.3 (asyncio) |
| Autenticación | JWT HS256 (local) | PyJWT |
| Serialización | Pydantic | >=2.7 |
| Configuración | pydantic-settings | >=2.0 |
| Logging | structlog | >=24.0 |
| Procesamiento Imágenes | Pillow | 10.2.0 |
| Computación Numérica | NumPy | 1.26.4 |
| Criptografía | hashlib (SHA-256) | Built-in |
| Resilience | tenacity | >=8.2 |
| Observabilidad | Prometheus / OpenTelemetry | — |
| Rate Limiting | slowapi | 0.1.9 |

## 2. Diagrama Textual de Arquitectura Hexagonal

```
POST /api/v1/vision/analyze
  → FastAPI (JWT HS256 + EXIF sanitization + rate limit 5/min)
    → AnalyzePlantUseCase
      → VisionClientPort (NVIDIA NIM)
      → EventPublisherPort (Redis pub/sub)
      → DiagnosticRepositoryPort (stub)
    → NOM-059 check (403 si especie protegida)
    → PlantDiagnosis (15 campos)
```

## 3. Requisitos Funcionales (RF)

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-01 | Autenticación JWT HS256 | Validar tokens locales sin fetch remoto | `dependencies.py:get_current_user()` — 401 si inválido |
| RF-02 | Inferencia NVIDIA NIM | Diagnóstico fitosanitario completo con detección de plagas/enfermedades vía Llama 3.2 Vision | Retorna `PlantDiagnosis` con: especie (común+científica), etapa crecimiento, plaga/enfermedad, severidad, progresión, recomendaciones, pH estimado |
| RF-03 | Fallback Mock | Si NVIDIA no está disponible (CI/dev sin GPU), usar adaptador mock en `tests/fakes/` | `get_vision_client()` intenta NVIDIA o lanza RuntimeError |
| RF-04 | Detección por etapa de crecimiento | El diagnóstico debe identificar la etapa del cultivo (plántula, vegetativa, floración, fructificación, senescencia) | `growth_stage` en `PlantDiagnosis` |
| RF-05 | Evaluación de progresión | El diagnóstico debe incluir etapa de progresión de la aflicción (inicial, avanzada, terminal) | `progression` en `PlantDiagnosis` |
| RF-06 | Recomendaciones accionables | El diagnóstico debe incluir acciones inmediatas, preventivas y de mitigación | Tres listas en `PlantDiagnosis` |
| RF-07 | Publicación de Eventos | Publicar `diagnostic.completed` en Redis | Canal: `mole_vision:diagnostics`; fallo no bloqueante |
| RF-08 | Persistencia de Diagnóstico | Guardar resultado en Repositorio | `save_diagnostic()` retorna UUID |
| RF-09 | Sanitización EXIF | Limpiar metadatos GPS/EXIF antes de inferencia | `clean_exif()` en `dependencies.py` vía `run_in_threadpool` |
| RF-10 | Anonimización PII | SHA-256 de plant_id en logs y eventos | `anonymize_id()` en `app/core/privacy.py` |
| RF-11 | NOM-059 especies protegidas | Bloquear diagnósticos que involucren especies protegidas por la NOM-059-SEMARNAT | 403 si `affliction_name == "ESPECIE_PROTEGIDA"` o regex coincide |

## 4. Requisitos No Funcionales (RNF)

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-01 | Latencia POST /analyze | ≤1000ms (NVIDIA NIM) | Medido en CI |
| RNF-02 | Rate limiting | 5 requests/minuto por IP | slowapi + `X-Forwarded-For` |
| RNF-03 | Circuit breaker | Tenacity con backoff en NVIDIA NIM | 3 retries, backoff 2-15s, solo 429/5xx |
| RNF-04 | Sin PII en logs | SHA-256 de identificadores | `anonymize_id()` + structlog JSON |
| RNF-05 | Sin EXIF en imágenes | Stripping antes de enviar a LLM externo | `clean_exif()` en pipeline |
| RNF-06 | Config centralizada | 0 `os.getenv` fuera de config.py | Verificado |
| RNF-07 | Dependencias bloqueadas | `requirements.lock` con `pip-compile` | CI verifica + gate GPL/LGPL |
| RNF-08 | Docker hardening | Multi-stage + USER appuser + HEALTHCHECK | Dockerfile |
| RNF-09 | CI/CD pipeline | Lint → test → license gate → build | `.github/workflows/ci_vision.yml` |
| RNF-10 | Cobertura de pruebas | ≥60% (`--cov-fail-under=60`) | 51 tests, 0 failed |
| RNF-11 | NOM-059-SEMARNAT | Bloqueo de especies protegidas en dos capas | Prompt LLM + `check_nom059_violation()` post-inferencia → 403 |

## 5. Endpoints

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/v1/vision/analyze` | JWT HS256 | Diagnóstico fitosanitario (PlantDiagnosis: especie, etapa, plaga, severidad, progresión, recomendaciones) |
| GET | `/api/v1/vision/health` | Público | Health básico |
| GET | `/api/v1/vision/healthz` | Público | Health completo con verificación de componentes |
| GET | `/metrics` | Público | Métricas Prometheus |
| GET | `/config` | Público | Estado de configuración |

## 6. Estado de auditoría

| Categoría | Estado |
|-----------|--------|
| Tests | 51 unitarias, 0 failed |
| Cobertura | ≥60% (verificado en CI con `--cov-fail-under=60`); real ~90% |
| `os.getenv` en producción | 0 (centralizado en `config.py`) |
| JWT | HS256 unificado (`security.py` ES256+JWKS eliminado) |
| Circuit breaker | tenacity en `nvidia_client.py` (3 retries, backoff 2-15s) |
| Ontología diagnóstico | `PlantDiagnosis` — 15 campos (especie, etapa, plaga, severidad, progresión, recomendaciones) |
| NOM-059 especies protegidas | ✅ Dos capas: prompt LLM + `check_nom059_violation()` post-inferencia |
| Fallback visión | NVIDIA NIM solo (TFLite eliminado); Mock en `tests/fakes/` |
| Docker | Multi-stage + USER appuser + HEALTHCHECK |
| Dependencias | `requirements.lock` generado con opentelemetry |
| CI/CD | `.github/workflows/ci_vision.yml` con lint → test → license → build |
| Config centralizada | Todos los campos migrados a `config.py` |
| Dominio | Formalizado: `PlantDiagnosis`, `DiagnosticEvent`, `GrowthStage`, `AfflictionType`, `ProgressionStage` |
| LFPDPPP | EXIF stripping + SHA-256 anonimización + structlog JSON |

## 7. Pipeline MLOps (entrenamiento continuo)

El microservicio incluye un pipeline de fine-tuning que corre en un proceso separado (`ProcessPoolExecutor`) para no bloquear el event loop de FastAPI. Este pipeline **no está activo por defecto** y carece de cobertura de tests.

| Componente | Archivo | Descripción |
|------------|---------|-------------|
| Listener | `app/infrastructure/adapters/vision_listener.py` | Redis Pub/Sub; descarga ZIP desde MinIO |
| Entrenamiento | `app/infrastructure/adapters/training_pipeline.py` | CNN fine-tuning con Keras; proceso aislado |
| Descarga S3 | `app/infrastructure/adapters/s3_downloader.py` | Descarga assets de MinIO |

> ⚠️ **Deuda técnica**: Pipeline MLOps sin cobertura de tests (ver §8 TD-03).

## 8. Deuda técnica

| ID | Severidad | Descripción | Archivo |
|----|-----------|-------------|---------|
| TD-01 | ✅ RESUELTO | `opentelemetry-api` + `opentelemetry-sdk` añadidos al lock | `requirements.lock:23-24` |
| TD-02 | ✅ RESUELTO | `TFLiteVisionAdapter`, `PhEstimation`, `_hot_swap_model` eliminados; `mock_vision.py` movido a `tests/fakes/` | — |
| TD-03 | **MEDIA** | Pipeline MLOps sin tests | `tests/` |
| TD-04 | **MEDIA** | `SupabaseDiagnosticRepository` es stub: `save_diagnostic()` retorna UUID sin persistir; `get_diagnostic()` lanza `NotImplementedError` | `adapters/supabase_adapter.py` |
| TD-05 | **MEDIA** | `test_vision_api.py` (E2E manual) usa 4 `os.environ.get` — no ejecutable en CI | `tests/test_vision_api.py` |
| TD-06 | **BAJA** | Logger dual: `app/core/logger.py` (JSONFormatter) vs structlog — no documentado | `app/core/logger.py` |
| TD-07 | **BAJA** | tenacity `@retry` es retry mechanism, no circuit breaker real (sin estado open/closed/half-open) | `nvidia_client.py:41-46` |
