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
| RF-11 | Recuperación FAISS | Búsqueda en vector store para contexto | Context relevante del RAG |
| RF-12 | Cacheo Redis (CAG) | Contexto de sensores desde Redis | Telemetry del usuario cacheada |
| RF-13 | Fallback Trefle.io | API botánica si FAISS falla | Busca en internet como Plan B |
| RF-14 | Contexto Multi-Fuente | Agregación de sensores + RAG + external | Prompt con 3 fuentes |

### 1.4 Gestión de Conocimiento

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RF-15 | Ingesta de PDFs | Endpoint para subir manuales/documentos | PDF indexado en FAISS |
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
| RNF-01 | Latencia Chat | Timeout de llamada LLM | ≤30s (HF_API_TIMEOUT) |
| RNF-02 | Latencia Inference | Timeout de inferencia TFLite | ≤2s |
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
| RNF-09 | Graceful Degradation | Fallback si servicios fallan | No 500 por redis/faiss/llm |
| RNF-10 | Health Check | Endpoint público | /health accesible sin auth |

### 2.4 Arquitectura

| ID | Nombre | Descripción | Criterio de Aceptación |
|----|--------|-------------|-------------------|
| RNF-11 | Hexagonal | Puertos y Adaptadores | Capas: api, core, domain, application, infrastructure |
| RNF-12 | DI en Use Cases | Inyección de dependencias | MoleAIChatUseCase recibe puertos |
| RNF-13 | Async/Await | I/O asíncrono | Todos los adapters son async |

---

## 3. Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| API | FastAPI |
| Servidor ASGI | Uvicorn |
| Auth | Supabase JWT (ES256) |
| Cache/Pub-Sub | Redis (aioredis) |
| Vector Store | FAISS |
| LLM | HuggingFace Inference API |
| Logging | structlog |
| Config | pydantic-settings |

---

## 4. Endpoints

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | /api/v1/mole-ai/chat | JWT | Chat RAG+CAG |
| POST | /api/v1/knowledge/ingest-pdf | JWT | Ingesta PDF |
| DELETE | /api/v1/knowledge/pdf/{doc_id} | JWT | Borra PDF |
| GET | /api/v1/health | Público | Health check |

---

## 5. Diagrama de Flujo (RAG+CAG)

```
[HTTP Request + JWT]
       ↓
[get_current_user] → HTTPBearer + SupabaseTokenValidator
       ↓ (user_id validado)
[PIISanitizer.sanitize] → Limpia emails/teléfonos
       ↓ (mensaje_seguro)
[Redis (CAG)] ← telemetria
[FAISS (RAG)] ← contexto local
[Trefle.io] ← fallback
       ↓
[LLM (HF)] ← prompt multi-fuente
       ↓
[Disclaimer Injection]
       ↓
[Response + sources + disclaimer]
```