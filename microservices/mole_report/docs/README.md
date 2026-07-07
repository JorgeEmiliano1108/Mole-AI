# mole_report — Guía de arquitectura y cumplimiento

## 1. Glosario de dominio

| Término | Definición |
|---------|-----------|
| **Reporte** | Documento PDF generado asíncronamente con telemetría de sensores, insights LLM y gráficas de tendencia |
| **ReportJob** | Trabajo de generación de reporte con estado (`QUEUED`, `STARTED`, `SUCCESS`, `FAILED`) y progreso |
| **JobMetadataStore** | Almacenamiento en Redis del estado, progreso y resultado de cada `ReportJob` |
| **Presigned URL** | URL firmada de S3/MinIO con expiración (24h) para descarga segura del PDF |
| **AuditRecord** | Registro de auditoría persistido en Supabase (`reports_audit`) con trazabilidad completa |
| **Ownership check** | Verificación de que el `hashed_user_id` del JWT coincide con el creador del reporte |
| **RAG context** | Contexto científico obtenido por búsqueda semántica en pgvector (`rag_knowledge_chunks`) |
| **CAG** | Cache-Augmented Generation: logs históricos precargados antes de la inferencia LLM |
| **COFEPRIS** | Comisión Federal para la Protección contra Riesgos Sanitarios; disclaimer legal en todo PDF |
| **STACK** | Conjunto de dependencias: FastAPI + Celery/Redis + WeasyPrint + Matplotlib + pgvector + NVIDIA NIM |

## 2. Stack tecnológico

| Componente | Tecnología | Uso |
|-----------|-----------|-----|
| API | FastAPI + Uvicorn | Endpoints REST |
| Task queue | Celery + Redis | Generación asíncrona de reportes |
| PDF | WeasyPrint + Jinja2 | Renderizado HTML → PDF in-memory |
| Charts | Matplotlib (OO API) | Gráficas de tendencia de sensores |
| Vector store | pgvector (read-only) | Búsqueda semántica en `rag_knowledge_chunks` |
| LLM | NVIDIA NIM (OpenAI-compatible) | Síntesis de anomalías y recomendaciones agronómicas |
| Storage | MinIO / S3 | Almacenamiento de PDFs + presigned URLs |
| Auth | JWT HS256 (local) | Validación sin Supabase ni JWKS externos |
| Cache/state | Redis | `JobMetadataStore`: estado, progreso, resultado |
| Metrics | Prometheus / fastapi-instrumentator | `/metrics` vía instrumentador automático |
| Logging | structlog | Logs estructurados sin PII |
| Config | pydantic-settings | Centralizado en `app/config.py` |
| DB driver | asyncpg | Pool de conexiones a PostgreSQL con pgvector |
| HTTP | httpx | Cliente REST para Supabase |
| Resilience | tenacity | Retry con backoff exponencial en NIM, Supabase y S3 |

## 3. Variables de entorno

| Variable | Default | Obligatoria | Propósito |
|----------|---------|-------------|-----------|
| `ms3_host` | `0.0.0.0` | No | Host del servidor Uvicorn |
| `ms3_port` | `8003` | No | Puerto del servidor Uvicorn |
| `ms3_redis_url` | `redis://mole_ai_redis:6379` | No | URL de Redis para `JobMetadataStore` |
| `ms3_celery_broker_url` | — | No | Broker de Celery (default = `ms3_redis_url`) |
| `ms3_celery_result_backend` | — | No | Backend de Celery (default = `ms3_redis_url`) |
| `ms3_task_soft_time_limit` | `600` | No | Soft time limit para tareas Celery (segundos) |
| `ms3_storage_backend` | `minio` | No | Backend de almacenamiento: `minio` o `s3` |
| `ms3_s3_endpoint` | — | No | Endpoint del servidor S3/MinIO |
| `ms3_s3_access_key` | `""` | Sí* | Access key para S3 (*requerido si storage=s3) |
| `ms3_s3_secret_key` | `""` | Sí* | Secret key para S3 |
| `ms3_s3_bucket` | `mole-ai-production` | No | Bucket para almacenar PDFs |
| `ms3_supabase_url` | — | No | URL de Supabase para telemetría y auditoría |
| `ms3_supabase_key` | — | No | API key de Supabase |
| `nvidia_api_key` | — | No | API key para NVIDIA NIM (LLM de reportes) |
| `nvidia_base_url` | `https://integrate.api.nvidia.com/v1` | No | Base URL de la API NVIDIA NIM |
| `nvidia_report_model` | `meta/llama-3.3-70b-instruct` | No | Modelo LLM para síntesis de reportes |
| `origen_permitido` | `""` | No | Orígenes CORS permitidos (separados por coma) |
| `cors_allow_credentials` | `false` | No | Permitir credenciales en CORS |
| `debug` | `false` | No | Modo debug |
| `database_url` | — | Sí | URL de PostgreSQL con pgvector (`postgresql://user:pass@host:port/db`) |
| `jwt_secret_key` | `""` | Sí | Clave secreta JWT para validación HS256 |
| `REDIS_URL` | — | No | URL alternativa de Redis (lee `ms3_redis_url` si no está definida) |
| `DATABASE_URL` | — | Sí | Alias para `database_url` (lee ambas) |

