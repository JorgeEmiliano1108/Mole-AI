# mole_chat — Guía de arquitectura y cumplimiento

## 1. Glosario de dominio

**PII (Información Personal Identificable)** — Emails, teléfonos o IDs de usuario. Deben enmascararse (`[EMAIL_OCULTO]`, `[TEL_OCULTO]`) o hashearse (SHA-256) en logs. Cumplimiento LFPDPPP.

**JWT / JWKS** — Autenticación mediante tokens ES256 verificados con JWKS cacheado (TTL 300s). Fallback HS256 si no hay JWKS URL configurada.

**Disclaimer / Ética IA** — Aviso legal COFEPRIS obligatorio en toda respuesta. `generated_by: "Mole.AI"` para transparencia algorítmica.

**Session Memory** — Persistencia de contexto conversacional por `session_id` en Redis con TTL 15 min. Permite diálogos multi-turno.

## 2. Stack tecnológico

| Componente | Tecnología |
|-----------|-----------|
| API | FastAPI + Uvicorn |
| Auth | JWT ES256 (JWKS) / HS256 fallback |
| Cache / Pub-Sub | Redis (redis.asyncio) |
| Vector store | pgvector + PostgreSQL |
| LLM | NVIDIA NIM (OpenAI-compatible) |
| Embeddings | NVIDIA nv-embedqa-e5-v5 |
| Logging | structlog |
| Config | pydantic-settings |

## 3. Capas y estructura del código

```
api/ → application/ → domain/ (protocols)
                         ↑
                 infrastructure/ (adapters)
```

- `app/api/` — endpoints FastAPI + middlewares
- `app/application/use_cases/` — lógica de negocio (`chat_usecase.py`)
- `app/domain/` — schemas + protocols (interfaces `@runtime_checkable`)
- `app/infrastructure/adapters/` — implementaciones concretas (DB, LLM, Redis)
- `app/core/` — config, security, circuit_breaker, logger
- `tests/` — unitarios (uso de fakes) e integración (`@pytest.mark.integration`)

## 4. Mapa de adaptadores (Puertos y Adaptadores)

| Puerto (Protocolo) | Implementación | Test double |
|---|---|---|
| `LLMClientPort` | `nvidia_client.py` | `FakeLLMClient` |
| `VectorStorePort` | `pgvector_store.py` | `FakeVectorStore` |
| `RedisAdapterPort` | `redis_sensor_cache_adapter.py` | `FakeRedisAdapter` |
| `CitationManagerPort` | `citation_manager.py` | — |
| `TokenValidatorPort` | `security.py` (JWKSValidator / HS256Validator) | `FakeTokenValidator` |

## 5. Reglas obligatorias

1. **PII** — `PIISanitizer.sanitize()` antes de enviar texto al LLM
2. **Logs** — `PIISanitizer.hash_user_id()` en `chat_usecase.py`
3. **REGLA DE ORO** — anteponer `REGLA_DE_ORO` a todo system_prompt
4. **Config** — usar `settings.*` de `app/core/config.py`, nunca `os.getenv`
5. **Tests** — NO usar `MagicMock`; preferir fakes de `tests/fakes.py`

## 6. Workflow típico (nueva feature)

1. Definir/actualizar protocolo en `domain/protocols.py`
2. Implementar adaptador en `infrastructure/adapters/`
3. Inyectar en `chat_usecase.py` (constructor)
4. Tests unitarios con fakes; integración si requiere red
5. Actualizar este archivo si cambia la estructura principal

## 7. Endpoints

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | /api/v1/mole-ai/chat | JWT | Chat RAG+CAG |
| POST | /api/v1/knowledge/ingest-pdf | JWT | Ingesta PDF |
| DELETE | /api/v1/knowledge/pdf/{doc_id} | JWT | Borra PDF |
| GET | /api/v1/health | Público | Health check |

## 8. Flujo de datos (RAG+CAG)

