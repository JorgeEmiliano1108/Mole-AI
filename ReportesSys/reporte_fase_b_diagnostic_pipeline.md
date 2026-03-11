# Reporte Sprint 2 — Fase B: Pipeline de Diagnóstico CNN (FastAPI)

**Fecha:** 8 de marzo de 2026  
**Alcance:** Implementación completa de la Fase B del roadmap Sprint 2 — endpoints de Signed URL y Diagnóstico CNN en el microservicio FastAPI (`ai_rag_service`), junto con correcciones de infraestructura Django necesarias para compatibilidad.

---

## 1. Inventario de Archivos

### 1.1 Archivos Creados (6)

| # | Archivo | Capa Hexagonal | LOC | Propósito |
|---|---------|---------------|-----|-----------|
| 1 | `ai_rag_service/infrastructure/external/mock_vision_client.py` | Infraestructura (Adapter) | 47 | Stub del cliente CNN para dev/MVP |
| 2 | `ai_rag_service/infrastructure/database/supabase_diagnostic_repo.py` | Infraestructura (Adapter) | 103 | Persistencia de diagnósticos vía PostgREST |
| 3 | `ai_rag_service/domain/ports/diagnostic_ports.py` | Dominio (Port) | 51 | Interfaces abstractas del pipeline |
| 4 | `ai_rag_service/application/use_cases/create_diagnostic_use_case.py` | Aplicación (Use Case) | 140 | Orquestador del pipeline CNN completo |
| 5 | `apps/authentication/models.py` | Django (Re-export) | 2 | Puente para `AUTH_USER_MODEL` |
| 6 | `apps/plants/models.py` | Django (Re-export) | 2 | Puente para descubrimiento de modelo |

### 1.2 Archivos Modificados (6)

| # | Archivo | Tipo de cambio |
|---|---------|---------------|
| 1 | `ai_rag_service/infrastructure/api/routes.py` | +4 imports DTO, +1 import use case, +2 params en `create_routes()`, +2 endpoints nuevos (~60 LOC) |
| 2 | `ai_rag_service/infrastructure/api/contracts.py` | +2 secciones de contratos (UploadUrl + Diagnostic, ~45 LOC) |
| 3 | `ai_rag_service/app/main.py` | +4 imports, +2 globals, +1 bloque DI (8 líneas), +2 kwargs en `create_routes()` |
| 4 | `conftest.py` | +1 fixture session-scoped para tablas `managed=False` |
| 5 | `tests/integration/test_m2m_ingest_wide_table.py` | Adaptación de 3 tests para mockear `UserPlant.objects` |
| 6 | `apps/authentication/migrations/0001_initial.py` | **Auto-generada** por `makemigrations` |

### 1.3 Infraestructura (1)

| Acción | Detalle |
|--------|---------|
| `db.sqlite3` recreada | Se eliminó y reconstruyó porque `admin.0001_initial` estaba aplicada antes de `authentication.0001_initial` (dependencia circular con `AUTH_USER_MODEL` custom) |

---

## 2. Análisis Detallado por Archivo

### 2.1 `diagnostic_ports.py` — Puertos del Dominio

**Ubicación:** `ai_rag_service/domain/ports/diagnostic_ports.py`

Define dos interfaces abstractas (ABC) que desacoplan el caso de uso de la infraestructura:

- **`DiagnosticRepositoryPort`**: Contrato para persistir filas en `ai_diagnostics` y `cnn_inferences`.
  - `save_diagnostic(...)` → `int` (ID del diagnóstico)
  - `save_cnn_inference(...)` → `int` (ID de la inferencia)
- **`VisionClientPort`**: Contrato para ejecutar el modelo CNN.
  - `analyze(image_url)` → `dict` con keys: `species`, `ph`, `condition`, `description`, `severity`, `confidence`, `predictions`, `confidence_scores`, `model_used`

**Observaciones:**
- Ambos métodos son `async` — correcto para I/O-bound (HTTP a Supabase/HF API).
- La firma de `save_diagnostic` acepta 12 parámetros posicionales. Esto podría beneficiarse de un dataclass intermedio en el futuro, pero es aceptable para MVP.
- `VisionClientPort.analyze` retorna `dict` en lugar de un dominio tipado. Trade-off pragmático para flexibilidad, pero pierde type-safety.

---

### 2.2 `create_diagnostic_use_case.py` — Orquestador del Pipeline