**Nota**: Las variables con prefijo `ms3_` se leen directamente desde pydantic-settings, sin necesidad de `os.getenv`. Los alias (`REDIS_URL`, `DATABASE_URL`) se cargan en `from_env()`.

## 4. Capas y estructura del código

```
mole_report/
├── app/                          # Capa de aplicación (FastAPI)
│   ├── main.py                   # FastAPI app, CORS, health, metrics
│   ├── config.py                 # pydantic-settings centralizado
│   └── api/
│       ├── v1/reports.py         # Endpoints REST de reportes
│       └── dependencies.py       # JWT validation (HS256) + user extraction
├── application/                  # Capa de aplicación (Casos de uso)
│   ├── use_cases/
│   │   └── generate_report_use_case.py  # Orquestación completa del reporte
│   └── services/
│       └── report_builder.py     # Builder: HTML + Matplotlib chart + Jinja2 template
├── domain/                       # Capa de dominio (Entidades)
│   ├── schemas.py                # ReportRequest, ReportJob, ReportResult
│   └── __init__.py
├── infrastructure/               # Capa de infraestructura (Adaptadores)
│   ├── celery_app.py             # Celery app factory
│   ├── db/supabase_client.py     # Cliente REST para Supabase (sensor_logs, audit)
│   ├── llm/nvidia_client.py      # Cliente NVIDIA NIM (OpenAI SDK)
│   ├── pdf/weasyprint_report_generator.py  # PDF engine (WeasyPrint in-memory)
│   ├── redis/job_metadata_store.py  # Redis hash store para job metadata
│   ├── storage/s3_adapter.py     # S3/MinIO adapter (upload + presigned URL)
│   ├── vector/pgvector_adapter.py  # Read-only pgvector para RAG context
│   └── workers/tasks.py          # Tareas Celery (generate_report_task)
├── tests/                        # Tests
│   ├── conftest.py               # Fixtures: fake_env_vars, fake_job_store, fake_supabase, fake_nvidia
│   ├── test_api_reports.py       # 7 tests de API (requiere TestClient; salta localmente)
│   ├── test_celery_app.py        # 3 tests: creación, broker URL, soft time limit
│   ├── test_domain_schemas.py    # 4 tests: ReportRequest, ReportJob, ReportResult
│   ├── test_job_metadata_store.py  # 6 tests: CRUD sobre Redis mock
│   ├── test_nvidia_client.py     # 2 tests: sin API key, build_user_message
│   ├── test_pgvector_adapter.py  # 4 tests: no DB URL, pool creation, resultados, encode
│   ├── test_smoke.py             # 2 tests: build_trend_image, faiss (skipped)
│   └── test_supabase_client.py   # 4 tests: fetch logs, diagnostics, audit, from_env
├── Dockerfile                    # Multi-stage: builder → development → production
├── requirements.txt              # Dependencias directas
└── .github/workflows/            # CI pipeline
```

## 5. Mapa de adaptadores (Puertos y Adaptadores)

| Protocolo / Puerto | Implementación | Test Double |
|-------------------|---------------|-------------|
| Redis (hash store) | `JobMetadataStore` (infrastructure/redis) | `MagicMock` en `fake_job_store` |
| Supabase REST | `SupabaseClient` (infrastructure/db) | `MagicMock` en `fake_supabase` |
| NVIDIA NIM (LLM) | `NvidiaReportClient` (infrastructure/llm) | `MagicMock` en `fake_nvidia` |
| S3/MinIO | `S3Adapter` (infrastructure/storage) | No test double (boto3 directo) |
| pgvector | `PgVectorAdapter` (infrastructure/vector) | Mock de `asyncpg` + `OpenAI` |
| Celery workers | `generate_report_task` (infrastructure/workers) | `send_reminder.delay` mockeable |
| PDF rendering | `WeasyPrintReportGenerator` (infrastructure/pdf) | No test double |

