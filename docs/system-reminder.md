# PRD Técnico Maestro – MOLE‑AI

---

## 1. Visión global
MOLE‑AI es una plataforma de asistencia agronómica basada en inteligencia artificial que **integra**:
- **Captura y gestión de telemetría IoT** (sensores instalados en campo).
- **Chat de consulta** que combina un Large Language Model (LLM) con búsqueda semántica (RAG).
- **Análisis visual de imágenes** mediante el modelo de visión NVIDIA.
- **Generación de reportes** en PDF, almacenados en AWS S3.
- **Auditoría y trazabilidad** de todas las operaciones críticas.

El objetivo del PRD es describir **qué está disponible hoy**, **qué se contempla para el futuro** y **qué queda fuera del alcance**, separando claramente la **deuda técnica** y los **riesgos**.

---

## 2. Alcance actual (producto entregado)

### Capacidades de producto
> **Nota:** La tabla muestra únicamente la capacidad observable por el usuario o administrador. Los detalles de endpoints, librerías y clases se encuentran en el **Anexo A – Detalles técnicos**.

| Área | Capacidad implementada (versión v1.0.0) |
|------|----------------------------------------|
| **Autenticación** | Login con *username* o *email* que devuelve un JWT firmado con HS256. |
| **Gestión de usuarios** | Registro, visualización, actualización de campos permitidos, eliminación con anonimización de PII y registro en auditoría. |
| **Roles** | `superuser`, `admin` (staff) y `user` (authenticated) con control de permisos basado en `IsAuthenticated` y `IsSuperuserOrReadOnly`. |
| **Plantas y especies** | CRUD de plantas por parte del propietario; CRUD de especies limitado a personal administrativo. |
| **Búsqueda pública de especies** | Consulta de catálogo con límite máximo de 50 resultados. |
| **Telemetría IoT** | Ingesta de lecturas individuales y por lote; incluye verificación anti‑replay (Δ ≤ 300 s) y throttling de 200 req/min. |
| **Chat IA (CAG)** | Respuestas contextuales que combinan un prompt estático, datos de sensores y vectores relevantes (RAG). |
| **Filtro NOM‑059** | Bloqueo automático de consultas que incluyen actividades prohibidas por la normativa. |
| **Visión IA** | Análisis de imágenes que devuelve diagnóstico estructurado (especie, condición, severidad, confianza, pH estimado). |
| **Ingesta de documentos PDF** | Procesamiento de PDFs: extracción, chunk‑eo, generación de embeddings con modelo NVIDIA y persistencia en tabla de conocimiento vectorial. |
| **Búsqueda semántica** | Recuperación de los *top‑k* chunks por similitud coseno dentro del flujo de chat. |
| **Generación de reportes** | Creación bajo demanda de PDFs que se almacenan en AWS S3 y se entregan mediante URL pre‑firmada. |
| **Auditoría** | Registro inmutable de acciones críticas; la tabla `audit_logs` solo permite inserciones. |

### Capacidades de plataforma/operación
| Área | Capacidad implementada (versión v1.0.0) |
|------|----------------------------------------|
| **Configuración de modelos** | Variables de entorno `NVIDIA_VISION_MODEL`, `NVIDIA_CHAT_MODEL`, `NVIDIA_REPORT_MODEL` y `NVIDIA_EMBEDDING_MODEL` son leídas al iniciar cada contenedor. |
| **Infraestructura** | Docker‑Compose que orquesta Nginx (TLS termination), Django backend, tres micro‑servicios FastAPI, PostgreSQL + pgvector, Redis, MQTT broker y AWS S3 para storage. |
| **Observabilidad** | Métricas Prometheus (`/metrics`), health‑checks (`/health/`) y logs estructurados mediante `structlog`. |

---

## 3. Alcance futuro (hipótesis de evolución, no compromisos)
> Las siguientes capacidades **se consideran hipótesis de evolución**; su implementación dependerá de priorización y recursos posteriores.

| Área | Capacidad futura (hipótesis) | Justificación / valor de negocio |
|------|------------------------------|---------------------------------|
| **Política de retención de chunks** | Purga automática de vectores antiguos (p. ej., > 2 años o > N GB). | Control de costes de almacenamiento y mantenimiento de rendimiento de pgvector. |
| **Interfaz de administración de variables NVIDIA** | UI o API para cambiar `NVIDIA_*` sin necesidad de reiniciar contenedores. | Reduce tiempo de reacción ante mejoras de modelo. |
| **Roles granulares** | Modelo de roles extensible (p. ej., *consultor*, *revisor*). | Permite delegar responsabilidades sin otorgar privilegios de super‑user. |
| **Fallback IA local** | Adaptadores ONNX / TensorRT como reserva si la API de NVIDIA falla. | Aumenta disponibilidad y disminuye dependencia externa. |
| **Dashboard y alertas** | Grafana + Alertmanager con paneles de latencia, error rate y uso de recursos. | Mejora detección proactiva de incidentes. |
| **CI/CD automatizado** | Pipelines de GitHub Actions que ejecuten lint, pruebas, build de imágenes y despliegue a un entorno de staging. | Asegura calidad continua y reduce errores manuales. |
| **Rotación de secrets** | Integración con AWS Secrets Manager o Docker secrets para rotar `JWT_SECRET_KEY`, credenciales AWS y `NVIDIA_API_KEY`. | Refuerza postura de seguridad. |
| **Orquestación con Kubernetes** | Manifiestos Helm / operadores para desplegar todo el stack en EKS. | Escalado automático, alta disponibilidad, despliegues blue/green. |
| **Backup y RTO** | Jobs de snapshots de RDS y versionado de objetos S3 con política de retención. | Cumplimiento de continuidad de negocio. |
| **SLA formal** | Documento que establezca latencia < 500 ms para búsquedas y uptime ≥ 99.5 %. | Proveer garantías contractuales a clientes. |
| **Pruebas de resiliencia** | Simulación de fallos de MQTT, Redis, PostgreSQL y verificación de recuperación automática. | Validar tolerancia a fallos de infraestructura. |