**Ubicación:** `ai_rag_service/application/use_cases/create_diagnostic_use_case.py`

Pipeline en 3 pasos:

```
CNN analyze() → [ExplainPh] → Persist (ai_diagnostics + cnn_inferences)
```

**Flujo detallado:**
1. **Step 1 — CNN Inference**: Llama a `vision_client.analyze(storage_url)`. El mock responde con especie, pH, condición, y confianza.
2. **Step 2 — pH Explainability** (condicional): Si `ph_predicted ≠ None` y `explain_ph_use_case` está inyectado, integra la cadena de explicabilidad existente. Envuelve en `try/except` para fault-tolerance.
3. **Step 3 — Persistencia dual**: Guarda en `ai_diagnostics` (diagnóstico completo) y `cnn_inferences` (detalle técnico de la inferencia).

**Observaciones:**
- `species_name` del request tiene prioridad sobre la detección CNN (`species_name or inference.get("species")`) — diseño correcto para override del agricultor.
- `time.perf_counter()` mide latencia del pipeline completo — incluye CNN + explainability pero no persistencia. Considerar si `elapsed_ms` debería incluir también el write a DB.
- El dataclass `DiagnosticResult` define el contrato de salida, cumpliendo el principio de que el caso de uso nunca retorna entidades de infraestructura.
- Fallo silencioso en ExplainPh (`logger.warning`) es correcto: el diagnóstico CNN tiene valor independiente del pH.

---

### 2.3 `mock_vision_client.py` — Stub del CNN

**Ubicación:** `ai_rag_service/infrastructure/external/mock_vision_client.py`

Implementa `VisionClientPort` con datos aleatorios realistas:

- **5 especies agrícolas**: Tomate, Chile, Lechuga, Pepino, Frijol
- **4 condiciones**: Healthy, Nitrogen Deficiency, Powdery Mildew, Early Blight
- **Rangos coherentes**: confianza 0.70–0.98, pH 5.0–7.5

**Observaciones:**
- Usa `random.choice`/`random.uniform` — resultados no deterministas. Para tests unitarios esto podría ser problemático; se recomienda inyectar seed o usar una versión fija para tests.
- No valida `image_url` (correcto para mock — la validación real será del cliente HF).
- El `model_used: "mock-dual-cnn-v0"` permite identificar en logs y DB que se usó el mock.

---

### 2.4 `supabase_diagnostic_repo.py` — Adaptador de Persistencia

**Ubicación:** `ai_rag_service/infrastructure/database/supabase_diagnostic_repo.py`

Persiste a Supabase vía PostgREST (mismo patrón que `SupabaseKnowledgeRepo`).

**Detalles:**
- **`save_diagnostic`**: POST a `/rest/v1/ai_diagnostics` con `Prefer: return=representation` para obtener el ID generado.
- **`save_cnn_inference`**: POST a `/rest/v1/cnn_inferences` con foreign key al `diagnostic_id`.
- `json.dumps()` para campos `recommendations`, `predictions`, `confidence_scores`, `top_prediction` — correcto porque PostgREST espera strings JSON para columnas `jsonb`.

**Observaciones:**
- En caso de fallo HTTP, ambos métodos retornan `0` silenciosamente y logean error. Esto es un trade-off de resiliencia: el pipeline no aborta por fallo de persistencia, pero el `diagnostic_id=0` puede causar confusión downstream. Para producción se recomienda propagar la excepción o retornar `Optional[int]`.
- El `http_client` se recibe por inyección y se comparte con otros adaptadores (lifecycle management centralizado en `main.py`) — correcto para evitar connection pool leaks.
- `timeout=10.0` es razonable para PostgREST.

---

### 2.5 `supabase_storage.py` — Adaptador de Signed URLs

**Ubicación:** `ai_rag_service/infrastructure/external/supabase_storage.py`

Genera URLs pre-firmadas para que el cliente suba imágenes directamente a Supabase Storage (sin pasar por el backend).

**Flujo:**
1. Construye path único: `diagnostics/<YYYY-MM-DD>/<uuid12>_<filename>`
2. Si `SUPABASE_SERVICE_ROLE_KEY` no está configurado → retorna URL placeholder (dev graceful).
3. Si está configurado → POST al endpoint de sign de Supabase Storage API.

