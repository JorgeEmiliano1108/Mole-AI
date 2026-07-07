# Visión y fundamentos del sistema

## Propósito
El sistema **MOLE‑AI** provee una plataforma integral de asistencia agronómica basada en inteligencia artificial, diseñada para facilitar la gestión de cultivos mediante la captura de datos de sensores IoT, la generación de respuestas automáticas a consultas de los agricultores y el análisis visual de plantas.  La solución permite a los usuarios obtener información científica, diagnósticos de salud vegetal y reportes de desempeño de sus parcelas de forma segura, escalable y auditada.

## Contexto del proyecto
La agricultura de precisión demanda la convergencia de tecnologías emergentes –Internet de las Cosas (IoT), modelos de lenguaje grande (LLM) y análisis de visión por computadora– para reducir la brecha entre la información disponible y la toma de decisiones en campo.  MOLE‑AI se inserta en este contexto como un sub‑sistema de gestión de datos de sensores, generación de conocimiento (RAG) y servicio de visión que se integra con infraestructuras de nube pública (AWS) y canales de comunicación de bajo consumo (MQTT).

## Problema que resuelve
Los agricultores carecen de herramientas accesibles que:
- Integren de forma automática lecturas de sensores distribuidos.
- Proporcionen respuestas basadas en evidencia científica sin requerir expertise en IA.
- Detecten visualmente plagas o deficiencias nutricionales mediante imágenes capturadas en campo.
- Generen reportes consolidados y auditables de manera periódica.
MOLE‑AI aborda estas carencias mediante un ecosistema de micro‑servicios que procesan, almacenan y exponen la información bajo estrictas normas de seguridad y trazabilidad.

## Justificación técnica
- **Escalabilidad:** La arquitectura basada en micro‑servicios permite dimensionar individualmente los componentes de visión, chat y generación de informes.
- **Rendimiento:** La búsqueda semántica se implementa con **pgvector**, ofreciendo consultas vectoriales en tiempo sub‑segundo.
- **Cumplimiento normativo:** Se incluyen filtros automáticos de la normativa **NOM‑059‑SEMARNAT**, gestión de consentimientos bajo la Ley Federal de Protección de Datos (LFPDPPP) y auditoría inmutable.
- **Resiliencia:** Los procesos pesados (generación de embeddings, inferencia de visión) se ejecutan en workers Celery, aislando fallos del flujo de petición‑respuesta.

## Objetivo general
Desarrollar y mantener una plataforma de asistencia agronómica basada en IA que brinde a los usuarios finales respuestas precisas, diagnósticos visuales y reportes de cultivo, garantizando la seguridad, la trazabilidad y la disponibilidad del sistema.

## Objetivos específicos
1. **Captura y almacenamiento de datos IoT** mediante dispositivos ESP32 que envían telemetría a través de MQTT y HTTP.
2. **Implementar RAG (Retrieval‑Augmented Generation)** para combinar conocimientos botánicos estructurados con documentos PDF cargados por los usuarios.
3. **Proveer un motor de visión** basado en **NVIDIA LLM (Llama 3.2‑vision‑instruct)** que genere diagnósticos estructurados a partir de imágenes de plantas.
4. **Garantizar autenticación y autorización** mediante JWT firmado con claves secretas y control de acceso basado en roles.
5. **Ofrecer generación automática de reportes** en PDF, almacenados en **AWS S3**, con seguimiento de tareas mediante Celery.
6. **Implementar observabilidad completa** (metrics, logs y health‑checks) y mecanismos de recuperación ante fallos.

## Alcance
- **Cobertura funcional:** gestión de usuarios, plantas, especies, telemetría, chat IA, visión, ingestión de documentos, generación de reportes y auditoría.
- **Exclusiones:** desarrollo de frontend móvil nativo (se contempla como evolución futura) y entrenamiento de modelos desde cero (se consumen modelos pre‑entrenados de NVIDIA). 

