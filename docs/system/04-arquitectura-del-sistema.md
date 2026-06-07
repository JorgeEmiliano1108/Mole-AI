# Arquitectura del sistema

## Propósito
Describir la arquitectura técnica de MOLE‑AI siguiendo la plantilla arc42 y el modelo C4, de modo que cualquier lector pueda comprender la organización de los componentes, sus interacciones y las decisiones que sustentan la solución.

## Vista de contexto (C4 – Nivel 1)

```
[Usuario final] ──► HTTPS (API REST) ◄───► [Frontend SPA (HTML/JS)]
                         │
                         ▼
                     [NGINX]
                         │
  ┌──────────────────────┼───────────────────────┐
  │                      │                       │
  ▼                      ▼                       ▼
[Core Django]   [ms1_vision]   [ms2_chat]   [ms3_reports]
   │                │               │               │
   ▼                ▼               ▼               ▼
[PostgreSQL]   [AWS S3]        [AWS S3]        [AWS S3]
   │                │               │               │
   ▼                ▼               ▼               ▼
[Redis]        [Redis]        [Redis]        [Redis]
   │                │               │               │
   ▼                ▼               ▼               ▼
[Celery Workers] (tasks) (tasks) (tasks)
   │
   ▼
[MQTT Broker] ◄─ Edge Node (ESP32) ◄─ Sensors
```
*Los usuarios finales acceden a través del navegador a la SPA que consume los endpoints REST expuestos por Nginx.  Nginx actúa como único punto de entrada, terminando TLS y gestionando CORS.*

## Vista de contenedores (C4 – Nivel 2)
| Contenedor | Tecnologías | Responsabilidad principal |
|------------|-------------|---------------------------|
| **NGINX** | Nginx (Docker) | Terminación TLS, routing a `/api/v1/*`, gestión de CORS, health‑checks. |
| **Core Django Backend** | Django 5, Django‑REST‑Framework, Channels, Axes, pgvector, PostgreSQL | Gestión de usuarios, dispositivos, telemetría, auditoría, publicación de eventos MQTT, exposición de API de gestión. |
| **ms1_vision** | FastAPI (abstract) | Servicio de visión: análisis de imágenes de plantas y generación de diagnóstico estructurado. |
| **ms2_chat** | FastAPI (abstract) | Servicio de chat IA con RAG/CAG, ingestión de PDFs y búsqueda semántica. |
| **ms3_reports** | FastAPI (abstract) | Servicio de generación de reportes PDF bajo demanda y gestión de jobs con URLs pre‑firmadas. |
| **Redis** | Redis 7 (in‑memory) | Cache de datos críticos (sensores, citations), broker de Celery, Pub/Sub para RAG listener. |
| **PostgreSQL + pgvector** | PostgreSQL 13, extensión pgvector | Almacenamiento transaccional (usuarios, plantas, telemetría) y vectores de embedding (botanical_knowledge). |
| **AWS S3** | Amazon S3 | Almacenamiento definitivo de PDFs, reportes y cualquier archivo binario. |
| **Celery Workers** | Celery, RabbitMQ/Redis broker | Ejecución asíncrona de tareas pesadas (embeddings, visión, generación de PDFs). |
| **MQTT Broker** | Eclipse Mosquitto | Canal de telemetría de bajo consumo para dispositivos ESP32. |
| **Edge Node** | Docker (custom), WebSocket → HTTP | Gateway que recibe datos de los ESP32 vía WebSocket y los envía en lote al endpoint `/api/v1/sensor-data/batch/`. |

