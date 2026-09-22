# Requisitos de core_backend — Monolito Django

> Nota 2026-09-14: estados corregidos contra código. La fuente normativa de gaps
> es `docs/README.md` (mismo directorio) + `audit-matrix.md` (raíz).

## 1. Requisitos Funcionales

### 1.1 Autenticación y Seguridad

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-01 | Login JWT | Autenticación local JWT HS256 (Supabase solo validación opcional, deshabilitada por defecto) | Alta | ✅ Cumple | authentication |
| RF-02 | Refresh Token | Renovación de tokens JWT expirados | Alta | ✅ Cumple | authentication |
| RF-03 | API Key por Dispositivo | Identificación y autorización de dispositivos IoT mediante API Key | Alta | ✅ Cumple | authentication + core (no existe app `devices`) |
| RF-04 | CRUD Usuarios | Gestión de usuarios con roles (admin, agricultor, técnico) | Alta | ⚠️ Parcial | authentication (solo alta vía `admin/users/create/`; sin CRUD completo ni app `users`) |
| RF-05 | Rate Limiting | Límite de requests por usuario/IP para prevenir abuso | Media | ⚠️ Parcial | core (`throttles.py` DRF; `DiagnosticsThrottle` sin aplicar) |
| RF-06 | CORS Configurable | Orígenes permitidos configurables por entorno | Alta | ❌ No cumple | CORS vacío en Django; lo sirve Nginx |

### 1.2 IoT y Telemetría

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-07 | Ingesta M2M | Recepción de telemetría desde dispositivos IoT vía M2M | Alta | ✅ Cumple | core (no existe app `m2m`) |
| RF-08 | Bulk Insert Sensores | Inserción masiva de lecturas de sensores | Alta | ✅ Cumple | core (no existe app `sensores`) |
| RF-09 | Downsampling Histórico | Reducción de resolución de datos antiguos para retención | Media | ❌ No cumple | Task existe pero fuera de `CELERY_BEAT_SCHEDULE` |
| RF-10 | Geocercas | Definición de perímetros virtuales para parcelas | Media | ❌ No implementado | (no existe app `cultivos`) |
| RF-11 | Edge Processing | Procesamiento local en nodos edge antes de envío | Baja | ❌ No implementado | Lo hace `edge_node/` fuera de Django |

### 1.3 Inteligencia Artificial

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-12 | Diagnóstico por Visión | Análisis de imágenes de cultivos via mole_vision | Alta | ✅ Cumple | ai_models |
| RF-13 | Chat Contextual | Conversación con RAG sobre cultivos via mole_chat | Media | ✅ Cumple | ai_models |
| RF-14 | Predicción Rendimiento | Modelos predictivos (Prophet/LSTM) para cosecha | Media | ❌ No implementado | `model_performance_view` mide al modelo IA, no al cultivo (no existe app `predictivo`) |
| RF-15 | Modelo Hídrico | Optimización de riego basada en datos de sensores | Media | ❌ No implementado | (no existe app `riego`) |

### 1.4 Control de Riego

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-16 | Riego Automatizado | Programación de riego basada en umbrales de sensor | Alta | ❌ No implementado | (no existe app `riego`) |
| RF-17 | Control PID | Algoritmo PID para válvulas solenoides | Media | ❌ No implementado | — |
| RF-18 | Alertas de Sensor | Notificaciones cuando lecturas exceden umbrales | Alta | ⚠️ Parcial | `core/admin_views.py:live_alerts_view` (solo admin, sin push) |

### 1.5 Reportes y Exportación

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-19 | Reporte PDF | Generación de reportes de historial de cultivo en PDF | Media | ⚠️ Parcial | Delegado a MS3 externo + PDF de diagnósticos local (no existe app `reports`) |
| RF-20 | Exportación XLSX | Exportación de lecturas a Excel | Baja | ❌ No cumple | Solo CSV de datos viejos |
| RF-21 | Dashboard Admin | Panel con estadísticas del sistema | Media | ✅ Cumple | `core/admin_views.py` (no existe app `admin`) |

