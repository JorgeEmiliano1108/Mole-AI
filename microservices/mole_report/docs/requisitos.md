# Requisitos del Microservicio mole_report (MS-3)

## 1. Requisitos Funcionales

### 1.1 Generación de Reportes

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-01 | Generar reporte asíncrono | Encolar generación vía Celery. Retorna `job_id` inmediatamente sin bloquear | POST `/generate` responde en <500ms con `{"job_id": "<uuid>", "status": "queued"}` |
| RF-02 | Consultar estado | Polling del progreso del reporte desde `QUEUED` → `STARTED` → `SUCCESS` / `FAILED` | GET `/{job_id}/status` retorna `status` + `progress` (0–100) |
| RF-03 | Descargar PDF | Obtener URL firmada de S3 con expiración (24h por defecto) | GET `/{job_id}/download` retorna `{"download_url": "<presigned_url>"}` |

### 1.2 Seguridad y Ownership

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-04 | Ownership check | Solo el creador del reporte puede ver estado o descargar | 403 si `hashed_user_id` del JWT no coincide con el del `JobMetadataStore` |
| RF-05 | Disclaimer COFEPRIS | Aviso legal en todo PDF generado | El HTML renderizado contiene la palabra "COFEPRIS"; si no, se inyecta automáticamente |

### 1.3 Contexto RAG + LLM

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-06 | Búsqueda semántica en pgvector | Contexto científico desde `rag_knowledge_chunks` para enriquecer el reporte | `PgVectorAdapter.search()` retorna contenido relevante o `""` si falla (non-fatal) |
| RF-07 | Síntesis de anomalías vía LLM | Detección estadística (media ± 2σ) + insights de NVIDIA NIM | `NvidiaReportClient.synthesize_insights()` retorna `summary` + `text`; si no hay API key, retorna mensaje de error controlado |
| RF-08 | Cache-Augmented Generation (CAG) | Precarga de logs históricos (30/60/90 días) antes de la inferencia LLM | `SupabaseClient.fetch_sensor_logs()` para 30, 60 y 90 días combinados |

### 1.4 Auditoría

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-09 | Registro de auditoría | Persistir cada generación en Supabase (`reports_audit`) con job_id, status, timestamps | `insert_audit_record()` llamado al inicio (FAILED) y al final (SUCCESS/FAILED) |
| RF-10 | Datos sintéticos en demo | PDF demo sin PII real | `reporte_ejemplo_anonimizado.pdf` disponible para pruebas |

## 2. Requisitos No Funcionales

### 2.1 Rendimiento

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-01 | Timeout LLM | Límite de espera para respuesta de NVIDIA NIM | Timeout del cliente OpenAI configurado a 120s; retry 3 intentos con backoff exponencial |
| RNF-02 | Sin I/O a disco | PDF generado completamente en memoria | Cero escritura a disco en `generate_report_use_case.py`; uso de `io.BytesIO` |

### 2.2 Seguridad

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-03 | Sin PII en Redis | Solo `hashed_user_id` (SHA-256) almacenado en JobMetadataStore | El sub del JWT se hashea con `hashlib.sha256()` antes de persistir |
| RNF-04 | Sin PII en logs | structlog configurado sin datos personales | Ningún log contiene emails, tokens JWT, o valores de sensores sin anonimizar |
| RNF-05 | Presigned URL con expiración | URLs de descarga expiran automáticamente | `generate_presigned_url()` con `expires_in` (24h por defecto, 1h en fallback) |
| RNF-06 | Sin dependencias GPL/LGPL | Cero dependencias con licencia copyleft | Verificado en CI con `pip-licenses --fail-on` |

