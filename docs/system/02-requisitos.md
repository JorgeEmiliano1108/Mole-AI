# Requisitos del sistema

## Propósito
Definir de forma verificable los requisitos funcionales y no funcionales que deben cumplir los componentes de MOLE‑AI para cumplir su misión de asistencia agronómica basada en IA.

## Alcance de requisitos
El alcance cubre todos los micro‑servicios que forman la plataforma (Django backend, ms1_vision, ms2_chat, ms3_reports, MQTT broker, Redis, PostgreSQL/pgvector y AWS S3) así como los procesos de CI/CD, pruebas y despliegue.

## Supuestos
- Los servicios externos de NVIDIA (NIM) y de AWS están operativos y sus credenciales son válidas.
- Los dispositivos IoT utilizan MQTT sobre TLS (puerto 8883) y disponen de un token de autenticación (`auth_token`).
- Los usuarios finales acceden a través de un cliente web que consume los endpoints REST.
- La zona horaria del sistema es UTC.

## Requisitos funcionales

### Backend y micro‑servicios (RF)

| ID | Nombre | Descripción | Justificación | Prioridad | Actor/Fuente | Método de verificación |
|----|--------|-------------|----------------|-----------|--------------|------------------------|
| RF-01 | Autenticación de usuarios | Permitir a los usuarios registrarse y autenticarse mediante `username`/`password` o `email`/`password`, generando un token JWT firmado con `JWT_SECRET_KEY`. | Fundamento de seguridad y control de acceso. | Alta | Usuario final | Pruebas unitarias (`test_login_dual.py`) y pruebas de integración (`test_chat_e2e.py`). |
| RF-02 | Gestión de roles | Asignar a cada usuario uno de los roles: *superuser*, *admin* (staff), *user* (autenticado) o *hardware* (dispositivo). | Soporta autorización basada en privilegios. | Alta | Sistema (backend) | Validación de claims en JWT y pruebas de autorización (`test_device_ownership_success.py`). |
| RF-03 | Registro y mantenimiento de usuarios | Crear, actualizar (campos permitidos) y eliminar cuentas de usuario, respetando LFPDPPP (anonimización de PII). | Cumplimiento legal. | Alta | Usuario final / Administrador | Tests de `user_profile_view` (DELETE) y auditoría (`AuditLog`). |
| RF-04 | Gestión de plantas y especies | CRUD de `UserPlant`, `SpeciesCatalog` y `FavoritePlant`. Los usuarios pueden crear, actualizar y eliminar sus propias plantas; los administradores pueden gestionar especies globales. | Necesario para contextualizar la telemetría y los diagnósticos. | Alta | Usuario autenticado / Administrador | Tests en `plants/views.py` y cobertura de endpoints (`test_plants`). |
| RF-05 | Ingesta de telemetría IoT | Recepción de datos de sensores vía `POST /api/v1/sensor-data/` y `POST /api/v1/sensor-data/batch/` autenticados mediante token de hardware. Validar anti‑replay (Δ > 300 s) y aplicar throttling (200 req/min por usuario). | Garantiza integridad y seguridad de los datos de campo. | Alta | Dispositivo IoT | Tests `test_sensor_data_patch.py`, `test_sensor_data_batch`. |
| RF-06 | Almacenamiento de documentos PDF | Permitir la carga de PDFs que alimenten la base de conocimiento mediante endpoint `POST /api/v1/knowledge/ingest-pdf`. Los documentos se procesan y sus chunks se indexan en pgvector. | Enriquecer el contexto del RAG. | Media | Usuario autenticado | Pruebas de ingestión (`test_mlops_upload.py`). |
| RF-07 | Búsqueda semántica de conocimiento | Consultar la base de conocimiento mediante vectores de embedding para recuperar los fragmentos más relevantes a una consulta del usuario. | Mejora la precisión de respuestas generadas por el chat. | Media | Chat IA | Tests de RAG (`test_mlops_upload.py`). |
| RF-08 | Chat IA (CAG) | Permitir a los usuarios enviar preguntas al endpoint `POST /api/v1/mole-ai/chat`. El sistema combina el prompt estático, datos de sensores y chunks relevantes antes de invocar la lógica del modelo. | Proveer respuestas agronómicas basadas en datos actuales y conocimiento estructurado. | Alta | Usuario final | Pruebas end‑to‑end (`test_chat_e2e.py`). |
| RF-09 | Visión IA | Analizar imágenes de plantas mediante `POST /api/v1/vision/analyze/`. Utilizar el proceso de visión para generar un diagnóstico estructurado. | Detectar plagas, deficiencias y estado de salud. | Alta | Usuario final | Tests en `test_vision_api.py`. |
| RF-10 | Generación de reportes | Generar reportes PDF de sensores bajo demanda (`POST /api/v1/reports/generate`). El trabajo se procesa en un worker Celery y el PDF se almacena en AWS S3, devolviéndose una URL pre‑firmada. | Facilitar la revisión periódica de métricas de cultivo. | Media | Usuario autenticado | Tests `test_api_reports.py` (API, requiere TestClient). |
| RF-11 | Auditoría de acciones críticas | Registrar en tabla `audit_logs` cada operación que modifique datos críticos (creación/eliminación de usuarios, cambios de configuración, etc.). Los logs son inmutables. | Trazabilidad y cumplimiento normativo. | Alta | Sistema | Verificación mediante consultas directas a la tabla y tests `test_audit.py`. |
| RF-12 | Gestión de configuración de modelos | Permitir a los administradores cambiar los valores de las variables de entorno `NVIDIA_VISION_MODEL`, `NVIDIA_CHAT_MODEL`, `NVIDIA_REPORT_MODEL` y `NVIDIA_EMBEDDING_MODEL`. | Fuera de alcance actual – adaptar la plataforma a nuevas versiones de modelos sin redeploy completo. | Media | Administrador | Pendiente de verificación (no hay endpoint implementado). |