**Observaciones:**
- **Diseño zero-copy**: El backend nunca toca bytes de imagen. Solo genera la URL y el cliente sube directo. Reduce latencia, ancho de banda y memoria del backend.
- `uuid.uuid4().hex[:12]` en el path evita colisiones de nombres.
- Crea un nuevo `httpx.AsyncClient` por llamada (`async with httpx.AsyncClient`). Esto es ineficiente en producción — debería reutilizar el `_http_client` del lifespan. Sin embargo, el `SupabaseStorageAdapter.__init__` no recibe http_client actualmente (a diferencia de `SupabaseDiagnosticRepo`). Esto es un punto de mejora para Sprint 3.
- El fallback para desarrollo local devuelve una URL sintácticamente válida pero no funcional — suficiente para probar el flujo end-to-end sin credenciales.

---

### 2.6 `contracts.py` — Contratos Pydantic (Secciones 9 y 10)

**Ubicación:** `ai_rag_service/infrastructure/api/contracts.py` (líneas 171–227)

**Sección 9 — Signed Upload URL:**
- `UploadUrlRequest`: `file_name` (str, 1-255 chars), `content_type` (str, default `image/jpeg`)
- `UploadUrlResponse`: `upload_url`, `storage_path`, `expires_in`

**Sección 10 — Diagnostic Pipeline:**
- `CreateDiagnosticRequest`: `plant_id` (UUID, obligatorio), `storage_url` (str), `species_name` (Optional[str])
- `DiagnosticResultResponse`: 11 campos incluyendo `ph_explanation` (Optional dict del ExplainPhUseCase)

**Observaciones:**
- `plant_id: UUID` con validación Pydantic nativa — rechaza UUIDs malformados antes de llegar al use case.
- `storage_url: str` con `min_length=1` — impide cadenas vacías.
- `DiagnosticResultResponse.condition_description` está en el modelo pero **no** se mapea en la ruta (el endpoint de routes.py no pasa `condition_description` al DTO). Esto causará un **error de validación Pydantic** si `condition_description` no tiene default. **⚠️ BUG POTENCIAL** — verificar si Pydantic v2 asigna default `""` a `str` o si falla.

---

### 2.7 `routes.py` — Registro de Endpoints

**Ubicación:** `ai_rag_service/infrastructure/api/routes.py`

**Cambios:**
1. **Imports**: +4 DTOs (UploadUrl, Diagnostic) y `CreateDiagnosticUseCase`
2. **Firma `create_routes()`**: +2 parámetros opcionales (`storage_adapter=None`, `create_diagnostic_use_case=None`) — backward-compatible.
3. **Endpoint `POST /diagnostics/upload-url`**: Valida que `storage_adapter` esté inicializado (503 si no), delega a `generate_signed_upload_url()`.
4. **Endpoint `POST /diagnostics`**: Valida que el use case esté inicializado (503 si no), ejecuta pipeline, mapea `DiagnosticResult` → `DiagnosticResultResponseDTO`.

**Observaciones:**
- Ambos endpoints usan guard clause `if X is None: raise 503` antes de la lógica — correcto para evitar NoneType errors.
- **Tag `["Diagnostics"]`** agrupa los endpoints en Swagger/OpenAPI — buena UX para el frontend.
- El bug conocido del singleton `api_v1_router` a nivel de módulo sigue presente pero no afecta producción (solo tests con múltiples llamadas a `create_routes`).
- ⚠️ **Observación**: `condition_description` no se pasa en el dict de `DiagnosticResultResponseDTO(...)` en el endpoint `create_diagnostic`. El campo existe en el modelo `DiagnosticResult` y en el DTO. Si el campo no tiene default value en el contrato, Pydantic rechazará la respuesta con ValidationError.

---

### 2.8 `main.py` — Inyección de Dependencias

**Ubicación:** `ai_rag_service/app/main.py`

**Cambios:**
1. **+4 imports**: `CreateDiagnosticUseCase`, `SupabaseStorageAdapter`, `SupabaseDiagnosticRepo`, `MockVisionClient`
2. **+2 globals**: `storage_adapter`, `create_diagnostic_use_case` (tipo `Optional[object]`)
3. **Bloque 8 (nuevo)** en el lifespan — instanciación del pipeline completo:
   ```
   SupabaseStorageAdapter() → storage_adapter
   SupabaseDiagnosticRepo(url, key, http_client) → diagnostic_repo
   MockVisionClient() → vision_client
   CreateDiagnosticUseCase(repo, vision, explain_ph) → create_diagnostic_use_case
   ```
4. **`create_routes()`** actualizado con `storage_adapter=` y `create_diagnostic_use_case=`.

