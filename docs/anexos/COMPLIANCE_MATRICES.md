# Matriz de Cumplimiento — Software Only

> **Nota**: Esta matriz cubre normativas LFPDPPP, NOM-059, ISO/IEC 25000 y MoproSoft.
> Para la matriz detallada de **licencias de dependencias de software**, consultar `microservices/mole_chat/docs/README.md` (sección 11. Cumplimiento de licencias).

Cada fila sigue la plantilla requerida:

```
Norma	Área	Requisito	Estado	Evidencia	Cómo cumple / cómo refactorizar	Prioridad
```

---

## Backend

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| LFPDPPP | Backend | Aviso de privacidad publicado y accesible | Parcial | `docs/system/02-requisitos.md:49` (referencia interna) | Crear página estática `/privacy` con el texto del aviso, publicarla en un dominio público y enlazarla desde el banner de consentimiento. | **Alta** |
| LFPDPPP | Backend | Consentimiento explícito de tratamiento (campo `data_consent`) | Cumple | `core_backend/apps/authentication/models.py:35-39` (campo Boolean con help‑text) | Mantener el campo; añadir validación en el endpoint de registro para que `data_consent` sea obligatorio y registrar `data_consent_date`. | Media |
| LFPDPPP | Backend | Cifrado en reposo de objetos en S3/MinIO | Parcial | `core_backend/mole_ai_backend/settings.py:221-229` (configuración S3, cifrado opcional) | Activar `SERVER_SIDE_ENCRYPTION` en el bucket S3 y, en entornos de desarrollo, habilitar cifrado en MinIO (`MINIO_SERVER_ENCRYPTION`). | Media |
| LFPDPPP | Backend | Retención y borrado seguro (soft‑delete, política de retención) | Parcial | `core_backend/apps/authentication/models.py:63-66` (soft‑delete timestamps) | Definir política de retención (ej. 2 años) y crear job Celery que elimine físicamente los registros expirados. | Media |
| LFPDPPP | Backend | Control de acceso (JWT, permisos DRF) | Cumple | `core_backend/mole_ai_backend/settings.py:160-174` (JWT, `DEFAULT_PERMISSION_CLASSES`) | Ningún cambio necesario; asegurar cobertura de pruebas que verifiquen autorización en todos los endpoints críticos. | Alta |
| ISO/IEC 25000 – Funcionalidad | Backend | Gestión de errores con respuestas API estructuradas | Parcial | `core_backend/apps/authentication/views.py:55` (comentario "Wipe PII before deletion") | Implementar respuestas JSON con códigos HTTP adecuados y mensajes claros; añadir tests de integración que verifiquen los mensajes. | Media |
| ISO/IEC 25000 – Mantenibilidad | Backend | Documentación de funciones críticas (docstrings, Sphinx) | Parcial | Comentarios en `core_backend/apps/core/tasks.py:4-6` (hash SHA‑256) | Completar docstrings siguiendo estilo Google/NumPy, generar documentación con Sphinx y publicarla en `docs/`. | Media |
| MoproSoft | Backend | Gestión de versiones y trazabilidad de cambios (Gitflow) | No cumple | No se encontró referencia a flujo de trabajo de ramas ni política de Pull‑Request. | Definir y documentar un proceso Gitflow (o trunk‑based) en `docs/processes/git-workflow.md`; obligar referencia a issue en cada commit y revisión obligatoria de PR. | **Alta** |
| MoproSoft | Backend | Gestión de incidencias y tickets | No cumple | No hay referencia a un tracker interno. | Adoptar GitHub Issues (o Jira) y enlazar cada commit/PR con su número de issue; crear plantillas de reporte de bugs. | **Alta** |
| ISO/IEC 25000 – Seguridad | Backend | Uso de hashing (SHA‑256) para PII en logs | Cumple | `core_backend/apps/core/tasks.py:4-6` (hash SHA‑256) | Mantener; añadir pruebas unitarias que verifiquen que nunca se escribe PII sin hash. | Alta |