## Vista de componentes (C4 – Nivel 3) – Core Django
- **Authentication Module** – `apps.authentication` (views, models, backends, JWT middleware).  Provee login, registro, verificación de email y gestión de tokens.
- **User Management** – `User` (custom model) y `AuditLog`.  Registro inmutable de acciones críticas.
- **Device Management** – `Device`, `HardwareBinding`.  Relaciona dispositivos hardware con plantas.
- **Telemetry Module** – `AmbientReading`, `SoilReading`, `Hourly*Aggregate`.  Guarda lecturas y agrega datos horarios.
- **RAG Listener** – Servicio asíncrono (`apps.infrastructure.adapters.rag_listener`) que suscribe a Redis `mole:training:new_asset`, descarga PDFs desde **AWS S3**, extrae texto, genera embeddings con `NVIDIA_EMBEDDING_MODEL` y persiste en `botanical_knowledge`.
- **API Layer** – Routers bajo `apps.core.urls`, `apps.plants.urls`, `apps.authentication.urls`.  Cada endpoint declara permisos y throttling.
- **Background Workers** – Celery tasks (`apps.core.tasks`, `apps.report.tasks`).

## Vista de componentes (C4 – Nivel 3) – ms1_vision
- **Vision Service** – `NvidiaVisionAdapter` implementa la interfaz `VisionClientPort`.
- **NvidiaBaseClient** – Wrapper que llama a la API de NVIDIA NIM (`generate_vision`).
- **Domain Entities** – `DiagnosticResult`, `SeverityLevel`, `ConditionCategory` para normalizar la respuesta.

## Vista de componentes (C4 – Nivel 3) – ms2_chat
- **Chat Service** – `MoleAIClient` que envía prompts al modelo `NVIDIA_CHAT_MODEL`.
- **Embedding Service** – `NvidiaEmbeddingAdapter` (no expuesto como endpoint, usado por RAG listener) que genera vectores con `NVIDIA_EMBEDDING_MODEL`.
- **RAG Store** – `PgVectorStore` encapsula operaciones CRUD sobre `botanical_knowledge`.
- **Citation Manager** – `CitationManager` agrupa referencias de documentos en respuestas.

## Vista de componentes (C4 – Nivel 3) – ms3_reports
- **Report Generator** – `ReportBuilder` que recopila datos de sensores, los formatea y produce PDF mediante WeasyPrint.
- **Job Metadata Store** – `JobMetadataStore` (Redis) persiste estado de generación y URLs.
- **Celery Task** – `generate_report_task` que orquesta la creación del PDF y su subida a S3.

