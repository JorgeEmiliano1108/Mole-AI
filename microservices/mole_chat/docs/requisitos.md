# Requisitos del Microservicio mole_chat (MS-2 RAG+CAG)

## 1. Requisitos Funcionales

### 1.1 Autenticación y Seguridad

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-01 | Validación JWT ES256 | Validación asimétrica de tokens JWT con algoritmo ES256 | El endpoint /chat retorna 401 si token inválido |
| RF-02 | JWKS Caching | Cacheo de llaves públicas JWKS con TTL (default 300s) | Validación offline sin llamada a red en caché hit |
| RF-03 | Interceptor de Usuario | Extracción de user_id del token JWT vía HTTPBearer | get_current_user retorna user_id verificado |
| RF-04 | Validación Cruzada | Verificación de user_id en request vs token | Retorna 403 si mismatched |
| RF-05 | Protección Anti-DoS | Lock asíncrono en validación JWKS | No hay race conditions en cache refresh |

### 1.2 Sanitización PII (LFPDPPP)

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-06 | Sanitización de Email | Detección y enmascaramiento de correos en prompts | Correos reemplazados por [EMAIL_OCULTO] |
| RF-07 | Sanitización de Teléfono | Detección y enmascaramiento de teléfonos en prompts | Teléfonos reemplazados por [TEL_OCULTO] |
| RF-08 | Hash de Identificadores | Hash SHA-256 irreversibles para logs | user_id nunca en texto claro |
| RF-09 | Logs Estructurados | Logging con JSON y sin PII | structlog con campos seguros |

### 1.3 Chat Conversacional

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-10 | Chat RAG+CAG | Generación de respuestas con contexto multi-fuente | Respuesta incluye sources y disclaimer |
| RF-11 | Recuperación pgvector | Búsqueda en vector store para contexto | Context relevante del RAG |
| RF-12 | Cacheo Redis (CAG) | Contexto de sensores desde Redis | Telemetry del usuario cacheada |
| RF-13 | Fallback externo | API botánica (Trefle.io — placeholder) | Búsqueda externa como Plan B (no implementado) |
| RF-14 | Contexto Multi-Fuente | Agregación de sensores + RAG + external | Prompt con 3 fuentes |

### 1.4 Gestión de Conocimiento

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-15 | Ingesta de PDFs | Endpoint para subir manuales/documentos | PDF indexado en pgvector |
| RF-16 | Borrado de Documentos | Eliminación selectiva de documentos | doc_id eliminado del índice |
| RF-17 | Extracción de Fuentes | Citación de fuentes en respuestas | sources con url y confianza |
| RF-18 | Anti-Alucinación | Sistema prompt con REGLA DE ORO | LLM no inventa información |

### 1.5 Ética de IA

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-19 | Disclaimer Legal | Inyección de aviso legal en respuestas | Campo disclaimer presente |
| RF-20 | Fallback Seguro | Respuesta de error controlada | No revela información interna |

### 1.6 Health Checks

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-21 | Health Básico | Endpoint público /health | Retorna {status: "ok"} |

---

## 2. Requisitos No Funcionales

### 2.1 Rendimiento

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-01 | Latencia Chat | Timeout de llamada LLM | ≤30s (LLM_REQUEST_TIMEOUT) |
| RNF-02 | Latencia LLM Inference | Timeout de inferencia NVIDIA NIM | ≤30s (LLM_REQUEST_TIMEOUT) |
| RNF-03 | Async I/O | Operaciones asíncronas | redis.asyncio en adapters |
| RNF-04 | ThreadPool | Operaciones CPU-bound en ThreadPool | run_in_threadpool para inferencia |

### 2.2 Seguridad

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-05 | Zero-Trust | Validación JWT local sin dependencia de red | Validación offline posible |
| RNF-06 | PII Protection | Hash SHA-256 en logs | user_hash en lugar de user_id |
| RNF-07 | Prompt Sanitization | Sanitización PII antes de LLM | Mensaje sanitizado en prompt |
| RNF-08 | CORS Configurable | Orígenes permitidos via env | ORIGEN_PERMITIDO configurable |