---

## 4. Fuera de alcance (no se considerará en la versión v1.0.0 ni en la hoja de ruta inmediata)
- **Frontend móvil nativo** (Flutter, React‑Native, etc.).
- **Entrenamiento de modelos propios** (solo se consumen modelos pre‑entrenados de NVIDIA).
- **Integración con proveedores de datos externos diferentes a Supabase o AWS.**
- **Marketplace de sensores** (venta o gestión comercial de hardware).
- **Funcionalidad de streaming de video en tiempo real para visión.**

---

## 5. Actores y sus responsabilidades
| Actor | Interacciones con el sistema |
|------|-------------------------------|
| **Agricultor / Usuario final** | Registro, login, gestión de sus plantas, envío de telemetría, consultas al chat, análisis de imágenes, generación de reportes. |
| **Administrador** | Cambio de variables `NVIDIA_*`, gestión de usuarios y plantas, supervisión de auditoría, monitorización de salud del sistema, ejecución de tareas de mantenimiento (p. ej., purga de chunks). |
| **Dispositivo IoT (hardware)** | Autenticación mediante `auth_token`; envío de lecturas de sensores (individual o batch). |
| **Operador de infraestructura** | Despliegue de contenedores, gestión de AWS (S3, RDS, Secrets Manager), monitorización (Prometheus), backup de bases de datos. |


---

## 6. Restricciones técnicas
> Componentes y condiciones obligatorias para que el sistema funcione correctamente.
- **NVIDIA NIM API** – Necesario para chat, visión y embeddings; su disponibilidad es un requisito externo crítico.
- **AWS S3** – Almacenamiento único de objetos; requiere credenciales válidas y política de bucket adecuada.
- **PostgreSQL 13+ con extensión pgvector** – Base de datos obligatoria; la extensión debe estar habilitada.
- **Redis** – Cache y broker de Celery; debe estar disponible y accesible desde todos los contenedores.
- **MQTT broker (Eclipse Mosquitto)** – Canal de telemetría TLS (puerto 8883).
- **TLS** – Todas las comunicaciones externas deben usar TLS 1.2+ (NGINX, MQTT).
- **Variables de entorno** – `NVIDIA_*`, `JWT_SECRET_KEY`, `AWS_*` deben estar definidas antes del arranque del contenedor.

---

## 7. Dependencias externas
> Proveedores de terceros fuera del control del equipo, cuya disponibilidad impacta directamente la operación del producto.
- **NVIDIA NIM API** – Endpoint esencial para chat, visión y embeddings.
- **AWS S3** – Almacenamiento permanente de PDFs, reportes y assets.

---
## 8. Deuda técnica (elementos que deben resolverse, no son requisitos)
| Elemento | Motivo de la deuda | Consecuencia funcional concreta |
|----------|---------------------|--------------------------------|
| `tflite_adapter.py` | Código legado sin uso; confunde la base de código. | Riesgo de mantenimiento innecesario y posibles errores si se reutiliza accidentalmente. |
| Comentarios de **MinIO** en `docker‑compose.yml` | Indica almacenamiento obsoleto; puede generar errores al intentar usarlo en producción. | Posible falla de despliegue o confusión operativa. |
| Ausencia de política de retención para `botanical_knowledge` | Crecimiento ilimitado de la tabla pgvector. | Degradación progresiva del tiempo de respuesta en búsquedas y aumento de costes de almacenamiento. |
| Credenciales en archivo `.env` sin rotación automática | Exposición potencial y dificultad para rotar claves. | Vulnerabilidad de seguridad y mayor esfuerzo manual para actualizaciones de secrets. |
| Falta de Alertmanager / Grafana | No hay notificaciones automáticas ante superación de límites. | Detección tardía de incidentes críticos (latencia, errores, saturación). |
| No hay CI/CD automatizado | Despliegues manuales incrementan probabilidad de error humano. | Riesgo de introducir bugs en producción y retrasos en entregas. |
| No existe fallback local a modelos IA | Dependencia total de NVIDIA; caída del servicio implica indisponibilidad total del chat/visión/embeddings. | Interrupción total de funcionalidades clave. |
| Modelo de roles limitado a `is_staff`/`is_superuser` | No permite granularidad futura sin refactor. | Dificultad para delegar permisos específicos sin sobrecargar privilegios. |
| Tests de resiliencia a fallos de infraestructura inexistentes | No se puede validar la tolerancia a caídas de Redis, PostgreSQL o MQTT. | Falta de evidencia de comportamiento bajo escenarios de falla. |
| No hay políticas de lifecycle en S3 | Los PDFs pueden acumularse indefinidamente, generando costes. | Coste operativo creciente y posible saturación del bucket. |
| SLA no formalizado | No hay compromiso contractual verificable para clientes. | Falta de garantía de nivel de servicio ante usuarios externos. |

