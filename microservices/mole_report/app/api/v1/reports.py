# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Reports API v1 — JWT-protected endpoints.

All endpoints require a valid local JWT (HS256).
User identity is derived from the token and used for ownership checks.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.config import settings
from domain.schemas import ReportRequest
from infrastructure.redis.job_metadata_store import JobMetadataStore
from infrastructure.workers.tasks import generate_report_task

router = APIRouter()


def get_job_store() -> JobMetadataStore:
    return JobMetadataStore.from_env()


@router.post("/generate")
def generate_report(
    payload: ReportRequest,
    current_user: dict = Depends(get_current_user),
    job_store: JobMetadataStore = Depends(get_job_store),
):
    job_id = str(uuid.uuid4())
    hashed_uid = current_user["hashed_user_id"]
    job_store.create_job(job_id)
    job_store.update_job(job_id, {"hashed_user_id": hashed_uid})
    generate_report_task.delay(payload.model_dump(), job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}/status")
def get_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_store: JobMetadataStore = Depends(get_job_store),
):
    data = job_store.get_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="job not found")

    # Ownership check: only the user who created the job can view its status
    if data.get("hashed_user_id") and data["hashed_user_id"] != current_user["hashed_user_id"]:
        raise HTTPException(status_code=403, detail="access denied")

    return data


@router.get("/{job_id}/download")
def download_report(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_store: JobMetadataStore = Depends(get_job_store),
):
    data = job_store.get_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="job not found")

    # Ownership check
    if data.get("hashed_user_id") and data["hashed_user_id"] != current_user["hashed_user_id"]:
        raise HTTPException(status_code=403, detail="access denied")

    if data.get("status") != "SUCCESS":
        raise HTTPException(status_code=400, detail="report not ready")

    # Presigned URL stored by the Celery task (24h TTL)
    presigned_url = data.get("result")
    if presigned_url and presigned_url.startswith("http"):
        return {"download_url": presigned_url}

    # Fallback: regenerate presigned URL from s3_path if result was not set
    s3_path = data.get("pdf_s3_path")
    if not s3_path:
        raise HTTPException(status_code=500, detail="no pdf path stored")

    from infrastructure.storage.s3_adapter import S3Adapter
    s3 = S3Adapter.from_env()
    presigned_url = s3.generate_presigned_url(s3_path, expires_in=3600)
    return {"download_url": presigned_url}