### Frontend (RF‑F)
| ID | Nombre | Descripción | Justificación | Prioridad | Actor/Fuente | Método de verificación | Estado funcional | Observación |
|----|--------|-------------|----------------|-----------|--------------|------------------------|------------------|-------------|
| RF‑F‑01 | Interfaz de login | Permite a un usuario introducir credenciales y enviar la solicitud de autenticación al backend, gestionando el token JWT en el almacenamiento local. | Necesario para iniciar sesión y obtener acceso a la aplicación. | Alta | Usuario final | Código en `frontend/src/js/auth.js` (funciones `login`, `setAuthToken`). | Implementado | Sin pruebas E2E |
| RF‑F‑02 | Navegación entre vistas | Provee botones y enlaces que permiten al usuario moverse entre pantallas (login, dashboard, admin) y muestra el tipowriter inicial. | Facilita el flujo de uso del sistema. | Media | Usuario final | Código en `frontend/src/js/index-boot.js` y `frontend/src/js/modules/ui/navigation.js`. | Parcial | Sin pruebas E2E |
| RF‑F‑03 | Chat IA UI | Permite al usuario enviar preguntas al endpoint `/api/v1/mole-ai/chat` y muestra la respuesta en pantalla. | Expone la funcionalidad de Chat IA al usuario. | Alta | Usuario final | Código en `frontend/src/js/modules/services/chat.js`. | Implementado | Sin pruebas E2E |
| RF‑F‑04 | Visión IA UI | Permite al usuario cargar una imagen y enviarla al endpoint `/api/v1/vision/analyze`, mostrando el diagnóstico estructurado. | Da acceso a la funcionalidad de visión al usuario. | Alta | Usuario final | Código en `frontend/src/js/modules/services/vision.js`. | Parcial | Carga de imagen disponible, falta validación completa |
| RF‑F‑05 | Generación y descarga de reportes | Permite al usuario solicitar la generación de un reporte PDF mediante `/api/v1/reports/generate` y descargar el archivo desde la URL pre‑firmada. | Necesario para exportar datos de sensores. | Media | Usuario final | Código en `frontend/src/js/modules/services/reports.js`. | Parcial | Generación disponible, descarga no probada |
| RF‑F‑06 | Envío de telemetría manual | Permite al usuario introducir manualmente lecturas de sensores y enviarlas al endpoint `/api/v1/sensor-data/` o `/api/v1/sensor-data/batch/`. | Soporta la captura de datos cuando el IoT no está disponible. | Media | Usuario final | Código en `frontend/src/js/modules/services/iot.js`. | Parcial | Interfaz presente, sin pruebas automatizadas |