### 2.3 Disponibilidad

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-09 | Graceful Degradation | Fallback si servicios fallan | No 500 por redis/pgvector/llm |
| RNF-10 | Health Check | Endpoint público | /health accesible sin auth |

### 2.4 Arquitectura

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-11 | Hexagonal | Puertos y Adaptadores | Capas: api, core, domain, application, infrastructure |
| RNF-12 | DI en Use Cases | Inyección de dependencias | MoleAIChatUseCase recibe puertos |
| RNF-13 | Async/Await | I/O asíncrono | Todos los adapters son async |

---

## 3. Bugs corregidos

| Fecha | Bug | Solución | Archivo |
|------|-----|----------|---------|
| 2026-06-15 | `_get_pgvector_store` era función **sync** pero se usaba con `await` → `TypeError` | Corregido a función async | `routers.py:146,184` |
| 2026-06-16 | `prompt_loader.py` y `nvidia_client.py` calculaban rutas relativas incorrectas a `prompts/` (2 niveles en vez de 4) → YAML nunca se cargaban, caían a hardcoded | Rutas corregidas a 4 niveles `(.., .., ..)` | `prompt_loader.py:4`, `nvidia_client.py:38` |
| 2026-06-16 | `pgvector_store.initialize()` sin `asyncio.Lock` → race condition en creación de pool | Añadido double-check locking | `pgvector_store.py:90-121` |

---

## 4. Decisiones Arquitectónicas (ADRs)

| ID | Título | Estado |
|----|--------|--------|
| ADR-001 | JWT ES256 con JWKS Cache | Implementado |
| ADR-002 | Docker Multi-Stage Hardening | Implementado |
| ADR-003 | Circuit Breaker Centralizado | Implementado |
| ADR-004 | mTLS y API Key por Dispositivo | Implementado |
| ADR-005 | SBOM y Gestión de Licencias | Parcial (gate de licencias OK, SBOM/Trivy pendiente) |

### ADR-001: JWT ES256 con JWKS Cache

**Contexto**: mole_chat necesita validar tokens JWT de forma segura y offline. La implementación original usaba HS256 con clave secreta estática, lo cual no cumple con Zero-Trust (se necesita verificación asimétrica). Supabase (proveedor de autenticación) expone un endpoint JWKS con llaves ES256 rotables.

**Decisión**: Se implementa:
- `JWKSClient`: fetch y cache de llaves públicas desde `JWKS_URL` con TTL configurable y lock asíncrono.
- `JWKSValidator`: verifica tokens usando algoritmo ES256 y la llave correspondiente al `kid` del header.
- `HS256Validator`: se mantiene como fallback si `JWKS_URL` no está configurado.
- Singleton `get_token_validator()` selecciona automáticamente el validador correcto.
- Ajustes `JWT_AUDIENCE`, `JWT_LEEWAY` y `JWKS_CACHE_TTL_SECONDS` en configuración.

**Consecuencias**:
- Validación offline de tokens ES256 sin depender de red en cada request (cache warm).
- Rotación de llaves JWKS manejada automáticamente (TTL expiry).
- Compatibilidad hacia atrás: si no hay JWKS_URL, se usa HS256.
- Complejidad adicional de mantenimiento del cache y manejo de errores de fetch.

### ADR-002: Docker Multi-Stage Hardening

**Contexto**: El Dockerfile original era monolítico, instalaba compiladores y dependencias de build en la imagen final, y ejecutaba como root. Esto incrementa la superficie de ataque.

**Decisión**: Se rediseña el Dockerfile con 4 etapas:
1. **builder**: instala compiladores, crea venv con `requirements.lock`.
2. **base**: imagen slim, copia venv, crea usuario `appuser` no-root, añade HEALTHCHECK.
3. **development**: hereda de base con hot-reload.
4. **production**: hereda de base, copia solo `app/` y `prompts/`, remueve binarios SUID.

Además:
- Se usa `requirements.lock` en lugar de `requirements.txt` para versiones fijas.
- Se añade `.dockerignore` para excluir archivos innecesarios.

**Consecuencias**:
- Imagen final < 100MB, sin compiladores ni herramientas de build.
- Ejecución como usuario no-root (`appuser`).
- HEALTHCHECK automático en producción.
- Mayor mantenimiento del `requirements.lock`.

