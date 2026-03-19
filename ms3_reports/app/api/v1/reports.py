from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import uuid
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
def generate_report(payload: GenerateRequest, job_store: JobMetadataStore = Depends(get_job_store)):
    job_id = str(uuid.uuid4())
    job_store.create_job(job_id)
    # enqueue celery task
    generate_report_task.delay(payload.dict(), job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}/status")
def get_status(job_id: str, job_store: JobMetadataStore = Depends(get_job_store)):
    data = job_store.get_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="job not found")
    return data


@router.get("/{job_id}/download")
def download_report(job_id: str, job_store: JobMetadataStore = Depends(get_job_store)):
    data = job_store.get_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="job not found")
    if data.get("status") != "SUCCESS":
        raise HTTPException(status_code=400, detail="report not ready")
    s3_path = data.get("pdf_s3_path")
    if not s3_path:
        raise HTTPException(status_code=500, detail="no pdf path stored")
    # Return a presigned URL
    from infrastructure.storage.s3_adapter import S3Adapter

    s3 = S3Adapter.from_env()
    url = s3.generate_presigned_url(s3_path)
    return {"download_url": url}