### 2.3 Operación

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-07 | Reintentos y circuit breaker | Tenacity con backoff exponencial en llamadas externas | `SupabaseClient`: retry en `httpx.RequestError`; `NvidiaReportClient`: retry en 429/5xx; `S3Adapter`: retry en `ClientError` |
| RNF-08 | Docker hardening | Multi-stage build + usuario no-root + HEALTHCHECK | `USER appuser` en development y production; HEALTHCHECK cada 30s |
| RNF-09 | Almacenamiento configurable | STORAGE_BACKEND seleccionable vía env var | `ms3_storage_backend: str = "minio"` en `config.py`; S3Adapter usa endpoint configurable |
| RNF-10 | Config centralizada | Cero `os.getenv` fuera de `config.py` | 6 ocurrencias de `os.getenv` dentro de `config.py:from_env()` (compatibilidad con variables legacy). 0 fuera de `config.py`. |
| RNF-11 | Graceful degradation | Fallo de cualquier adaptador externo no tumba la tarea | Cada llamada externa (Supabase, pgvector, NVIDIA, S3) wrapped en try/except con logging |
| RNF-12 | Retención de PDFs | TTL en S3/MinIO lifecycle | 90 días por defecto; configurable vía política de bucket |

## 3. Bugs corregidos

| Fecha | Bug | Solución | Archivo |
|------|-----|----------|---------|
| 2026-06-16 | `public_url` undefined en audit payload → `NameError` | Cambiado a `presigned_url` | `generate_report_use_case.py:105` |
| 2026-06-16 | Tests importaban `ms3_reports.*` (no existe) | Corregido a imports relativos | `test_smoke.py:5,14` |
| 2026-06-16 | 34 `os.getenv` en 10 archivos | Centralizados en `config.py` con `pydantic-settings` | Múltiples archivos |
| 2026-06-16 | `minio_client.py` código muerto (stubs) | Eliminado | `infrastructure/db/minio_client.py` |
| 2026-06-16 | `huggingface_client.py` nunca importado | Eliminado | `infrastructure/llm/huggingface_client.py` |
| 2026-06-16 | `faiss` reemplazado por pgvector (read-only) | Nuevo adaptador | `infrastructure/vector/pgvector_adapter.py` |
| 2026-06-16 | Sin `requirements.lock` | Generado con `pip-compile` | `requirements.lock` |
| 2026-06-16 | Docker sin HEALTHCHECK | Añadido | `Dockerfile` |
| 2026-06-16 | Development stage como root | `USER appuser` añadido | `Dockerfile` |
| 2026-06-16 | Sin tests de `celery_app.py` | Añadidos 3 tests | `tests/test_celery_app.py` |
| 2026-06-16 | Sin tests de `pgvector_adapter.py` | Añadidos 4 tests | `tests/test_pgvector_adapter.py` |
| 2026-07-06 | `settings.HOST`/`settings.PORT` en `main.py:47` — campos inexistentes (los correctos son `ms3_host`/`ms3_port`) → `AttributeError` al iniciar | Corregido a `settings.ms3_host`/`settings.ms3_port`. Eliminada `PORT=8003` de `docker-compose.yml` y `docker-compose.e2e.yml` (redundante con default). Añadido `test_startup.py` como test de regresión. | `main.py`, `docker-compose.yml`, `docker-compose.e2e.yml`, `tests/test_startup.py` |

## 4. Decisiones Arquitectónicas (ADRs)

### ADR-001: pgvector como reemplazo de FAISS para RAG en reportes

**Estado:** Implementado

**Contexto:**
El microservicio mole_report original usaba FAISS para búsqueda semántica en el contexto de generación de reportes. FAISS requería dependencias nativas difíciles de mantener en Docker multi-stage y duplicaba la funcionalidad de búsqueda que ya existía en mole_chat con pgvector. Además, FAISS almacenaba los índices localmente, lo que impedía compartir el conocimiento entre microservicios.

**Decisión:**
Reemplazar FAISS por un adaptador read-only a pgvector (`PgVectorAdapter`) que consulta la misma tabla `rag_knowledge_chunks` que usa mole_chat. El adaptador usa `asyncpg` para pool de conexiones y el SDK de OpenAI para generar embeddings vía NVIDIA NIM.

**Consecuencias:**
- Positivas: Elimina dependencias nativas (FAISS), comparte conocimiento con mole_chat, arquitectura más simple (un solo vector store), el adaptador read-only no puede corromper datos
- Negativas: Requiere conexión a PostgreSQL con pgvector habilitado; dependencia de red para búsqueda semántica
- Mitigación: Si pgvector no está disponible, `search()` retorna `""` (non-fatal, graceful degradation)

### ADR-002: STORAGE_BACKEND=minio como default

**Estado:** Implementado