### ADR-003: Circuit Breaker Centralizado

**Contexto**: mole_chat depende de servicios externos (LLM, pgvector, Redis) que pueden fallar o degradarse. La implementación previa tenía un circuit breaker embebido en `nvidia_client.py` (SimpleAsyncCircuitBreaker), pero no era reutilizable y no protegía otros adapters.

**Decisión**: Se extrae un `AsyncCircuitBreaker` genérico en `app/core/circuit_breaker.py`:
- Configurable por nombre, `fail_max` y `reset_timeout`.
- Thread-safe con `asyncio.Lock`.
- Estados: CLOSED → OPEN → HALF_OPEN → CLOSED.
- Método `call(coro_factory)` que envuelve cualquier async callable.
- Se reemplaza el breaker embebido en `nvidia_client.py` por el genérico.

**Consecuencias**:
- Breaker reutilizable en LLM, pgvector, Redis y futuros adapters.
- Lógica de resiliencia centralizada y testeable.
- Métricas de estado (`state`, `failure_count`) disponibles para monitoreo.
- Pequeña sobrecarga de lock en cada llamada.

### ADR-004: mTLS y API Key por Dispositivo

**Contexto**: La comunicación entre microservicios (chat ↔ Redis, chat ↔ LLM) no estaba autenticada ni cifrada a nivel de transporte. Además, no existía un mecanismo para identificar dispositivos IoT que envían telemetría (requisito ETSI EN 303 645).

**Decisión**: Se implementan dos capas de autenticación:

1. **API Key por dispositivo** (ETSI EN 303 645):
   - Header `X-API-KEY` obligatorio en endpoints.
   - Dependency `verify_api_key()` en `dependencies.py`.
   - Configurable via env `API_KEY`.

2. **mTLS para Redis**:
   - `RedisSensorCacheAdapter` acepta certificados TLS opcionales (`TLS_CERT_PATH`, `TLS_KEY_PATH`, `TLS_CA_PATH`).
   - Si están presentes, se establece conexión SSL/TLS autenticada.
   - Para el LLM (servicio externo), mTLS se delega a proxy sidecar (Envoy/Linkerd).

**Consecuencias**:
- Dispositivos no autorizados no pueden consumir la API.
- Conexión Redis autenticada y cifrada (cuando se configuran certificados).
- API Key como capa adicional además de JWT (defense in depth).
- Complejidad operativa al gestionar certificados.

### ADR-005: SBOM y Gestión de Licencias

**Contexto**: El microservicio usa múltiples dependencias open-source. No existía un inventario de software (SBOM) ni validación de licencias, exponiendo a riesgo de propiedad intelectual y violación de términos GPL/Apache.

**Decisión**: Se integra en el pipeline CI:
1. **Generación de SBOM**: `cyclonedx-bom` a partir de `requirements.lock` → `sbom.json`. (PENDIENTE)
2. **Verificación de licencias**: `pip-licenses` con lista blanca de licencias permitidas (MIT, Apache-2.0, BSD-2/3, PSF, ISC, Python-2.0, Unlicense, MPL-2.0). (IMPLEMENTADO)
3. **Escaneo de vulnerabilidades**: Trivy sobre la imagen Docker final, fallando en CRITICAL/HIGH. (PENDIENTE)
4. **Artefacto SBOM**: subido como artifact de CI para trazabilidad. (PENDIENTE)

**Consecuencias**:
- Cumplimiento de propiedad intelectual: cualquier dependencia con licencia no permitida bloqueará el CI. (IMPLEMENTADO via pip-licenses --fail-on)
- Trazabilidad: SBOM versionado por commit. (PENDIENTE)
- Detección temprana de vulnerabilidades en imágenes. (PENDIENTE)
- Dependencia de herramientas externas (cyclonedx-bom, pip-licenses, Trivy) en CI.

**Estado**: Parcialmente implementado. El gate de licencias con `pip-licenses --fail-on` está operativo en `.github/workflows/system-tests.yml` (job `license-check`). La generación de SBOM y el escaneo Trivy quedan como tareas futuras.
