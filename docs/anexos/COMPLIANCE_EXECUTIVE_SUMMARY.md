# Resumen Ejecutivo de Cumplimiento (Software‑Only)

**Ámbito de la auditoría**: se evaluó exclusivamente el código fuente, la configuración, la arquitectura, los pipelines de CI/CD, las pruebas y la documentación.  No se consideraron componentes de hardware, cables, fuentes de alimentación ni certificaciones eléctricas.

## Cumplimiento por norma (software)

| Norma | Filas total | Cumple | Parcial | No cumple | % de cumplimiento* |
|-------|------------|--------|---------|----------|--------------------|
| **LFPDPPP** (protección de datos personales) | 14 | 6 | 8 | 0 | **71 %** |
| **MoproSoft** (gestión de configuración, trazabilidad, CI/CD, documentación) | 12 | 0 | 7 | 5 | **29 %** |
| **ISO/IEC 25000** (calidad del producto software) | 18 | 1 | 11 | 6 | **36 %** |

*El porcentaje se calcula como `(Cumple + 0.5 × Parcial) / Filas total`.

## Principales brechas (prioridad **Alta**)

1. **Aviso de privacidad público** – falta una página `/privacy` enlazada desde el banner (LFPDPPP, Backend).
2. **Persistencia del consentimiento en backend** – no hay evidencia de que el consentimiento aceptado se registre en el backend (LFPDPPP, Frontend).
3. **Pipeline CI/CD automatizado** – no existe workflow que garantice lint, pruebas, cobertura y despliegue (MoproSoft, CI/CD).
4. **Circuit‑breaker en llamadas inter‑service** – ausencia de mecanismo de resiliencia (ISO 25000, Micro‑servicios).
5. **TLS interno (mTLS) entre micro‑servicios** – falta de cifrado interno de comunicaciones (ISO 25000, Micro‑servicios).
6. **Escaneo de vulnerabilidades de dependencias (SCA)** – no hay Dependabot ni herramientas de análisis de seguridad (MoproSoft, CI/CD).
7. **Pruebas de migraciones y rollbacks** – la base de datos carece de pruebas que validen cambios de esquema (ISO 25000, Base de datos).
8. **Política formal de retención de datos personales** – existe una restricción en la documentación pero no está formalizada ni automatizada (LFPDPPP, Documentación).

## Recomendaciones de refactorización (por área)

- **Backend**: crear `/privacy`, validar `data_consent` en registro, habilitar cifrado S3, definir política de retención y job Celery de purga, establecer proceso Gitflow y usar issues.
- **Frontend**: enlazar banner a la API de consentimiento, mejorar accesibilidad (ARIA, contraste) y habilitar gzip en NGINX.
- **Micro‑servicios**: integrar circuit‑breaker (`pybreaker`), usar mTLS entre servicios, bloquear versiones de dependencias y versionar imágenes Docker.
- **Base de datos**: crear índices críticos, añadir pruebas de migración, aplicar cifrado en reposo y automatizar retención.
- **Infra‑software**: hardening de Dockerfiles (usuario non‑root), gestionar secretos con Vault, habilitar HSTS y excluir query strings del log.
- **CI/CD & pruebas**: implementar workflow completo, activar lint/pyright, cobertura >= 80 %, SCA con Dependabot/Snyk, pruebas de carga (Locust) y UI (Cypress).
- **Documentación & políticas**: añadir sección LFPDPPP a la arquitectura, redactar política de retención, crear manual de usuario, iniciar CHANGELOG y completar ADRs.

Con esta hoja de ruta el proyecto avanzará hacia el cumplimiento pleno de **LFPDPPP**, **MoproSoft** e **ISO/IEC 25000**, garantizando calidad, seguridad y trazabilidad en todo el software.