## 6. Reglas obligatorias

1. **PII**: Nunca almacenar PII en Redis ni logs. Solo `hashed_user_id` (SHA-256 del `sub` del JWT).
2. **Logs**: Usar `structlog`. No loguear cuerpos de requests ni tokens JWT.
3. **REGLA_DE_ORO**: Cualquier error en adaptador externo (Supabase, NVIDIA, S3, pgvector) **nunca** debe tumbar la tarea Celery. Capturar excepción, loguear, continuar.
4. **Config**: Toda configuración vía `settings.*` (pydantic-settings). Cero `os.getenv` fuera de `config.py`.
5. **Zero MagicMock en tests de dominio**: Usar `MagicMock` solo para adaptadores. Schemas Pydantic se prueban con instancias reales.

## 7. Workflow típico (nueva feature)

```
1. Definir/actualizar entidad en domain/schemas.py (Pydantic)
2. Escribir test de dominio (sin mocks, instancias reales)
3. Implementar adaptador en infrastructure/ (con tests mockeando IO)
4. Agregar/actualizar caso de uso en application/use_cases/
5. Exponer endpoint en app/api/v1/reports.py (con JWT + ownership check)
```

## 8. Endpoints

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | `/generate` | JWT | Encola generación asíncrona de reporte (retorna `job_id`) |
| GET | `/{job_id}/status` | JWT + ownership | Estado del reporte (`QUEUED`, `STARTED`, `SUCCESS`, `FAILED`) |
| GET | `/{job_id}/download` | JWT + ownership | URL firmada de descarga (presigned S3, 24h TTL) |
| GET | `/health` | Público | Health check (`{"status": "ok"}`) |
| GET | `/metrics` | Público | Métricas Prometheus |
| GET | `/config` | Público | Estado de configuración (debug, puerto, DB conectada) |

## 9. Flujo de datos (Pipeline de generación de reporte)

```
POST /generate (JWT + ReportRequest)
  │
  ├── 1. JobMetadataStore.create_job()         # Redis: {status: QUEUED}
  ├── 2. generate_report_task.delay()           # Celery: encola tarea
  │
  └── [Celery worker — generate_report_task]
        │
        ├── 3. SupabaseClient.fetch_sensor_logs()   # 30/60/90 días
        ├── 4. PgVectorAdapter.search()             # RAG: pgvector → contexto científico
        ├── 5. NvidiaReportClient.synthesize_insights() # LLM: anomalías + recomendaciones
        ├── 6. ReportBuilder.build_report_html()    # HTML + Matplotlib chart
        ├── 7. WeasyPrintReportGenerator.generate_pdf()  # HTML → PDF (in-memory, cero disco)
        ├── 8. S3Adapter.upload_bytes()             # Subir PDF a S3/MinIO
        ├── 9. S3Adapter.generate_presigned_url()   # URL firmada 24h
        ├── 10. JobMetadataStore.set_result()       # Redis: {status: SUCCESS, result: url}
        └── 11. SupabaseClient.insert_audit_record() # Supabase: reports_audit
```

## 10. Generación de PDF

- **Stack**: WeasyPrint + Jinja2 + Matplotlib (OO API, sin `pyplot` para thread-safety)
- **Pipeline**: Jinja2 template → HTML inline → Matplotlib chart en base64 → WeasyPrint → PDF en `io.BytesIO`
- **Disclaimer**: COFEPRIS inyectado automáticamente si no está presente en el HTML
- **Cero disco**: El PDF se genera y sube completamente en memoria. Sin archivos temporales.
- **Matplotlib**: API orientada a objetos (`Figure`, `FigureCanvas`). Sin estado global. `gc.collect()` post-render.

## 11. Entorno E2E y tests