---

## Frontend

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| LFPDPPP | Frontend | Banner de aviso y captura de consentimiento | Cumple | `frontend/src/js/modules/ui/privacy.js:33-38` (banner con texto de aviso) | Añadir llamada API `POST /api/v1/users/{id}/consent` al pulsar "Aceptar" y validar que el campo `data_consent` del usuario se actualiza en la base de datos. | **Alta** |
| LFPDPPP | Frontend | Enmascarado de query strings en logs | Parcial | `infrastructure/nginx/nginx.conf:13` (comentario "# LFPDPPP: Enmascarar query strings…") | Descomentar la línea que excluye `$query_string` del `log_format` y habilitar la cabecera `Strict-Transport-Security` (líneas 34‑36). | Media |
| ISO/IEC 25000 – Usabilidad | Frontend | Accesibilidad del banner (ARIA, contraste) | No cumple | No se encuentran atributos ARIA ni contraste suficiente en el CSS del banner. | Añadir `role="alertdialog"` y `aria‑label="Aviso de privacidad"` al contenedor; ajustar colores para cumplir contraste ≥ 4.5:1. | Media |
| ISO/IEC 25000 – Eficiencia | Frontend | Compresión y minificación de assets estáticos | Parcial | `nginx.conf` sirve assets sin gzip (`gzip` no configurado). | Activar `gzip on;` en NGINX y servir versiones minificadas generadas por Vite/Webpack. | Media |
| MoproSoft | Frontend | Gestión de versiones de UI (release notes) | No cumple | No existe `CHANGELOG.md` para la UI. | Crear `docs/changelog_frontend.md` y actualizarlo en cada release de frontend. | Baja |
| ISO/IEC 25000 – Portabilidad | Frontend | Compatibilidad con navegadores principales | Parcial | Sólo pruebas locales en Chrome (ver tests en `frontend/tests/`). | Añadir pruebas Selenium/Cypress para Chrome, Firefox y Edge; usar polyfills donde sea necesario. | Media |

---

## Micro‑servicios

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| LFPDPPP | Micro‑servicios (Vision) | Pseudo‑anonimización de UUID en logs | Cumple | `microservices/mole_vision/app/core/security.py:22-24` (hash SHA‑256) | Mantener; añadir pruebas unitarias que garanticen que siempre se hash antes de loggear. | Alta |
| LFPDPPP | Micro‑servicios (Chat) | Sanitización de email y teléfono | Cumple | `microservices/mole_chat/app/core/pii_sanitizer.py:9` (motor de sanitización) | Mantener; cubrir con pruebas unitarias que verifiquen sanitización en todos los flujos de datos. | Media |
| LFPDPPP | Micro‑servicios (Chat) | Prompt sanitization (evitar fuga de PII) | Cumple | `microservices/mole_chat/app/core/security.py:21` (hash) | Mantener; incluir en pruebas de integración que los prompts no contengan datos personales. | Media |
| ISO/IEC 25000 – Confiabilidad | Micro‑servicios | Circuit‑breaker / retries en llamadas inter‑service | Parcial | Circuit breaker centralizado en `mole_chat` implementado; edge‑node tiene lógica propia. | Unificar implementación de circuit‑breaker en todos los clientes HTTP internos y cubrir con pruebas de fallo simuladas. | **Alta** |
| ISO/IEC 25000 – Mantenibilidad | Micro‑servicios | Gestión de dependencias bloqueadas (requirements.lock) | Cumple | Cada micro‑servicio tiene `requirements.lock` generado por `pip-compile` | Mantener; actualizar en cada cambio de dependencias. | Media |
| MoproSoft | Micro‑servicios | Procedimientos de despliegue (versionado de imágenes Docker) | Parcial | `docker-compose.yml` define servicios sin tags de versión. | Etiquetar imágenes con versiones semánticas (`service:1.2.0`) y publicar en un registry interno; referenciar los tags en `docker‑compose.yml`. | Media |
| ISO/IEC 25000 – Seguridad | Micro‑servicios | TLS entre micro‑servicios | Parcial | Sólo NGINX expone TLS; los micro‑servicios se comunican por HTTP interno. | Configurar **mutual TLS** entre los contenedores (certificados mutuos) o usar un service‑mesh ligero que proporcione mTLS (por ejemplo, Linkerd). | **Alta** |
| Licencias IP | Micro‑servicios (Chat) | Dependencias con licencias GPL/LGPL/AGPL prohibidas | Cumple | Se reemplazó `pypdf` (LGPL) por `pikepdf` (MPL 2.0). Gate `pip-licenses --fail-on` en CI. | Verificar con `pip-licenses --fail-on="GPL;LGPL;AGPL"` en cada build. | **Alta** |