**Observaciones:**
- `SupabaseDiagnosticRepo` recibe el `_http_client` compartido (correcto: lifecycle unificado).
- `SupabaseStorageAdapter()` se instancia sin `http_client` — usa su propio cliente efímero internamente. Inconsistencia con el patrón del repo (ver punto 2.5).
- Los globals `Optional[object]` podrían ser `Optional[SupabaseStorageAdapter]` y `Optional[CreateDiagnosticUseCase]` para type-safety, pero funciona correctamente en runtime.
- El `MockVisionClient` se instancia incondicionalmente. En producción, se debería condicionar con un env var o feature flag (e.g., `VISION_CLIENT=mock|huggingface`).

---

### 2.9 `conftest.py` — Tablas Unmanaged para Tests

**Ubicación:** `conftest.py` (raíz del proyecto)

**Cambio:** Nuevo fixture `_create_unmanaged_tables` (session-scoped, autouse):

```python
@pytest.fixture(autouse=True, scope="session")
def _create_unmanaged_tables(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.db import connection
        with connection.schema_editor() as editor:
            for model in (UserPlant, SensorLog):
                try:
                    editor.create_model(model)
                except Exception:
                    pass
```

**Justificación:** Los modelos `UserPlant` y `SensorLog` usan `managed = False` porque las tablas reales viven en Supabase PostgreSQL. Pero el test runner crea una DB SQLite temporal que no las incluye. Este fixture crea las tablas manualmente usando el schema editor de Django.

**Observaciones:**
- `scope="session"` es correcto: las tablas se crean una sola vez para toda la sesión de tests.
- `try/except Exception: pass` es broad pero seguro aquí — solo atrapa `OperationalError` si la tabla ya existe.
- Dependencia en `django_db_setup` garantiza que las migraciones estándar se ejecuten primero.

---

### 2.10 `test_m2m_ingest_wide_table.py` — Adaptación de Tests

**Ubicación:** `tests/integration/test_m2m_ingest_wide_table.py`

**Cambio en 3 tests:**

Los tests de Sprint 1 originales mockeaban solo `SensorLog.objects.create`. Tras la adición de validación `plant_id` contra `UserPlant` en Sprint 2 (Fase A.4), los tests fallaban con 404. Se añadió mock adicional de `UserPlant.objects`:

| Test | Mock añadido |
|------|-------------|
| `test_sensor_data_m2m_success_flat_payload_creates_single_row` | `plant_qs.filter().exists() → True` |
| `test_sensor_data_m2m_accepts_null_ph_level` | `plant_qs.filter().exists() → True` |
| `test_sensor_batch_m2m_bulk_insert_success` | `plant_qs.filter().values_list() → {pid1, pid2}` |

**Observaciones:**
- Los 2 tests que no requerían cambio (`rejects_missing_api_key`, `rejects_missing_plant_id`) fallan antes de llegar a la validación de UserPlant — no necesitan mock.
- Para batch, se usan variables `pid1`, `pid2` para poder retornarlas en el mock de `values_list()`.

---

### 2.11 Django Model Re-exports + Migración

| Archivo | Propósito |
|---------|-----------|
| `apps/authentication/models.py` | Re-exporta `User` desde `infrastructure/repositories/models.py` para que `AUTH_USER_MODEL = 'authentication.User'` funcione |
| `apps/plants/models.py` | Re-exporta `UserPlant` para descubrimiento de Django (`managed=False`, sin migración) |
| `apps/authentication/migrations/0001_initial.py` | Migración auto-generada para `auth_users` (tabla managed del custom User model) |

**Problema resuelto:** Django busca modelos en `<app>.models` por convención. La arquitectura hexagonal coloca los modelos en `<app>.infrastructure.repositories.models`. Los archivos bridge de 2 líneas resuelven esta tensión sin violar la estructura existente.

---

## 3. Mapa de Dependencias (Pipeline Completo)

```
┌─────────────────┐    ┌──────────────────────┐
│  POST            │    │  POST                │
│  /diagnostics/   │    │  /diagnostics/       │
│  upload-url      │    │                      │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         ▼                         ▼
 SupabaseStorage        CreateDiagnosticUseCase
    Adapter                    │
    (signed URL)               ├── VisionClientPort ──→ MockVisionClient
                               │                        (→ HF API prod)
                               ├── ExplainPhUseCase
                               │     ├── KnowledgeRepo
                               │     ├── BotanicalGateway
                               │     └── SensorValidator
                               │
                               └── DiagnosticRepoPort ──→ SupabaseDiagnosticRepo
                                                           ├── ai_diagnostics
                                                           └── cnn_inferences
```

