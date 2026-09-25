# Issue 15: Pinear dependencias + .env.example completo

Status: ready-for-agent
Sev: P2 · Área: backend+infra · Fase: D

## Evidencia
- `requirements.txt` con `>=` en celery, redis, boto3, Pillow, argon2-cffi,
  django-axes, tenacity, bleach, pydantic, langsmith, locust, dj-database-url,
  paho-mqtt, sentry-sdk (solo Django/gunicorn con `~=`).
- `.env.example` sin `FRONTEND_BASE_URL`, `DATABASE_URL`, `MINIO_*`, `NVIDIA_*`
  (usa `OBJECT_STORAGE_*`/`LLM_BASE_URL` con otros nombres); `DB_URL` vacío `:36`.

## Problema
Builds irreproducibles; ejemplo de entorno a la deriva del canon `DB_*`.

## Aceptación
- `pip freeze`-compatible: pines `==` (o `pip-compile`) + CI que verifique deriva.
- `.env.example` cubre toda var leída (`grep -rho getenv/getenv_first` como oracle),
  con el canon `DB_*` y alias legacy marcados.

## Compliance
Reproducibilidad; secreto fuera del repo (`.env` jamás commiteado).

## Comments
(none)