## Requisitos no funcionales
| ID | Nombre | Descripción | Métrica | Prioridad | Método de verificación |
|----|--------|-------------|---------|----------|------------------------|
| RNF-01 | Seguridad de la comunicación | Todas las comunicaciones externas utilizan TLS (HTTPS para APIs, TLS para MQTT). | Encriptación TLS 1.2+ | Alta | Escaneo de puertos (test_ssl) |
| RNF-02 | Autorización basada en JWT | Los tokens deben expirar en `JWT_TTL_MINUTES` (valor por defecto 20 min). | Expiración < 30 min | Alta | Decodificación del token y verificación de `exp`. |
| RNF-03 | Rendimiento de búsqueda semántica | Las consultas de embeddings deben devolver resultados en < 500 ms para 10 k vectores. | Tiempo de respuesta < 500 ms | Media | Pendiente: no existe test de rendimiento. pgvector configurado en producción (`settings.py:79` `INSTALLED_APPS` incluye `pgvector`). |
| RNF-04 | Disponibilidad del servicio | El sistema debe estar operativo ≥ 99.5 % mensual. | Uptime calculado por Prometheus | Alta | Métricas de `up` en Prometheus. |
| RNF-05 | Trazabilidad de cambios | Cada modificación de datos críticos genera un registro en `audit_logs`. | 100 % de operaciones críticas auditadas | Alta | Revisión de tabla `audit_logs`. |
| RNF-06 | Mantenibilidad del código | Cobertura de pruebas unitarias ≥ 80 % y mantenibilidad de código (radón) ≤ 10. | Cobertura y métricas de calidad | Media | Informes de cobertura (`cobertura.xml`). |
| RNF-07 | Escalabilidad horizontal | Cada micro‑servicio debe poder replicarse sin re‑configuración de la lógica de negocio. | Número de réplicas soportado ≤ N (N configurable). | Media | Pruebas de carga con Locust (`locustfile.py`). |
| RNF-08 | Observabilidad completa | Exponer métricas de Prometheus para latencia, tasa de peticiones y contadores de errores. | Métricas disponibles en `/metrics`. | Alta | Consulta a endpoint `/metrics`. |
| RNF-09 | Protección anti‑replay en IoT | Descartar paquetes cuya marca de tiempo difiera más de 300 s del tiempo del servidor. | Δ ≤ 300 s | Alta | Tests de `sensor_data_view`. |
| RNF-10 | Cumplimiento NOM‑059 | Bloquear consultas que contengan palabras clave relacionadas con actividades prohibidas por la normativa. | 100 % de detecciones | Alta | Tests `test_nom059.py`. |

## Restricciones de negocio
- Los usuarios deben consentir explícitamente el tratamiento de sus datos personales (campo `data_consent`).
- Los documentos PDF pueden ser cargados únicamente por usuarios autenticados.
- Los informes generados están sujetos a políticas de retención de 30 días en S3 antes de su eliminación automática.

## Restricciones tecnológicas
- La base de datos es PostgreSQL 13+ con extensión **pgvector** obligatoria.
- Los modelos de IA deben ser accesibles a través de la API de NVIDIA; no se admiten modelos locales.
- El almacenamiento de objetos está confinado a **AWS S3**; MinIO es un componente legado sin uso productivo.
- El código está escrito en Python 3.12 y depende de Django 5, FastAPI y Celery.

## Criterios de aceptación globales
1. Todas las pruebas automatizadas (unitarias, integración y de carga) deben pasar (exit‑code 0).
2. Los endpoints deben responder con los códigos HTTP especificados en los contratos de API.
3. Los logs de auditoría deben registrar cada acción crítica sin posibilidad de borrado.
4. Las métricas de disponibilidad y latencia deben cumplir los valores definidos en los RNF‑04 y RNF‑03.
5. Las variables de entorno `NVIDIA_*` deben poder modificarse y ser efectivas tras reinicio del contenedor correspondiente.

## Matriz de trazabilidad inicial
| Requisito | Caso de uso relacionado | Endpoint | Test automatizado | Estado funcional |
|-----------|------------------------|----------|-------------------|----------------|
| RF-01 | UC‑01 Iniciar sesión | POST /api/v1/auth/login/ | `test_login_dual.py` | Implementado |
| RF-02 | UC‑06 Administrar usuarios | PATCH/DELETE /api/v1/auth/profile/ | `test_user_profile.py` | Implementado |
| RF-03 | UC‑07 Registrar planta | POST /api/v1/user-plants/ | `test_plant_creation.py` | Implementado |
| RF-05 | UC‑08 Enviar telemetría | POST /api/v1/sensor-data/ | `test_sensor_data.patch` | Implementado |
| RF-08 | UC‑09 Consultar agente IA | POST /api/v1/mole-ai/chat | `test_chat_e2e.py` | Implementado |
| RF-09 | UC‑10 Analizar imagen | POST /api/v1/vision/analyze/ | `test_vision_api.py` | Implementado |
| RF-10 | UC‑11 Generar reporte | POST /api/v1/reports/generate | `test_api_reports.py` | Implementado |
| RF-11 | UC‑12 Auditoría | INSERT en audit_logs | `test_audit.py` | Implementado |
| RF-F-01 | UC‑F‑01 Interfaz de login | UI login (frontend) | Pendiente | Implementado |
| RF-F-02 | UC‑F‑02 Navegación entre vistas | UI navegación (frontend) | Pendiente | Parcial |
| RF-F-03 | UC‑F‑03 Chat IA UI | UI chat (frontend) | Pendiente | Implementado |
| RF-F-04 | UC‑F‑04 Visión IA UI | UI visión (frontend) | Pendiente | Parcial |
| RF-F-05 | UC‑F‑05 Generación y descarga de reportes UI | UI reportes (frontend) | Pendiente | Parcial |
| RF‑F‑06 | UC‑F‑06 Envío de telemetría manual UI | UI telemetría (frontend) | Pendiente |
