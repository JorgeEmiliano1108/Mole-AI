# Requisitos de core_backend — Monolito Django

## 1. Requisitos Funcionales

### 1.1 Autenticación y Seguridad

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-01 | Login JWT | Autenticación mediante JWT HS256 validado contra Supabase | Alta | ✅ Cumple | authentication |
| RF-02 | Refresh Token | Renovación de tokens JWT expirados | Alta | ✅ Cumple | authentication |
| RF-03 | API Key por Dispositivo | Identificación y autorización de dispositivos IoT mediante API Key | Alta | ✅ Cumple | devices |
| RF-04 | CRUD Usuarios | Gestión de usuarios con roles (admin, agricultor, técnico) | Alta | ✅ Cumple | users |
| RF-05 | Rate Limiting | Límite de requests por usuario/IP para prevenir abuso | Media | ⚠️ Parcial | core |
| RF-06 | CORS Configurable | Orígenes permitidos configurables por entorno | Alta | ✅ Cumple | core |

### 1.2 IoT y Telemetría

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-07 | Ingesta M2M | Recepción de telemetría desde dispositivos IoT vía M2M | Alta | ✅ Cumple | m2m |
| RF-08 | Bulk Insert Sensores | Inserción masiva de lecturas de sensores | Alta | ✅ Cumple | sensores |
| RF-09 | Downsampling Histórico | Reducción de resolución de datos antiguos para retención | Media | ✅ Cumple | sensores |
| RF-10 | Geocercas | Definición de perímetros virtuales para parcelas | Media | ✅ Cumple | cultivos |
| RF-11 | Edge Processing | Procesamiento local en nodos edge antes de envío | Baja | ⚠️ Parcial | devices |

### 1.3 Inteligencia Artificial

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-12 | Diagnóstico por Visión | Análisis de imágenes de cultivos via mole_vision | Alta | ✅ Cumple | ai_models |
| RF-13 | Chat Contextual | Conversación con RAG sobre cultivos via mole_chat | Media | ✅ Cumple | ai_models |
| RF-14 | Predicción Rendimiento | Modelos predictivos (Prophet/LSTM) para cosecha | Media | ✅ Cumple | predictivo |
| RF-15 | Modelo Hídrico | Optimización de riego basada en datos de sensores | Media | ✅ Cumple | riego |

### 1.4 Control de Riego

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-16 | Riego Automatizado | Programación de riego basada en umbrales de sensor | Alta | ✅ Cumple | riego |
| RF-17 | Control PID | Algoritmo PID para válvulas solenoides | Media | ⚠️ Parcial | riego |
| RF-18 | Alertas de Sensor | Notificaciones cuando lecturas exceden umbrales | Alta | ✅ Cumple | riego/notifications |

### 1.5 Reportes y Exportación

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-19 | Reporte PDF | Generación de reportes de historial de cultivo en PDF | Media | ✅ Cumple | reports |
| RF-20 | Exportación XLSX | Exportación de lecturas a Excel | Baja | ✅ Cumple | reports |
| RF-21 | Dashboard Admin | Panel con estadísticas del sistema | Media | ✅ Cumple | admin |

### 1.6 Administración

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-22 | Django Admin | Panel de administración completo para gestión | Alta | ✅ Cumple | admin |
| RF-23 | Auditoría de Acciones | Log de operaciones críticas (CRUD usuarios, etc.) | Media | ⚠️ Parcial | core |
| RF-24 | Almacenamiento MinIO | Subida y gestión de archivos multimedia | Alta | ✅ Cumple | core/storage |
| RF-25 | Health Check | Endpoint público de estado del sistema | Alta | ✅ Cumple | core |

## 2. Requisitos No Funcionales

### 2.1 Seguridad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-01 | JWT Seguro | Tokens con expiración configurable, algoritmo HS256 | Alta | ✅ Cumple | Supabase gestiona |
| RNF-02 | API Keys Rotables | Keys por dispositivo con rotación forzada | Alta | ✅ Cumple | |
| RNF-03 | CORS Restrictivo | Solo orígenes en lista blanca | Alta | ✅ Cumple | |
| RNF-04 | Rate Limit | Máximo N requests/minuto por usuario | Media | ⚠️ Parcial | django-ratelimit presente, no universal |
| RNF-05 | Contraseñas Seguras | Hashing con bcrypt (delegado a Supabase) | Alta | ✅ Cumple | |
| RNF-06 | Anti-SQL Injection | Uso exclusivo de Django ORM | Alta | ✅ Cumple | |
| RNF-07 | Path Traversal | Validación de rutas en uploads | Alta | ⚠️ Verificar | |

### 2.2 Resiliencia

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-08 | Reintentos Celery | Reintentos automáticos con backoff (tenacity) | Alta | ⚠️ Parcial | No todas las tasks |
| RNF-09 | Dead-Letter Queue | Cola separada para tareas que fallan permanentemente | Media | ❌ No cumple | Pendiente de implementar |
| RNF-10 | Degradación Gradual | Respuesta parcial si microservicio externo falla | Alta | ⚠️ Parcial | |
| RNF-11 | Connection Pool | Pool de conexiones PostgreSQL | Alta | ✅ Cumple | django-db-connection-pool |