## Vista de despliegue (C4 – Nivel 4)
- Todos los contenedores se ejecutan sobre una red Docker (`mole_public`, `mole_internal`).
- **NGINX** expone los puertos 80 (interno) y 8080 (exterior) y enruta los sub‑paths `/api/v1/*` a los contenedores correspondientes.
- **Redis** y **PostgreSQL** se despliegan como servicios stateful con volúmenes persistentes (`backend_logs`, `postgres_data`).
- **AWS S3** es un recurso externo; las credenciales se suministran mediante variables de entorno (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
- **Celery workers** se escalan de forma independiente (configurable mediante `docker‑compose scale`).
- **MQTT broker** y **edge_node** operan en la red interna; el broker está expuesto en puertos 1883 (inseguro, para migración) y 8883 (TLS) para los dispositivos.

## Cross‑cutting Concepts (arc42 Sección 7)
- **Seguridad** – TLS en NGINX, JWT con expiración < 30 min, permission classes, anti‑replay y rate‑limit.
- **Observabilidad** – Métricas con Prometheus, trazas OpenTelemetry, logs estructurados.
- **Resiliencia** – Se contempla el uso de circuit‑breaker y retries en llamadas a servicios externos; aún no está implementado.

## Decisiones arquitectónicas confirmadas
| Decisión | Motivo | Estado |
|----------|--------|-------|
| **Motor de visión activo** | Reemplazo de TFLite por **NVIDIA Vision** (Llama 3.2‑vision‑instruct) mediante `NvidiaVisionAdapter`. | Implementado.
| **Almacenamiento de objetos** | Descarte de MinIO por lentitud; adopción de **AWS S3** como backend definitivo. | Implementado.
| **Variables NVIDIA unificadas** | Centralizar la selección de modelos mediante `NVIDIA_VISION_MODEL`, `NVIDIA_CHAT_MODEL`, `NVIDIA_REPORT_MODEL`, `NVIDIA_EMBEDDING_MODEL`. | Implementado.
| **Rol Admin con control total** | Ampliación del alcance de admin para incluir gestión de modelos, agentes, analítica y configuración global. | Implementado.
| **Microservicios independientes** | Facilita escalado horizontal y aislamiento de fallos. | Implementado.
| **Uso de pgvector** | Permite búsqueda semántica de documentos de conocimiento. | Implementado.
| **Celery + Redis** | Desacopla procesos intensivos del ciclo de petición‑respuesta. | Implementado.
| **Observabilidad con Prometheus** | Métricas de latencia, conteo de peticiones y health‑checks. | Implementado.
| **Seguridad JWT y throttling** | Garantiza autenticación segura, expiración controlada y limitación de abuso. | Implementado.
| **Anti‑replay en telemetría** | Previene inyección de datos obsoletos, Δ ≤ 300 s. | Implementado.
| **Filtro NOM‑059** | Bloquea consultas que exploren actividades prohibidas por normativa. | Implementado.

## Quality Goals (arc42 Sección 9)

| Goal | Metric | Threshold |
|------|--------|-----------|
| Disponibilidad | % uptime del API | ≥ 99.5 % |
| Seguridad | Expiración del JWT | < 30 min |
| Performance | Latencia para endpoints críticos (login, telemetría, chat) | ≤ 200 ms |
| Observabilidad | Cobertura de métricas con Prometheus | 100 % de servicios instrumentados |
| Maintainability | Cobertura de pruebas unitarias + integración | ≥ 80 % |

## Riesgos y trade‑offs
| Riesgo | Impacto | Mitigación |
|--------|----------|------------|
| **Dependencia de APIs externas de NVIDIA** | Si el endpoint NIM deja de estar disponible, los servicios de visión, chat y embeddings fallarán. | Implementar fallback a modelos locales (p. ej., ONNX) y monitorizar disponibilidad vía health‑checks. |
| **Latencia de S3** | Acceso a PDFs y reportes depende de la red hacia AWS, pudiendo afectar tiempos de respuesta. | Cachear metadatos críticos en Redis y usar multipart upload para reducir sobrecarga. |
| **Escalado de Celery** | Un solo worker podría convertirse en cuello de botella bajo alta carga de ingestión. | Configurar número de workers y colas (`celery -Q reports_queue,training_queue`). |
| **Gestión de credenciales** | Exposición accidental de `JWT_SECRET_KEY` o credenciales AWS compromete la seguridad. | Usar Docker secrets / AWS Parameter Store y habilitar rotación periódica. |
| **Complejidad de microservicios** | Aumenta la superficie de ataque y el coste operativo. | Mantener documentación actualizada, aplicar pruebas de integración y usar herramientas de orquestación (Docker‑Compose, Kubernetes). |
| **Modelo de visión estático** | Cambiar el modelo requiere redeploy del contenedor `ms1_vision`. | Variables `NVIDIA_VISION_MODEL` permiten cambiar modelo sin modificar código; solo es necesario reiniciar el contenedor. |
| **Tamaño de la tabla pgvector** | Crecimiento ilimitado de embeddings puede degradar performance. | Implementar políticas de retención (p. ej., eliminar chunks > 2 años) y crear índices GIN eficientes. |

## Evolución futura (no confirmada)
- Migración a orquestador Kubernetes para gestión automática de escalado y despliegues.
- Sustitución de la SPA actual por una aplicación móvil nativa (p. ej., Flutter) que consuma los mismos endpoints.
- Incorporación de modelos ONNX como fallback local para visión y embeddings.
- Implementación de un portal de gestión de configuración (feature flag service).