**Contexto:**
Originalmente mole_report asumía S3 como único backend de almacenamiento, lo que impedía el desarrollo local sin conexión a AWS. El código de configuración dependía de variables de entorno de AWS directas (`AWS_ACCESS_KEY_ID`, etc.).

**Decisión:**
Configurar `ms3_storage_backend: str = "minio"` como valor por defecto. `S3Adapter` acepta un endpoint configurable que puede apuntar a MinIO local o a S3 real. Las variables de entorno legacy (`AWS_*`, `AWS_STORAGE_BUCKET_NAME`) se usan como fallback si las nuevas (`MS3_S3_*`) no están definidas.

**Consecuencias:**
- Positivas: Desarrollo local sin AWS, misma interfaz `S3Adapter` para ambos backends, sin cambios en el caso de uso
- Negativas: `S3Adapter` sigue importando `boto3` incluso cuando se usa MinIO (biblioteca compartida aceptable)
- Documentación: README incluye guía paso a paso para levantar MinIO local

### ADR-003: pydantic-settings como config centralizada

**Estado:** Implementado

**Contexto:**
El código original tenía 34 ocurrencias de `os.getenv` distribuidas en 10 archivos, lo que dificultaba la auditoría de configuración, el tipado de variables y la documentación de defaults. No existía un punto único de verdad para la configuración.

**Decisión:**
Migrar toda la configuración a `app/config.py` usando `pydantic-settings.BaseSettings` con un método de clase `from_env()` que centraliza los pocos `os.getenv` restantes (necesarios por compatibilidad con variables legacy). El resto del código accede a `settings.*` properties tipadas.

**Consecuencias:**
- Positivas: 0 `os.getenv` en producción, configuración tipada con defaults explícitos, documentación auto-generable, separación clara entre config nueva (`MS3_*`) y legacy (`AWS_*`, `DATABASE_URL`)
- Negativas: El método `from_env()` retiene 6 `os.getenv` para compatibilidad con variables legacy (transición controlada)
- Fase futura: Eliminar `from_env()` y mover los fallbacks legacy a alias de `pydantic-settings` con `Field(validation_alias=...)`

### ADR-004: Celery con acks_late + retry backoff para tareas de reportes

**Estado:** Implementado

**Contexto:**
La generación de reportes es una operación de larga duración (hasta 10 minutos) que involucra múltiples llamadas externas (Supabase, pgvector, NVIDIA NIM, S3). Si el worker falla o se reinicia, la tarea debe ser re-ejecutada sin perder el mensaje del broker.

**Decisión:**
Configurar Celery tasks con `acks_late=True`, `task_reject_on_worker_lost=True`, `autoretry_for=(Exception,)`, `retry_backoff=True`, `max_retries=3`. Además, un `ReportTaskBase` base class maneja el fallo final actualizando el estado del job a `FAILED` en Redis.

**Consecuencias:**
- Positivas: Tolerancia a fallos de workers, retry con jitter, estado consistente incluso en fallo extremo
- Negativas: `acks_late` requiere workers persistentes; tareas pueden ejecutarse más de una vez (idempotencia por diseño: `S3Adapter` sobrescribe el PDF)
- CV: `worker_prefetch_multiplier = 1` evita acaparar mensajes

### ADR-005: JWT HS256 local sin Supabase Auth

**Estado:** Implementado

**Contexto:**
Originalmente se planeó delegar la validación JWT a Supabase Auth (JWKS remoto), lo que introducía dependencia de red y latencia en cada request. Además, el resto de microservicios (mole_chat) ya usaban validación local con JWKS caching.

**Decisión:**
Validar JWT localmente con `PyJWT` y algoritmo HS256 usando `JWT_SECRET_KEY` (o `SUPABASE_JWT_SECRET` como fallback). No hay llamado a Supabase Auth ni a endpoints JWKS. El usuario se extrae del token y se hashea con SHA-256 para LFPDPPP.

**Consecuencias:**
- Positivas: Sin latencia de red para auth, sin dependencia de Supabase Auth, mismo patrón que mole_chat
- Negativas: Rotación de secret requiere reinicio del servicio; no soporta tokens emitidos por third parties que usen RS256/ES256
- Seguridad: El secreto se lee de env var y nunca se loguea
