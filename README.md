# Mole.AI

Mole.AI is an enterprise-grade greenhouse monitoring and AI inference platform combining a Django gateway with specialized microservices for vision, RAG/CAG chat, and reporting. Designed for secure local and cloud deployments using Docker Compose.

Architecture
- Django Gateway (HTTP, authentication, ingest)
- MS1 Vision (image inference, CNN/TFLite)
- MS2 RAG/CAG (retrieval-augmented conversation service)
- MS3 Reports (Celery workers, storage to S3/MinIO)

Technologies
- Python 3.11+, Django, FastAPI
- Docker & docker-compose
- PostgreSQL (pgvector), Redis
- MinIO (S3-compatible) for object storage
- HuggingFace / OpenAI for LLMs (configurable)

Quickstart (local, development)
1. Copy the example env and fill values (DO NOT commit `.env`):

```bash
cp .env.example .env
# Edit .env with secure values (SECRET_KEY, DB passwords, API keys, etc.)
``` 

2. Build and start services (development):

```bash
docker-compose up --build
```

Notes & Security
- Never commit `.env`. This repo contains `.env.example` as a template only.
- Rotate any credentials that were previously exposed in version control.
- For production, use a secrets manager (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) and avoid storing secrets in environment files.

Repository Prep
- `.env.example`: template for required env vars.
- `.gitignore`: excludes `.env`, local DB files, caches, docker runtime data, and logs.

Support
Open an issue or contact the internal DevOps team for onboarding and secrets rotation.

Changelog
- 2026-07-06: Fixed `settings.HOST`/`settings.PORT` → `settings.ms3_host`/`settings.ms3_port` in mole_report (AttributeError at startup). Removed 11 unused environment variables from `.env`. See `microservices/mole_report/docs/README.md` §14 for details.
# Mole-AI
Plants Monitoring and Assistance System
