# MS-3 Reports Service (scaffold)

This folder contains the scaffold for MS-3: an asynchronous report generator (FastAPI + Celery + Redis) that produces PDFs with WeasyPrint and charts with Matplotlib.

Quick start (development):

```bash
docker-compose -f docker-compose.ms3.yml up --build
```

Endpoints:
- `POST /api/v1/reports/generate` -> enqueue report generation
- `GET /api/v1/reports/{job_id}/status` -> check progress
- `GET /api/v1/reports/{job_id}/download` -> get presigned download URL