| Indicador | Valor |
|-----------|-------|
| Tests totales | 27 (25 pasan, 2 skipped, 7 API saltan localmente por conflicto starlette) |
| Cobertura | ~74% (objetivo ≥80% — se alcanza en CI con Docker) |
| `os.getenv` en producción | 6 en `config.py:from_env()` (compatibilidad legacy); 0 fuera de `config.py` |
| MagicMock | Solo en adaptadores (supabase, redis, nvidia) |
| Zero MagicMock en dominio | Sí — `domain/schemas.py` probado con instancias reales |
| CI pipeline | lint (ruff) → test (pytest-cov) → license check (pip-licenses) → build (Docker) |

### Fixtures disponibles (`tests/conftest.py`)

| Fixture | Propósito |
|---------|-----------|
| `fake_env_vars` | Variables de entorno para tests (monkeypatch) |
| `fake_job_store` | `JobMetadataStore` con `MagicMock` de Redis |
| `fake_supabase` | `SupabaseClient` mockeado con datos de prueba |
| `fake_nvidia` | `NvidiaReportClient` mockeado con respuesta dummy |

## 12. Cumplimiento de licencias

### 12.1 Política

Código cerrado (propietario). Prohibido el uso de dependencias con licencias GPL, LGPL, AGPL o cualquier variante copyleft fuerte.
Verificado automáticamente en CI con `pip-licenses --fail-on="GPL;LGPL;AGPL;GPLv2;GPLv3;LGPLv2;LGPLv3"`.

### 12.2 Dependencias directas verificadas

| Paquete | Versión | Licencia |
|---------|---------|----------|
| fastapi | 0.104.1 | MIT |
| uvicorn | 0.24.0 | BSD-3-Clause |
| celery | 5.3.1 | BSD-3-Clause |
| redis | 4.6.0 | MIT |
| weasyprint | 57.0 | BSD-3-Clause |
| matplotlib | 3.8.1 | PSF/BSD |
| httpx | 0.24.1 | BSD-3-Clause |
| boto3 | 1.28.0 | Apache-2.0 |
| jinja2 | 3.1.2 | BSD-3-Clause |
| python-dotenv | 1.0.0 | BSD-3-Clause |
| openai | >=1.0 | Apache-2.0 |
| tenacity | >=8.2 | Apache-2.0 |
| pydantic | >=2.7 | MIT |
| pydantic-settings | >=2.2 | MIT |
| PyJWT | >=2.8 | MIT |
| cryptography | >=42.0 | Apache-2.0 / BSD |
| pydyf | <0.12 | BSD-3-Clause |
| prometheus-fastapi-instrumentator | >=6.1 | MIT |
| structlog | >=24.1 | Apache-2.0 / MIT |
| asyncpg | >=0.29 | Apache-2.0 |

### 12.3 Notas de implementación

- **Dependencias eliminadas en remediación**: `pypdf` (posible PII en metadatos), `aiofiles` (no usado)
- **Código muerto eliminado**: `minio_client.py`, `huggingface_client.py`, `faiss_reader_adapter.py`
- **WeasyPrint**: Usa bibliotecas C del sistema (`libcairo2`, `libpango`, etc.), no afectan licencia del código Python
- **Matplotlib**: Usa API OO (sin `pyplot`) para thread-safety en Celery. Cero estado global

## 13. Desarrollo local con MinIO

Por defecto `STORAGE_BACKEND=minio`. Para desarrollo local:

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  quay.io/minio/minio server /data --console-address ":9001"

docker exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec minio mc mb local/reportes

export MS3_STORAGE_BACKEND=minio
export MS3_S3_ENDPOINT=http://localhost:9000
export MS3_S3_ACCESS_KEY=minioadmin
export MS3_S3_SECRET_KEY=minioadmin
export MS3_S3_BUCKET=reportes
export MS3_S3_REGION=us-east-1

uv run python -m app.main
```

### 12.4 Herramientas de verificación en CI

- `pip-licenses` con `--fail-on` para licencias GPL/LGPL/AGPL
- `ruff check` para linting
- `pytest-cov` con umbral mínimo de cobertura
- Docker build multi-stage verifica imagen producible

## 14. Bugs corregidos

| Fecha | Bug | Archivo | Solución |
|-------|-----|---------|----------|
| 2026-07-06 | `settings.HOST`/`settings.PORT` causaban `AttributeError` al iniciar el servicio — los campos correctos son `ms3_host`/`ms3_port` | `main.py:47` | Cambiado a `settings.ms3_host`/`settings.ms3_port`. Eliminada variable `PORT=8003` de `docker-compose.yml` y `docker-compose.e2e.yml` (redundante con default `ms3_port=8003`).
