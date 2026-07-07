# Operación, seguridad y calidad

## 1. Context & Scope
Establecer lineamientos operativos, de seguridad, observabilidad y calidad que garanticen disponibilidad, integridad y confiabilidad de MOLE‑AI en entornos de producción y desarrollo.

## 2. Constraints
- Despliegue mediante `docker‑compose.yml`.
- PostgreSQL 13+ con extensión `pgvector`.
- No se utiliza Kubernetes, ONNX ni panel de administración en la versión actual.

## 3. Solution Strategy
Aplicar principios de **mínimo privilegio**, **defensa en profundidad** y separación clara entre lógica de negocio y persistencia.

## 4. Building Blocks
- **NGINX** (gateway TLS).
- **Docker containers** para backend, micro‑servicios, Redis y PostgreSQL.
- **PostgreSQL** + `pgvector` para datos y embeddings.
- **Redis** (cache, broker y throttling).
- **Celery workers** (backend y reports).
- **AWS S3** para PDFs y artefactos.

## 5. Runtime View
Cliente → **NGINX** → **API** (Django/FastAPI) → *(auth / autorización)* → **Celery / Redis** → **PostgreSQL** → **S3**. Cada componente expone endpoints de health‑check utilizados por Docker‑Compose.

## 6. Deployment View
Todos los bloques se despliegan con `docker‑compose.yml`; los puertos y variables de entorno están definidos en dicho archivo.

## 7. Cross‑cutting Concepts
### 7.1 Seguridad
- **Autenticación**: JWT firmado (HS256) con expiración ≤ 30 min.
- **Autorización**: clases DRF (`IsAuthenticated`, `IsSuperuserOrReadOnly`, `HardwareOnlyPermission`).
- **Gestión de secretos**: Docker secrets o variables `.env`; producción usa AWS Secrets Manager.
- **Cifrado y transporte seguro**: TLS 1.2+ en todas las comunicaciones externas; NGINX termina TLS.
- **Anti‑replay & throttling**: límites por endpoint y detección de timestamps > 300 s.
- **Filtro NOM‑059**: bloqueo de contenido prohibido mediante expresiones regulares.

### 7.2 Operación
- **NGINX**: gateway público (puerto 8080) con CORS y redirección a `/api/v1/*`.
- **Docker & redes**: `mole_public` y `mole_internal`; contenedores críticos en red interna.
- **Celery workers**: backend y reports, usando Redis como broker.
- **Bases de datos**: PostgreSQL con `pgvector`; Redis para caché y Pub/Sub.
- **Almacenamiento**: AWS S3 como repositorio definitivo.

### 7.3 Observabilidad
- **Prometheus** recoge métricas expuestas por Django y FastAPI.
- **Logging** estructurado (JSON) enviado a `stdout` y rotado por Docker.
- **Health‑checks**: cada servicio expone `/health/` con código 200 si está operativo.

### 7.4 Calidad
- **Objetivos**: latencia ≤ 200 ms en endpoints críticos; cobertura de pruebas ≥ 80 % (actual: **88%** en ms2_chat); disponibilidad ≥ 99.5 % (medida por Prometheus).
- **Estrategia de pruebas**:
  - **Unitarias**: 113 tests, 0 fallos con `requirements.lock` (pytest + fakes, 0% MagicMock)
  - **E2E**: 3 scripts shell sobre Docker Compose autónomo (`docker-compose.e2e.yml`) — chat con sensores Redis reales, validación JWT, bloqueo NOM-059
  - **Integración** (`pytest --run-integration`): esqueleto para pgvector (requiere `--break-system-packages` no disponible; pendiente de Dockerizar)
  - **Carga** (Locust): no implementado — pendiente
- **Gate de licencias**: el CI ejecuta `pip-licenses --fail-on="GPL;LGPL;AGPL;GPLv2;GPLv3;LGPLv2;LGPLv3"` y bloquea el build si aparece cualquier licencia no permitida (ver `.github/workflows/system-tests.yml`).
- **Entorno de tests**: los test unitarios deben ejecutarse dentro del contenedor Docker o con las versiones pinneadas de `requirements.lock`. Versiones no pinneadas pueden causar falsos positivos por incompatibilidad de `prometheus-fastapi-instrumentator` con Starlette ≥ 0.28.

### 7.5 Disponibilidad & Resiliencia
- **Redundancia**: se busca alta disponibilidad mediante configuraciones de redundancia; la implementación actual depende de la infraestructura provisionada.
- **Persistencia**: volúmenes Docker o snapshots RDS garantizan recuperación.

## 8. Decisions
| Decisión | Contexto | Estado |
|----------|----------|--------|
| JWT expiración ≤ 30 min | Seguridad de tokens | Implementado |
| Celery + Redis para tareas asíncronas | Operación | Implementado |
| TLS en NGINX | Transporte seguro | Implementado |
| Replicación PostgreSQL | Alta disponibilidad | Futuro |

## 9. Risks
| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Dependencia de APIs externas de NVIDIA | Interrupción del chat y visión | Monitorizar health‑checks de NVIDIA y alertas proactivas |
| Latencia de S3 | Aumento de tiempos de respuesta | Cachear metadatos en Redis y usar multipart upload |
| Rotura de secrets | Compromiso de credenciales | Rotación automática, uso de AWS Secrets Manager, auditoría de accesos |
| Crecimiento ilimitado de `botanical_knowledge` | Degradación de consultas vectoriales | Política de retención (> 2 años) y compresión de embeddings |

## 10. Technical Debt
- **TFLiteAdapter** permanece como código legado no utilizado.
- **MinIO** – referencia histórica, reemplazado por S3.
- **ms1_vision**: error preexistente `ModuleNotFoundError: No module named 'opentelemetry'` — falta dependencia en su Dockerfile. No bloquea tests de ms2_chat.
- **Falso positivo local**: `prometheus-fastapi-instrumentator` incompatible con Starlette ≥ 0.28. Los tests unitarios deben ejecutarse con `requirements.lock` (Starlette 0.27.0) para evitar 17 falsos fallos.
- **JWT key length**: la clave HMAC en E2E tests tiene 29 bytes (< 32 recomendados por RFC 7518). No crítico para pruebas, pero debe corregirse en producción.
- Falta de pruebas de resiliencia frente a caída del broker MQTT.
- Pipeline CI/CD: workflows existentes para system-tests E2E y license-check. Pendiente: lint automatizado, type-checking y despliegue continuo.

## 11. Evolution
- Integración de modelo ONNX como fallback.
- Orquestación con Kubernetes.
- Frontend móvil (Flutter).
- Panel de administración UI para usuarios, dispositivos y variables NVIDIA.
- Implementación de circuit‑breaker (Resilience4j/Hystrix) como futura medida de resiliencia.