```
[HTTP Request + JWT]
       ↓
[get_current_user] → HTTPBearer + JWKSValidator
       ↓ (user_id validado)
[PIISanitizer.sanitize] → Limpia emails/teléfonos + hashea user_id
       ↓ (mensaje_seguro + user_hash)
[Redis (CAG)] ← telemetria
[pgvector (RAG)] ← contexto local (embeddings NVIDIA)
[Trefle.io] ← fallback (placeholder)
       ↓
[REGLA DE ORO] antepuesta al system prompt
       ↓
[LLM (NVIDIA NIM)] ← prompt multi-fuente + anti-alucinación
       ↓
[Disclaimer Injection]
       ↓
[Response + sources + disclaimer]
```

## 9. Ingesta de PDF

- El endpoint `POST /api/v1/knowledge/ingest-pdf` procesa el PDF íntegramente en memoria.
- El conteo de páginas se realiza con **pikepdf** (MPL 2.0, reemplazo de pypdf LGPL).
- El nombre de archivo es sanitizado (rechaza `..`, `/`, `\\`).
- No se escribe a disco en ningún punto del flujo.

## 10. Entorno E2E y tests

- El entorno E2E se define en `infrastructure/docker-compose.e2e.yml` (postgres, redis, minio, fake NIM, ms1_vision, ms2_chat, ms3_reports). Usa `target: production` (no `--reload`) para ms2_chat.
- `infrastructure/fake-nim/server.py` simula los endpoints de NVIDIA NIM (chat completions y embeddings dim 1024) para pruebas sin dependencia externa.
- `scripts/wait-for-services.sh` hace opcional ms1_vision (error preexistente: falta `opentelemetry`).
- El orquestador `scripts/run_system_tests.sh` levanta, espera health checks, ejecuta `tests/system/test_*.sh` y limpia.
- Los tests E2E cubren: chat con sensores reales + disclaimer, validación JWT (token inválido→401, válido→200), y bloqueo NOM-059 (consulta ilegal→403).

**Resultados (2026-06-16)**: 115 passed, 10 skipped, 0 failed. Cobertura 88% (objetivo ≥80%). E2E: 3/3 tests pasan. 0% MagicMock, 2 AsyncMock en frontera de red.

Auditoría completada 2026-06-16 — **87% → ~95%** tras corrección de rutas de prompts, adición de dependencias directas (`pyyaml`, `tenacity`) y protección con `asyncio.Lock` en `pgvector_store.initialize()`.

## 11. Cumplimiento de licencias

### 11.1 Política

El proyecto Mole.AI es software privativo (closed source). **Queda prohibido** integrar dependencias con licencias GPL, LGPL, AGPL o cualquier licencia «viral» que obligue a liberar el código fuente derivado.

### 11.2 Dependencias directas verificadas

| Paquete | Versión | Licencia | Compatible | Notas |
|---------|---------|----------|------------|-------|
| fastapi | ≥0.104 | MIT | ✅ | |
| uvicorn | ≥0.24 | BSD | ✅ | |
| gunicorn | ≥21.2 | MIT | ✅ | |
| pydantic | ≥2.1 | MIT | ✅ | |
| pydantic-settings | ≥2.2 | MIT | ✅ | |
| structlog | ≥24.1 | Apache 2.0 / MIT | ✅ | |
| PyJWT | ≥2.8 | MIT | ✅ | |
| cryptography | ≥42.0 | BSD / Apache 2.0 | ✅ | |
| openai | ≥1.0 | Apache 2.0 | ✅ | |
| slowapi | ≥0.1.9 | MIT | ✅ | |
| langchain-text-splitters | ≥0.2 | MIT | ✅ | |
| pikepdf | ≥8.0 | MPL 2.0 | ✅ | Reemplazo de pypdf (LGPL) |
| pdfminer.six | ≥20231228 | BSD | ✅ | Reemplazo de pypdf (LGPL) |
| pgvector | ≥0.2.5 | Apache 2.0 | ✅ | |
| redis | ≥4.6 | MIT | ✅ | |
| aiohttp | ≥3.8 | Apache 2.0 | ✅ | |
| python-multipart | ≥0.0.9 | Apache 2.0 | ✅ | |
| reportlab | - | BSD | ✅ | |
| asyncpg | ≥0.29 | Apache 2.0 | ✅ | |
| boto3 | ≥1.34 | Apache 2.0 | ✅ | |
| httpx | ≥0.27 | BSD | ✅ | Solo testing |
| prometheus-fastapi-instrumentator | ≥6.1 | MIT | ✅ | |