---

## 9. Riesgos identificados
| Riesgo | Probabilidad | Impacto | Mitigación propuesta |
|--------|--------------|----------|----------------------|
| Caída del endpoint NVIDIA | Media | Alto (chat, visión y embeddings quedan inoperables) | Implementar adaptador ONNX como fallback; monitorizar health‑checks del endpoint. |
| Crecimiento descontrolado de `botanical_knowledge` | Media | Medio | Añadir job de purga programada, establecer límites de retención. |
| Exposición de secrets en `.env` | Baja | Alto | Migrar a AWS Secrets Manager / Docker secrets, habilitar rotación automatizada. |
| Falta de alertas proactivas | Media | Medio | Configurar Prometheus Alertmanager y paneles Grafana. |
| Escalado manual limitado (Docker‑Compose) | Alta (en producción) | Medio | Planificar migración a Kubernetes o autoscaling mediante Docker Swarm. |
| Dependencia de una única zona de disponibilidad AWS | Baja | Alto | Utilizar RDS Multi‑AZ y replicación de S3. |

---

## 10. Preguntas breves respondidas
1. **Capacidades del sistema que son producto (implementado)** – Se listan en la sección *Alcance actual*. La mayoría cuenta con pruebas automatizadas y health‑checks, aunque la cobertura completa puede variar.
2. **Partes que deben marcarse como alcance futuro** – Ver sección *Alcance futuro*; son funcionalidades planificadas pero no presentes en la versión v1.0.0.
3. **Elementos que deben quedar explícitamente en deuda técnica o fuera de alcance** – Deuda técnica enumerada en la sección *Deuda técnica*; fuera de alcance está descrito en la sección *Fuera de alcance*.

---

## Anexo A – Detalles técnicos (endpoints, librerías y clases relevantes)
| Área | Endpoint(s) / Clase(s) | Tecnologías clave |
|------|------------------------|-------------------|
| Autenticación | `POST /api/v1/auth/login/` – `login_view` (Django REST). | JWT, HS256, `settings.JWT_SECRET_KEY`. |
| Registro | `POST /api/v1/auth/register/` – `register_view`. | Validación de contraseña, envío de email de verificación. |
| Perfil | `GET/PATCH/DELETE /api/v1/auth/profile/` – `user_profile_view`. | `AuditLog` (inmutabilidad). |
| Plantas | `/api/v1/user-plants/`, `/api/v1/plants/<uuid>/` – `PlantCreateSerializer`, `PlantUpdateSerializer`. |
| Especies | `SpeciesViewSet` (FastAPI) – CRUD protegido por `IsSuperuserOrReadOnly`. |
| Telemetría | `POST /api/v1/sensor-data/`, `POST /api/v1/sensor-data/batch/` – `SensorReadingSerializer`, `SensorBatchSerializer`. |
| Chat | `POST /api/v1/mole-ai/chat` – `MoleAIChatUseCase`, `LlamaChatClient` (NVIDIA LLM). |
| Visión | `POST /api/v1/vision/analyze/` – `NvidiaVisionAdapter` → `NvidiaBaseClient.generate_vision`. |
| PDF ingest | `POST /api/v1/knowledge/ingest-pdf` – `RAGListener`, `PgVectorStore`, `NvidiaEmbeddingAdapter`. |
| Reportes | `POST /api/v1/reports/generate` – `generate_report_task` (Celery), `WeasyPrint`, `S3Adapter`. |
| Auditoría | Modelo `AuditLog` (inmutable). |
| Configuración de modelos | Variables `NVIDIA_*` leídas en `settings.py`; utilizadas por adapters vision, chat y embedding. |
| Infraestructura | Docker‑Compose (`docker-compose.yml`), Nginx TLS termination, Redis (broker y cache), PostgreSQL + pgvector, MQTT broker, AWS S3. |
| Observabilidad | Prometheus (`/metrics`), health‑checks (`/health/`), `structlog`. |

---

## Conclusión
Este PRD maestro establece una frontera clara entre lo que **MOLE‑AI entrega hoy**, lo que **se contempla** para próximas iteraciones y lo que **no forma parte** del producto. La separación explícita de deuda técnica, riesgos y consecuencias funcionales permite que los equipos de desarrollo, producto y operaciones prioricen correcciones, mitigaciones y evoluciones de manera trazable y auditable.