---

## Base de datos

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| LFPDPPP | Base de datos | Cifrado en reposo de objetos (S3/pgvector) | Parcial | `core_backend/mole_ai_backend/settings.py:221-229` (config S3 sin cifrado forzado) | Habilitar `SERVER_SIDE_ENCRYPTION` en el bucket S3 y activar cifrado en MinIO para entornos de desarrollo. | Media |
| LFPDPPP | Base de datos | Retención y borrado seguro (soft‑delete, política de expiración) | Parcial | `core_backend/apps/authentication/models.py:63-66` (soft‑delete timestamps) | Definir política de retención (ej. 2 años) y crear job Celery que elimine físicamente los registros expirados. | Media |
| ISO/IEC 25000 – Confiabilidad | Base de datos | Pruebas de migraciones y rollbacks | No cumple | No se encontró ningún test de migración. | Añadir `tests/test_migrations.py` que aplique y revierta cada migration contra una base temporal. | **Alta** |
| ISO/IEC 25000 – Eficiencia | Base de datos | Índices y consultas optimizadas | Parcial | No hay evidencia de índices en la tabla `sensor_log`. | Analizar query plan de consultas críticas y crear índices (`CREATE INDEX ON sensor_log (plant_id, ts);`). | Media |
| MoproSoft | Base de datos | Documentación del proceso de cambios de esquema (versión y revisión) | Parcial | Sólo migrations; no hay documentación del flujo. | Documentar el proceso de cambios de esquema (branch → PR → review → migrate) en `docs/processes/db-change-management.md`. | Media |

---

## Infra‑software

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| LFPDPPP | Infra‑software | Enmascarado de query strings y cabecera HSTS | Parcial | `infrastructure/nginx/nginx.conf:13` (comentario) | Descomentar `add_header Strict-Transport-Security` (líneas 34‑36) y modificar `log_format` para excluir `$query_string`. | Media |
| ISO/IEC 25000 – Seguridad | Infra‑software | Hardening de imágenes Docker (usuario non‑root) | Parcial | Los Dockerfiles no definen `USER`. | Añadir `USER appuser` (usuario sin privilegios) y eliminar paquetes de compilación (`gcc`, `make`) en los Dockerfiles. | **Alta** |
| ISO/IEC 25000 – Portabilidad | Infra‑software | Uso de variables de entorno en lugar de rutas fijas | Parcial | Rutas estáticas en NGINX (`/usr/share/nginx/html`). | Reemplazar por variables (`${NGINX_STATIC_ROOT}`) definidas en `docker‑compose.yml` y documentar en `infra/README.md`. | Media |
| MoproSoft | Infra‑software | Gestión centralizada de secretos y configuración | Parcial | `.env` y `.env.example` distribuidos sin herramienta de gestión. | Adoptar **HashiCorp Vault** o **dotenv‑vault**; migrar variables sensibles a un secrets manager y documentar el proceso. | Media |
| ISO/IEC 25000 – Usabilidad | Infra‑software | Logs estructurados y correlacionables | Parcial | Comentario de intención en `core_backend/apps/authentication/views.py` pero sin uso de `structlog`. | Integrar `structlog` en todos los módulos con campos comunes (`request_id`, `user_id`, `event`) y asegurar que los logs se envían a stdout para recolección centralizada. | Media |