### 11.3 Dependencias eliminadas por licencia incompatible

| Paquete | Versión anterior | Licencia | Riesgo | Reemplazo |
|---------|-----------------|----------|--------|-----------|
| pypdf | 4.2.0 | LGPL | Obliga a liberar cambios | pikepdf (MPL 2.0) + pdfminer.six (BSD) |
| aiofiles | 23.2.1 | Apache 2.0 | ✅ Permisiva, eliminada por innecesaria | Ninguno (contenido en memoria) |

### 11.4 Árbol de dependencias transitivas

| Paquete | Licencia | Dependencia de | Compatible |
|---------|----------|----------------|------------|
| anyio | MIT | fastapi, httpx | ✅ |
| sniffio | MIT | anyio | ✅ |
| starlette | BSD | fastapi | ✅ |
| typing_extensions | MIT | pydantic | ✅ |
| annotated-types | MIT | pydantic | ✅ |
| certifi | MPL 2.0 | httpx, cryptography | ✅ |
| h11 | MIT | uvicorn | ✅ |
| idna | BSD | anyio, httpx | ✅ |
| yarl | Apache 2.0 | aiohttp | ✅ |
| multidict | Apache 2.0 | aiohttp | ✅ |
| frozenlist | MIT | aiohttp | ✅ |
| aiosignal | Apache 2.0 | aiohttp | ✅ |
| attrs | MIT | aiohttp | ✅ |
| charset-normalizer | MIT | aiohttp | ✅ |
| async-timeout | Apache 2.0 | aiohttp | ✅ |
| pycparser | BSD | cryptography | ✅ |
| cffi | MIT | cryptography | ✅ |
| six | MIT | cryptography | ✅ |
| jmespath | MIT | boto3 | ✅ |
| s3transfer | Apache 2.0 | boto3 | ✅ |
| botocore | Apache 2.0 | boto3 | ✅ |
| python-dateutil | Apache 2.0 / BSD | botocore | ✅ |
| urllib3 | MIT | botocore | ✅ |
| pikepdf | MPL 2.0 | requirements.txt | ✅ |
| lxml | BSD | pikepdf | ✅ |
| Pillow | Historical (MIT-like) | pikepdf | ✅ |
| libqpdf (nativa) | Apache 2.0 | pikepdf (enlace C) | ✅ |

### 11.5 Notas de implementación

- La ingesta de PDF usa **pikepdf** (MPL 2.0) para conteo de páginas y **pdfminer.six** (BSD) para extracción de texto. No escribe a disco.
- El nombre de archivo es sanitizado para evitar path traversal (rechaza `..`, `/`, `\\`).
- El CI ejecuta `pip-licenses --fail-on="GPL;LGPL;AGPL;GPLv2;GPLv3;LGPLv2;LGPLv3"` como gate (job `license-check`).
- **Historial de cambios de licencias**:
  - `pypdf` (LGPL) reemplazado por `pikepdf` (MPL 2.0) para conteo de páginas
  - `pypdf` (LGPL) reemplazado por `pdfminer.six` (BSD) para extracción de texto
  - `aiofiles` eliminado por innecesario
  - `HuggingFace` eliminado: único embedding activo es NVIDIA nv-embedqa-e5-v5
  - FAISS stub eliminado: `MoleAIChatUseCase` requiere inyección explícita de `vector_store`
- **Historial de cambios de seguridad**:
  - Path traversal eliminado: escritura a `/tmp/` reemplazada por procesamiento en memoria con validación de filename
  - Test de seguridad: `test_ingest_pdf_path_traversal_rejected` verifica rechazo de `../`

### 11.6 Herramientas de verificación en CI

- `pip-licenses --format=json` — auditoría automática
- `pip-licenses --fail-on="GPL;LGPL;AGPL;GPLv2;GPLv3;LGPLv2;LGPLv3"` — gate que bloquea el build si aparece licencia no permitida