### 1.6 Administración

| ID | Nombre | Descripción | Prioridad | Estado | Módulo |
|----|--------|-------------|-----------|--------|--------|
| RF-22 | Django Admin | Panel de administración completo para gestión | Alta | ⚠️ Parcial | Registro parcial de modelos |
| RF-23 | Auditoría de Acciones | Log de operaciones críticas (CRUD usuarios, etc.) | Media | ⚠️ Parcial | core |
| RF-24 | Almacenamiento MinIO | Subida y gestión de archivos multimedia | Alta | ✅ Cumple | core/storage |
| RF-25 | Health Check | Endpoint público de estado del sistema | Alta | ✅ Cumple | core |

## 2. Requisitos No Funcionales

### 2.1 Seguridad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-01 | JWT Seguro | Tokens con expiración configurable, algoritmo HS256 | Alta | ✅ Cumple | Supabase gestiona |
| RNF-02 | API Keys Rotables | Keys por dispositivo con rotación forzada | Alta | ❌ No cumple | Solo `revoke/` (soft-delete), sin rotación ni expiración |
| RNF-03 | CORS Restrictivo | Solo orígenes en lista blanca | Alta | ❌ No cumple | `CORS_ALLOWED_ORIGINS=[]` en Django; CORS real en Nginx |
| RNF-04 | Rate Limit | Máximo N requests/minuto por usuario | Media | ⚠️ Parcial | DRF throttles (no django-ratelimit), cobertura parcial |
| RNF-05 | Contraseñas Seguras | Hashing con bcrypt (delegado a Supabase) | Alta | ❌ No cumple | Argon2/PBKDF2; HS256 JWT; sin bcrypt ni Auth0 |
| RNF-06 | Anti-SQL Injection | Uso exclusivo de Django ORM | Alta | ✅ Cumple | |
| RNF-07 | Path Traversal | Validación de rutas en uploads | Alta | ⚠️ Verificar | |

### 2.2 Resiliencia

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-08 | Reintentos Celery | Reintentos automáticos con backoff (tenacity) | Alta | ⚠️ Parcial | No todas las tasks |
| RNF-09 | Dead-Letter Queue | Cola separada para tareas que fallan permanentemente | Media | ❌ No cumple | Pendiente de implementar |
| RNF-10 | Degradación Gradual | Respuesta parcial si microservicio externo falla | Alta | ⚠️ Parcial | |
| RNF-11 | Connection Pool | Pool de conexiones PostgreSQL | Alta | ❌ No cumple | Solo `CONN_MAX_AGE`; sin pgBouncer ni `django-db-connection-pool` |

### 2.3 Performance

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-12 | Cache Redis | Cache de queries frecuentes con django-redis | Alta | ✅ Cumple | |
| RNF-13 | Bulk Insert | Inserción masiva optimizada (bulk_create) | Alta | ✅ Cumple | |
| RNF-14 | Downsampling Automático | Reducción de resolución de datos >30 días | Media | ❌ No cumple | Task existe, fuera de beat schedule |
| RNF-15 | Paginación DRF | Paginación en todos los listados | Alta | ❌ No cumple | Sin `DEFAULT_PAGINATION_CLASS` |
| RNF-16 | Timeout Microservicios | Timeout max 30s en llamadas externas | Alta | ⚠️ Parcial | 30s default; 60s IA/llm_chat; 120s Mole-AI |

### 2.4 Mantenibilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-17 | Type Hints | Tipado estático en funciones públicas | Media | ⚠️ Parcial | ~30% de cobertura |
| RNF-18 | Docstrings | Documentación inline en clases críticas | Media | ⚠️ Parcial | |
| RNF-19 | Suite de Tests | Tests unitarios y de integración | Alta | ⚠️ Parcial | 32 ficheros / 81 funciones (no ~900); `pytest.ini` con ignores documentados |
| RNF-20 | Settings por Entorno | Separación dev/staging/prod | Alta | ❌ No cumple | Monolítico settings.py |

### 2.5 Observabilidad