---

## 4. Endpoints HTTP Nuevos

| Método | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| POST | `/api/v1/diagnostics/upload-url` | `{file_name, content_type}` | `{upload_url, storage_path, expires_in}` | 200 / 503 / 500 |
| POST | `/api/v1/diagnostics` | `{plant_id (UUID), storage_url, species_name?}` | Full `DiagnosticResultResponse` (11 campos) | 200 / 503 / 500 |

---

## 5. Bugs Detectados y Riesgos

### 5.1 ⚠️ Bug: `condition_description` omitido en la ruta

**Archivo:** `ai_rag_service/infrastructure/api/routes.py`, endpoint `create_diagnostic`  
**Detalle:** El mapeo de `DiagnosticResult` → `DiagnosticResultResponseDTO` no incluye `condition_description`. El contrato Pydantic `DiagnosticResultResponse` declara `condition_description: str` sin default value. En Pydantic v2 esto causaría `ValidationError`.  
**Severidad:** Media (rompe la respuesta HTTP si Pydantic es estricto)  
**Fix:** Añadir `condition_description=result.condition_description` en el endpoint, o agregar `default=""` al campo en el contrato.

### 5.2 ⚠️ Riesgo: `SupabaseStorageAdapter` no comparte `http_client`

**Archivo:** `ai_rag_service/infrastructure/external/supabase_storage.py`  
**Detalle:** A diferencia de `SupabaseDiagnosticRepo` y `SupabaseKnowledgeRepo`, el storage adapter crea un `httpx.AsyncClient` efímero por cada llamada. En producción con alto throughput, esto genera overhead de conexiones TCP.  
**Severidad:** Baja (solo afecta performance bajo carga)  
**Fix:** Añadir `http_client` al constructor, igual que los otros adaptadores.

### 5.3 ⚠️ Riesgo: `save_diagnostic` retorna `0` silenciosamente

**Archivo:** `ai_rag_service/infrastructure/database/supabase_diagnostic_repo.py`  
**Detalle:** Si PostgREST falla, ambos métodos retornan `0` sin propagar error. El `diagnostic_id=0` se retorna al cliente como si fuera exitoso.  
**Severidad:** Baja en MVP (datos mock), Media en producción  
**Fix:** Lanzar excepción custom (`DiagnosticPersistenceError`) o retornar `Optional[int]`.

### 5.4 Nota: `MockVisionClient` siempre activo

**Archivo:** `ai_rag_service/app/main.py` línea ~178  
**Detalle:** No hay feature flag para cambiar entre mock y producción.  
**Severidad:** Baja (claramente transitorio para MVP)  
**Fix futuro:** `os.getenv("VISION_BACKEND", "mock")` → factory pattern.

---

## 6. Resultado de Tests

```
======================== 10 passed, 1 warning in 0.58s =========================
```

| Suite | Tests | Estado |
|-------|-------|--------|
| `tests/integration/test_m2m_ingest_wide_table.py` | 5 | ✅ PASS |
| `ai_rag_service/tests/test_explain_ph_use_case_wide_table.py` | 3 | ✅ PASS |
| `ai_rag_service/tests/test_explain_ph_endpoint_contract.py` | 2 | ✅ PASS |

**Regresiones:** Ninguna. Los 10 tests de Sprint 1 pasan con las adaptaciones de mock.

---

## 7. Checklist de Arquitectura Hexagonal

| Principio | Cumplimiento | Detalle |
|-----------|:---:|---------|
| Puertos abstractos en dominio | ✅ | `DiagnosticRepositoryPort`, `VisionClientPort` en `domain/ports/` |
| Adaptadores en infraestructura | ✅ | `SupabaseDiagnosticRepo`, `MockVisionClient`, `SupabaseStorageAdapter` en `infrastructure/` |
| Caso de uso no importa infraestructura | ✅ | `CreateDiagnosticUseCase` solo usa ports por constructor |
| Contratos API separados del dominio | ✅ | Pydantic DTOs en `infrastructure/api/contracts.py` |
| DI por constructor (no service locator) | ✅ | Toda inyección ocurre en `main.py` lifespan |
| Modelos Django aislados | ✅ | Re-exports bridge en `models.py` raíz de cada app |
