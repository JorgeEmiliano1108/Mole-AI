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
- **Autenticación** – Gestiona login, registro, verificación de email y emisión de tokens JWT.
- **Authentication** – Gestión de login, registro y emisión de tokens JWT.
- **User Management** – Operaciones CRUD sobre usuarios y registro de auditoría.
- **Device Management** – Asociación de dispositivos IoT a usuarios/plantas.
- **Telemetry** – Ingesta, almacenamiento y agregación de lecturas de sensores.
- **RAG Processing** – Ingesta de documentos PDF y generación de embeddings para búsqueda semántica (sin detallar implementación interna).
- **API Layer** – Exposición de endpoints REST que aplican permisos y throttling.
- **Background Workers** – Ejecución de tareas asíncronas y procesamiento de datos en segundo plano.

## Vista de componentes (C4 – Nivel 3) – ms1_vision
- **Servicio de visión** – Analiza imágenes de plantas y genera diagnóstico estructurado; consume modelo de visión externo y expone el endpoint `/api/v1/vision/analyze/`.

## Vista de componentes (C4 – Nivel 3) – ms2_chat
- **Servicio de chat IA** – Recibe mensajes de usuarios, ejecuta RAG con embeddings almacenados y devuelve respuestas; utiliza un modelo de chat externo y expone el endpoint `/api/v1/mole-ai/chat`.

## Vista de componentes (C4 – Nivel 3) – ms3_reports
- **Servicio de generación de reportes** – Crea PDFs a partir de datos de sensores bajo demanda, gestiona trabajos asíncronos y provee URLs pre‑firmadas para descarga; expone el endpoint `/api/v1/reports/generate`.

## Vista de despliegue (C4 – Nivel 4)
- Todos los contenedores se ejecutan sobre una red Docker (`mole_public`, `mole_internal`).
- **NGINX** actúa como terminador TLS y router; los puertos expuestos se configuran en `docker‑compose.yml`. 
- **Redis** y **PostgreSQL** se despliegan como servicios stateful con volúmenes persistentes (`backend_logs`, `postgres_data`).
- **AWS S3** es un recurso externo; las credenciales se suministran mediante variables de entorno (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
- **Celery workers** se escalan de forma independiente (configurable mediante `docker‑compose scale`).
- **MQTT broker** y **edge_node** operan en la red interna; el broker está expuesto en los puertos configurados en `docker‑compose.yml`.

## Cross‑cutting Concepts (arc42 Sección 7)
- **Seguridad** – TLS en NGINX, JWT con expiración < 30 min, permission classes, anti‑replay y rate‑limit.
- **Observabilidad** – Métricas con Prometheus, trazas OpenTelemetry, logs estructurados.
- **Resiliencia** – Se contempla el uso de circuit‑breaker y retries en llamadas a servicios externos; aún no está implementado.

## Decisiones arquitectónicas confirmadas
| Decisión | Motivo | Estado |
|----------|--------|-------|
| **Motor de visión activo** | Reemplazo de TFLite por un modelo de visión externo (NVIDIA Vision). | Implementado.
| **Almacenamiento de objetos** | Descarte de MinIO por lentitud; adopción de **AWS S3** como backend definitivo. | Implementado.
| **Variables NVIDIA unificadas** | Centralizar la selección de modelos mediante variables de entorno (p.ej. `NVIDIA_VISION_MODEL`, `NVIDIA_CHAT_MODEL`, `NVIDIA_REPORT_MODEL`, `NVIDIA_EMBEDDING_MODEL`). | Implementado.
| **Rol Admin con amplio control** | Admin tiene privilegios sobre usuarios, plantas y auditoría, pero **no** puede modificar variables NVIDIA_* (RF‑12 fuera de alcance). | Parcialmente implementado.
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
| Seguridad | Expiración del JWT | ≤ 30 min |
| Performance | Latencia para endpoints críticos (login, telemetría, chat) | ≤ 200 ms |
| Observabilidad | Cobertura de métricas con Prometheus | 100 % de servicios instrumentados |
| Maintainability | Cobertura de pruebas unitarias + integración | ≥ 80 % |

## Riesgos y trade‑offs
| Riesgo | Impacto | Mitigación |
|--------|----------|------------|
| **Dependencia de APIs externas de NVIDIA** | Si el endpoint NIM deja de estar disponible, los servicios de visión, chat y embeddings fallarán. | Monitorizar disponibilidad vía health‑checks; el fallback local será una evolución futura. |
| **Latencia de S3** | Acceso a PDFs y reportes depende de la red hacia AWS, pudiendo afectar tiempos de respuesta. | Cachear metadatos críticos en Redis y usar multipart upload para reducir sobrecarga. |
| **Escalado de Celery** | Un solo worker podría convertirse en cuello de botella bajo alta carga de ingestión. | Configurar número de workers y colas (`celery -Q reports_queue,training_queue`). |
| **Gestión de credenciales** | Exposición accidental de `JWT_SECRET_KEY` o credenciales AWS compromete la seguridad. | Usar Docker secrets / AWS Parameter Store y habilitar rotación periódica. |
| **Complejidad de microservicios** | Aumenta la superficie de ataque y el coste operativo. | Mantener documentación actualizada, aplicar pruebas de integración y usar herramientas de orquestación (Docker‑Compose, Kubernetes). |
| **Modelo de visión estático** | Cambiar el modelo requiere redeploy del servicio de visión. | Variables `NVIDIA_VISION_MODEL` permiten cambiar modelo sin modificar código; solo es necesario reiniciar el servicio. |
| **Tamaño de la tabla pgvector** | Crecimiento ilimitado de embeddings puede degradar performance. | Implementar políticas de retención (p. ej., eliminar chunks > 2 años) y crear índices GIN eficientes. |

## Evolución futura (no confirmada)
- Migración a orquestador Kubernetes para gestión automática de escalado y despliegues.
- Sustitución de la SPA actual por una aplicación móvil nativa (p. ej., Flutter) que consuma los mismos endpoints.
- Incorporación de modelos ONNX como fallback local para visión y embeddings.
- Implementación de un portal de gestión de configuración (feature flag service).
