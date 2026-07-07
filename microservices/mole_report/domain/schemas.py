from pydantic import BaseModel
from typing import Optional


class ReportRequest(BaseModel):
    date_range_days: int = 90
    sensors: list[str] = []


class ReportJob(BaseModel):
    job_id: str
    hashed_user_id: str
    status: str = "QUEUED"
    progress: int = 0
    result: Optional[str] = None
    pdf_s3_path: Optional[str] = None
    error: Optional[str] = None


class ReportResult(BaseModel):
    download_url: str