### 2.3 Performance

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-12 | Cache Redis | Cache de queries frecuentes con django-redis | Alta | ✅ Cumple | |
| RNF-13 | Bulk Insert | Inserción masiva optimizada (bulk_create) | Alta | ✅ Cumple | |
| RNF-14 | Downsampling Automático | Reducción de resolución de datos >30 días | Media | ✅ Cumple | Tasks Celery programadas |
| RNF-15 | Paginación DRF | Paginación en todos los listados | Alta | ✅ Cumple | PageNumberPagination |
| RNF-16 | Timeout Microservicios | Timeout max 30s en llamadas externas | Alta | ✅ Cumple | |

### 2.4 Mantenibilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-17 | Type Hints | Tipado estático en funciones públicas | Media | ⚠️ Parcial | ~30% de cobertura |
| RNF-18 | Docstrings | Documentación inline en clases críticas | Media | ⚠️ Parcial | |
| RNF-19 | Suite de Tests | Tests unitarios y de integración | Alta | ✅ Cumple | ~900+ tests |
| RNF-20 | Settings por Entorno | Separación dev/staging/prod | Alta | ❌ No cumple | Monolítico settings.py |

### 2.5 Observabilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-21 | Logging Estructurado | Logs con formato consistente por app | Media | ⚠️ Parcial | |
| RNF-22 | Tracking Celery | Monitoreo de tareas en Django Admin | Alta | ✅ Cumple | |
| RNF-23 | OpenTelemetry | Exportación de trazas a backend OTLP | Baja | ⚠️ Parcial | Referencias en código, no implementado |
| RNF-24 | Health Check | Endpoint /api/health con estado de servicios | Alta | ✅ Cumple | |

## 3. Deuda Técnica

| ID | Deuda | Impacto | Prioridad | Módulo | Acción Recomendada |
|----|-------|---------|-----------|--------|-------------------|
| TD-01 | Shadowing `starlette/` y `pwd/` | **Crítico** — Rompe imports | Alta | apps/ | Renombrar o mover directorios locales |
| TD-02 | Env vars duplicadas | **Alto** — Inconsistencia silenciosa | Alta | settings.py | Unificar a una sola variable por servicio. **2026-07-06**: Eliminadas 11 vars no consumidas del `.env` (ADMIN_API_KEY, FARMER_API_KEY, MS3_S3_BUCKET, MS3_S3_ENDPOINT, VECTOR_DB_PATH, etc.). Variables MS3_S3_* duplicadas de AWS_* eliminadas. Pendiente: renombrar variables con nombre tecnológico (AWS_, NVIDIA_, POSTGRES_, REDIS_, etc.) a nombres neutrales. |
| TD-03 | Settings monolítico | **Medio** — Mantenibilidad reducida | Media | settings.py | Dividir en `base.py`, `dev.py`, `staging.py`, `prod.py` |
| TD-04 | Views sin type hints | **Medio** — Legibilidad | Baja | Varias apps | Agregar type hints gradualmente |
| TD-05 | Código legacy no referenciado | **Medio** — Ruido | Baja | chat/, otras | Auditar y eliminar código muerto |
| TD-06 | Sin `coverage` configurado | **Medio** — Sin métrica | Media | pyproject.toml | Agregar coverage + umbral en CI |
| TD-07 | Dependencias sin pin | **Alto** — Rotura silenciosa | Alta | requirements/ | Pinneadar versiones en requirements.txt |
| TD-08 | Sin pre-commit hooks | **Bajo** — Estilo inconsistente | Baja | — | Agregar pre-commit con ruff + black |
| TD-09 | `os.getenv` vs `decouple.config` | **Medio** — Auditoría | Media | Varias apps | Unificar a `decouple.config` |

## 4. Bugs Identificados

| ID | Bug | Severidad | Módulo | Causa Raíz | Solución Propuesta |
|----|-----|-----------|--------|-----------|-------------------|
| BUG-01 | Import collision `starlette` | **Crítica** | apps/starlette/ | Directorio local oculta paquete pip | Renombrar a `apps/starlette_app/` o similar |
| BUG-02 | Import collision `pwd` | **Alta** | apps/pwd/ | Directorio local oculta stdlib | Renombrar a `apps/pwd_app/` o similar |
| BUG-03 | DB URL inconsistente | **Alta** | settings.py | 3+ variables de entorno para DB (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` además de `DATABASE_URL`) | Unificar a `DATABASE_URL` + validación al startup. Las variables `POSTGRES_*` se mantienen para el servicio `postgres` en docker-compose (la imagen oficial las requiere). `settings.py` usa `DATABASE_URL` como fuente principal. |
| BUG-04 | DecoupleValueError | **Media** | Varias apps | Env var faltante sin manejo | Agregar validación temprana con `ValidationError` |

## 5. Cumplimiento Normativo

| Norma | Estado | Evidencia | Brecha |
|-------|--------|-----------|--------|
| **LFPDPPP** | ⚠️ Parcial | Logging sin PII en algunos módulos | No hay sanitización consistente de datos personales en logs; falta política de retención |
| **NOM-059-SEMARNAT** | ✅ Cumple (mole_vision) | Double layer: prompt sentinel + regex post-inference | core_backend no expone visión directamente; depende de mole_vision que sí cumple |
| **MoProSoft** | ⚠️ Parcial | CI/CD con pruebas automatizadas | Faltan procesos formales documentados (gestión de requisitos, aseguramiento de calidad) |
| **ISO 25000** | ⚠️ Parcial | Suite de tests extensa (~900+) | Sin métricas de mantenibilidad, eficiencia, portabilidad; sin umbral de cobertura en CI |
