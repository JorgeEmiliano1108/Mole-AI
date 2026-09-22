# Mole.AI

Mole.AI is an enterprise-grade greenhouse monitoring and AI inference platform combining a Django gateway with specialized microservices for vision, RAG/CAG chat, and reporting. Designed for secure local and cloud deployments using Docker Compose.

Architecture
- Django Gateway (HTTP, authentication, ingest)
- MS1 Vision (plant diagnosis via NVIDIA NIM vision models)
- MS2 RAG/CAG (retrieval-augmented conversation service)
- MS3 Reports (Celery workers, storage to S3-compatible object storage)

Technologies
- Python 3.11, Django 4.2 + DRF (gateway), FastAPI (microservices)
- Docker & Docker Compose (compose files live in `infrastructure/`)
- PostgreSQL 16 + pgvector, Redis 7, Mosquitto MQTT (1883 plain legacy / 8883 TLS)
- S3-compatible object storage (MinIO local / AWS S3 via `OBJECT_STORAGE_*`)
- NVIDIA NIM (OpenAI-compatible API) for LLM/vision/embedding models

Quickstart (local, development)
1. Obtain the `.env` file from the secrets manager or a teammate (it is gitignored
   and can NEVER be committed — DO NOT commit `.env`):

```bash
# .env is the single global env file (compose, Django, edge and MS read it).
# Each block inside documents its consumer in code.
# Edit values with secure secrets (SECRET_KEY, DB_PASSWORD, API keys, etc.)
``` 

2. Build and start services (development):

```bash
docker compose --env-file .env -f infrastructure/docker-compose.yml up --build -d
```

3. Run the checks:

```bash
# Backend unit tests (from core_backend/)
pytest apps tests --ignore=tests/integration --ignore=tests/load
# System E2E (needs the e2e stack)
docker compose --env-file .env -f infrastructure/docker-compose.e2e.yml up -d
bash tests/system/test_jwt_auth.sh
```

Notes & Security
- Never commit `.env`. This repo contains `.env.example` as a template only.
- Rotate any credentials that were previously exposed in version control.
- For production, use a secrets manager (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) and avoid storing secrets in environment files.

Repository Prep
- `.env`: single global env file (generic names; each block documents its consumer in code).
- `.gitignore`: excludes `.env`, local DB files, caches, docker runtime data, and logs.

Support
Open an issue or contact the internal DevOps team for onboarding and secrets rotation.

Changelog
- 2026-09-14: Root README quickstart fixed (was: `.env.example` + root `docker-compose.yml`, neither exists). Stack corrected: MS1 is NIM-only (no local CNN/TFLite), LLMs via NVIDIA NIM, compose files under `infrastructure/`.
- 2026-07-06: Fixed `settings.HOST`/`settings.PORT` → `settings.ms3_host`/`settings.ms3_port` in mole_report (AttributeError at startup). Removed 11 unused environment variables from `.env`. See `microservices/mole_report/docs/README.md` §14 for details.
# Mole-AI
Plants Monitoring and Assistance System