## Limitaciones
- La inferencia de visión depende exclusivamente del endpoint de NVIDIA NIM; no se soportan modelos alternativos (p. ej. ONNX, TFLite).
- El almacenamiento de objetos está limitado a **AWS S3**; MinIO se mantiene solo como referencia histórica.
- La disponibilidad de datos está sujeta a la latencia de los servicios externos de NVIDIA y de AWS.

## Stakeholders
| Stakeholder | Interés | Responsabilidad |
|-------------|---------|-----------------|
| Agricultor / Usuario final | Obtención de diagnósticos y recomendaciones agronómicas. | Interactuar con la UI/API, subir imágenes y documentos. |
| Administrador del sistema | Operación, configuración y mantenimiento de la plataforma. | Gestionar usuarios, modelos, infraestructura y supervisar la auditoría. |
| Equipo de desarrollo | Evolución y mejora continua del software. | Implementar nuevas funcionalidades, pruebas y documentación. |
| Proveedor de IA (NVIDIA) | Suministro de modelos LLM y visión. | Proveer endpoints de inferencia y embeddings. |
| Operador de Infraestructura (AWS) | Provisión de servicios de cómputo, bases de datos y S3. | Administrar recursos de cómputo, seguridad y escalado. |

## Fundamentos teóricos aplicados al sistema
### Arquitectura cliente‑servidor
El modelo clásico de cliente‑servidor se materializa mediante un **frontend** (actualmente una SPA estática) que consume APIs REST expuestas por los micro‑servicios.  La separación de preocupaciones permite que los clientes sean agnósticos del lenguaje de implementación del servidor.

### Microservicios
Cada dominio funcional (visón, chat/RAG, generación de reportes) está encapsulado en un contenedor Docker independiente, facilitando despliegues independientes, escalado selectivo y aislamiento de fallos.

### IoT y adquisición de datos
Los dispositivos ESP32 envían telemetría mediante **MQTT** (puerto 8883 TLS) y mediante HTTP a los endpoints de ingestión.  Los datos se normalizan en el backend y se persisten en PostgreSQL.

### APIs REST
Se utilizan **FastAPI** y **Django REST Framework** para describir contratos de servicio claros (método, ruta, payload, códigos).  Los endpoints están versionados bajo el prefijo `/api/v1/`.

### Bases de datos relacionales
**PostgreSQL** almacena los datos transaccionales (usuarios, plantas, sensores).  Se complementa con **pgvector** para almacenar embeddings de texto y habilitar búsquedas semánticas eficientes.

### pgvector y búsqueda semántica
Los vectores de 1536 dimensiones generados con el modelo **nvidia/nv-embedqa-e5-v5** se insertan en la tabla `botanical_knowledge`.  Consultas por similitud utilizan índices GIN para garantizar tiempos de respuesta sub‑segundo.

### RAG y CAG
El flujo de **Retrieval‑Augmented Generation (RAG)** combina los embeddings almacenados con prompts estáticos para producir respuestas contextualizadas.  El **Context‑Augmented Generation (CAG)** se implementa en el motor de chat, añadiendo información de sensores y documentos relevantes al prompt del LLM.

### JWT y control de acceso
Los tokens JWT firmados con `JWT_SECRET_KEY` incluyen claims de `sub`, `username`, `email` y `role`.  El middleware verifica la validez, la expiración y la audiencia (`authenticated`).  Los permisos se implementan mediante `IsAuthenticated`, `IsSuperuserOrReadOnly` y `HardwareOnlyPermission`.

### Observabilidad y resiliencia
Se despliegan **Prometheus** y **structlog** para métricas, trazas y logs estructurados.  Los health‑checks (`/health/`) permiten la detección automática de fallos por parte del orquestador.  Los procesos intensivos (embeddings, visión) se ejecutan en **Celery workers**, garantizando que la capa HTTP permanezca responsiva.

### Frontend multiplataforma (evolución futura)
Aunque el repositorio actual contiene una SPA estática basada en HTML/JS, el diseño está pensado para soportar una **aplicación multiplataforma** (Web, móvil) mediante consumo de los mismos endpoints REST, favoreciendo la reutilización del backend sin acoplamientos a tecnologías de presentación específicas.