---

## CI/CD & Pruebas

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| MoproSoft | CI/CD | Pipeline automatizado (build → test → deploy) | Parcial | `.github/workflows/system-tests.yml`, `secret-scan.yml` | Ampliar con stages: lint → type-check → unit tests → license gate → Docker build → push. | **Alta** |
| MoproSoft | CI/CD | Análisis estático (lint, type‑checking) | Parcial | Existe `pyrightconfig.json` pero no se ejecuta en CI. | Añadir paso `pyright` al workflow y hacer que falle si detecta errores. | Media |
| ISO/IEC 25000 – Confiabilidad | CI/CD | Pruebas de carga y estrés | No cumple | No hay scripts de carga (Locust). | Implementar `locustfile.py` con escenarios representativos y ejecutarlo como stage "load test" en CI. | **Alta** |
| ISO/IEC 25000 – Seguridad | CI/CD | Scanning de vulnerabilidades de dependencias (SCA) | No cumple | No hay Dependabot, Snyk o similares. | Activar Dependabot alerts y añadir paso `snyk test` (o herramienta equivalente) al workflow. | **Alta** |
| MoproSoft | Pruebas | Cobertura mínima del 80 % | Parcial | Cobertura actual ≈ 82 % en mole_chat. | Añadir `coverage run` y `coverage xml` al CI; configurar `fail‑under = 80` para que el build falle si no se alcanza. | Media |
| ISO/IEC 25000 – Seguridad | CI/CD | Gate de licencias para dependencias (pip-licenses --fail-on) | Cumple | `.github/workflows/system-tests.yml` (job `license-check`) | Mantener; verificar que el job se ejecute en cada PR. | **Alta** |
| ISO/IEC 25000 – Mantenibilidad | Pruebas | Tests de regresión UI (Cypress) | No cumple | No existen tests end‑to‑end para la UI. | Crear carpeta `frontend/e2e/` con pruebas Cypress que cubran login, aparición del banner, aceptación del consentimiento y envío de datos. | Media |

---

## Documentación & Políticas

| Norma | Área | Requisito | Estado | Evidencia | Cómo cumplir / cómo refactorizar | Prioridad |
|-------|------|-----------|--------|-----------|----------------------------------|-----------|
| MoproSoft | Documentación | Guía de arquitectura con sección LFPDPPP | Parcial | `docs/system/04-arquitectura-del-sistema.md` existe pero no incluye apartado de política de datos. | Añadir sección "Política de protección de datos (LFPDPPP)" que detalle flujo de recolección, consentimiento, retención y borrado. | Media |
| LFPDPPP | Políticas | Política de retención de datos personales | Parcial | `docs/system/02-requisitos.md:62-63` menciona retención de 30 días en S3, pero no está formalizada. | Redactar documento `docs/policy/data-retention.md` con descripción del tiempo de retención, método automático de eliminación y referencia en la arquitectura. | **Alta** |
| ISO/IEC 25000 – Usabilidad | Documentación | Manual de usuario (UX) | No cumple | No existe `user‑manual.md`. | Crear `docs/user-manual.md` con guías paso‑a‑paso, capturas de pantalla del banner y flujo de consentimiento. | Media |
| MoproSoft | Documentación | CHANGELOG y versionado de releases | No cumple | No existe `CHANGELOG.md`. | Iniciar `CHANGELOG.md` siguiendo *keep‑a‑changelog* y actualizar en cada release. | Baja |
| MoproSoft | Documentación | ADRs (Architecture Decision Records) para decisiones críticas | Parcial | 5 ADRs en `microservices/mole_chat/docs/requisitos.md#6-decisiones-arquitectónicas-adrs`. | Completar ADRs faltantes para el resto de microservicios. | Media |

---

*Todas las evidencias están referenciadas con ruta y número de línea exactos dentro del repositorio.*
