# mole_vision — Detección de Plagas y Enfermedades

Microservicio para diagnóstico fitosanitario con detección especializada de plagas/enfermedades en cualquier especie vegetal y etapa de crecimiento. Usa **NVIDIA NIM (Llama 3.2 Vision‑Instruct)** como único motor de inferencia. Mock disponible solo en `tests/fakes/` para CI.

## Stack

| Componente | Tecnología |
|------------|-----------|
| Framework API | FastAPI 0.110 |
| ASGI | Uvicorn 0.29 |
| Motor de visión | NVIDIA NIM (Llama 3.2 Vision‑Instruct) |
| Fallback CI/dev | MockVisionAdapter (en `tests/fakes/`) |
| Ontología | `PlantDiagnosis` (15 campos: especie, etapa, plaga, severidad, progresión, recomendaciones) |
| Protección especies | NOM-059-SEMARNAT (sentinel LLM + regex post-inferencia) |
| Cache/Pub-Sub | Redis asyncio |
| Logging | structlog JSON |
| Resilience | tenacity (exponential backoff 2–15s, 3 retries) |
| Rate limiting | slowapi (5 req/min por IP) |
| Auth | JWT HS256 (PyJWT, sin fetch remoto JWKS) |
| Config | pydantic-settings (0 os.getenv fuera de config.py) |
| Observabilidad | Prometheus + OpenTelemetry |
| Procesamiento imágenes | Pillow (EXIF stripping) |

## Arquitectura

```
POST /api/v1/vision/analyze
  → FastAPI (JWT HS256 + EXIF sanitization + rate limit 5/min)
    → AnalyzePlantUseCase
      → VisionClientPort (NVIDIA NIM)
      → EventPublisherPort (Redis pub/sub)
      → DiagnosticRepositoryPort (stub)
    → NOM-059 species check (403 if protected)
    → PlantDiagnosis (species, growth_stage, affliction, severity, progression, recommendations)
```

## Endpoints

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/v1/vision/analyze` | JWT HS256 | Diagnóstico fitosanitario (15 campos: especie, etapa, plaga, severidad, progresión, recomendaciones) |
| GET | `/api/v1/vision/health` | Público | Health básico |
| GET | `/api/v1/vision/healthz` | Público | Health con verificación de componentes |
| GET | `/metrics` | Público | Métricas Prometheus |
| GET | `/config` | Público | Estado de configuración |

## Tests

51 tests unitarios, 0 failed, 90% cobertura.

```bash
pytest tests/ --cov=app --cov-fail-under=60
```

CI usa `--cov-fail-under=60`. Cobertura real ~90%.

## Estado de auditoría

| Categoría | Estado |
|-----------|--------|
| Tests | 51 unitarias, 0 failed, cobertura ≥60% en CI |
| `os.getenv` en producción | 0 (centralizado en config.py) |
| JWT | HS256 unificado (security.py eliminado) |
| Circuit breaker | tenacity en nvidia_client.py (3 retries, backoff 2–15s) |
| Ontología diagnóstico | `PlantDiagnosis` — especie común/científica, etapa crecimiento, plaga/enfermedad, severidad, progresión, recomendaciones |
| NOM-059 especies protegidas | ✅ Dos capas: prompt LLM + `check_nom059_violation()` post-inferencia (403 si detectada) |
| Fallback visión | NVIDIA NIM solo; Mock en `tests/fakes/` para CI (TFLite eliminado) |
| Docker | Multi-stage + USER appuser + HEALTHCHECK |
| CI/CD | `.github/workflows/ci_vision.yml` (lint → test → license → build) |
| Dependencias | `requirements.lock` + gate GPL/LGPL en CI |
| LFPDPPP | EXIF stripping (`dependencies.py:30-46`), PII hasheada (`privacy.py`), structlog JSON |
| Cross-repo coupling | Roto (`app/core/privacy.py` local) |

## Deuda técnica

Ver `docs/requisitos.md §8` para lista completa. Principales:

- Supabase adapter es stub (no persiste)
- Pipeline MLOps (training_pipeline.py, vision_listener.py) sin tests
- Logger dual: `app/core/logger.py` vs structlog

## Documentación

- [`docs/requisitos.md`](docs/requisitos.md) — Requisitos funcionales y no funcionales, ADRs, deuda técnica
- [`docs/audit.md`](docs/audit.md) — Auditoría de seguridad y cumplimiento
