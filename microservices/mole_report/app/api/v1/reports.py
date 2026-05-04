# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Reports API v1 — JWT-protected endpoints.

All endpoints require a valid local JWT (HS256).
User identity is derived from the token and used for ownership checks.
"""
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.config import settings
from infrastructure.redis.job_metadata_store import JobMetadataStore
from infrastructure.workers.tasks import generate_report_task

router = APIRouter()


class GenerateRequest(BaseModel):
    date_range_days: int = 90
    sensors: list[str] = []


def get_job_store() -> JobMetadataStore:
    return JobMetadataStore.from_env()


@router.post("/generate")
def generate_report(
    payload: GenerateRequest,
    current_user: dict = Depends(get_current_user),
    job_store: JobMetadataStore = Depends(get_job_store),
):
    job_id = str(uuid.uuid4())
    hashed_uid = current_user["hashed_user_id"]

    job_store.create_job(job_id)
    # Persist ownership so status/download can verify later
    job_store.update_job(job_id, {"hashed_user_id": hashed_uid})

    # Enqueue celery task — only hashed ID transits through Redis (LFPDPPP)
    generate_report_task.delay(payload.dict(), job_id)
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

    s3_path = data.get("pdf_s3_path")
    if not s3_path:
        raise HTTPException(status_code=500, detail="no pdf path stored")

    # Return directly the static URL
    return {"download_url": f"/static/reports/{job_id}.pdf"}