| ID | Nombre | Descripción | Prioridad | Estado | Notas |
|----|--------|-------------|-----------|--------|-------|
| RNF-21 | Logging Estructurado | Logs con formato consistente por app | Media | ⚠️ Parcial | |
| RNF-22 | Tracking Celery | Monitoreo de tareas en Django Admin | Alta | ❌ No cumple | `django-celery-results` no instalado |
| RNF-23 | OpenTelemetry | Exportación de trazas a backend OTLP | Baja | ❌ No cumple | Solo 1 test ignorado; cero producción |
| RNF-24 | Health Check | Endpoint /api/health con estado de servicios | Alta | ✅ Cumple | |

## 3. Deuda Técnica

| ID | Deuda | Impacto | Prioridad | Módulo | Acción Recomendada |
|----|-------|---------|-----------|--------|-------------------|
| TD-01 | ~~Shadowing `starlette/` y `pwd/`~~ — **Cerrado 2026-09-14**: directorios inexistentes | — | Alta | — | — |
| TD-02 | Env vars duplicadas | **Medio** — Mitigado 2026-09 con `_env_first` + `_resolve_db_url` | Alta | settings.py | Completar split por entorno |
| TD-03 | Settings monolítico | **Medio** — Mantenibilidad reducida | Media | settings.py | Dividir en `base.py`, `dev.py`, `staging.py`, `prod.py` |
| TD-04 | Views sin type hints | **Medio** — Legibilidad | Baja | Varias apps | Agregar type hints gradualmente |
| TD-05 | Código legacy no referenciado | **Medio** — Ruido | Baja | chat/, otras | Auditar y eliminar código muerto |
| TD-06 | Sin `coverage` configurado | **Medio** — Sin métrica | Media | (no existe `pyproject.toml`) | Agregar coverage + umbral en CI |
| TD-07 | Dependencias con `>=` abiertos | **Medio** — Rotura silenciosa | Alta | `requirements.txt` (único) | Pinneadar versiones en requirements.txt |
| TD-08 | Sin pre-commit hooks | **Bajo** — Estilo inconsistente | Baja | — | Agregar pre-commit con ruff + black |
| TD-09 | ~~`os.getenv` vs `decouple.config`~~ — **No aplica**: cero `decouple` en código/requirements | — | Media | — | — |

## 4. Bugs Identificados

| ID | Bug | Severidad | Módulo | Causa Raíz | Solución Propuesta |
|----|-----|-----------|--------|-----------|-------------------|
| BUG-01 | ~~Import collision `starlette`~~ — **Cerrado**: directorio inexistente | — | apps/ | — | — |
| BUG-02 | ~~Import collision `pwd`~~ — **Cerrado**: directorio inexistente | — | apps/ | — | — |
| BUG-03 | DB URL inconsistente | **Media** — Mitigado 2026-09 con `_resolve_db_url` | settings.py | Múltiples vars | `DB_URL` manda; partes `DB_*` como fallback |
| BUG-04 | ~~DecoupleValueError~~ — **No aplica**: sin `decouple` | — | — | — | — |

## 5. Cumplimiento Normativo

| Norma | Estado | Evidencia | Brecha |
|-------|--------|-----------|--------|
| **LFPDPPP** | ⚠️ Parcial | Logging sin PII en algunos módulos | No hay sanitización consistente de datos personales en logs; falta política de retención |
| **NOM-059-SEMARNAT** | ✅ Cumple (mole_vision) | Double layer: prompt sentinel + regex post-inference | core_backend no expone visión directamente; depende de mole_vision que sí cumple |
| **MoProSoft** | ⚠️ Parcial | CI/CD con pruebas automatizadas | Faltan procesos formales documentados (gestión de requisitos, aseguramiento de calidad) |
| **ISO 25000** | ⚠️ Parcial | 32 ficheros / 81 funciones; ver `docs/anexos/COMPLIANCE_EXECUTIVE_SUMMARY.md` (36%) | Sin métricas de mantenibilidad, eficiencia, portabilidad; sin umbral de cobertura en CI |
