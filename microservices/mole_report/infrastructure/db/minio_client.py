import os
import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class MinioClient:
    """MinIO S3-compatible client for local storage."""

    def __init__(self, endpoint: Optional[str] = None, access_key: Optional[str] = None, secret_key: Optional[str] = None, bucket: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = bucket or os.getenv("MINIO_BUCKET", "mole-ai-storage")
        self._client = httpx.Client(timeout=30.0)

    @classmethod
    def from_env(cls):
        return cls()

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}:{self.secret_key}",
        }

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_sensor_logs(self, days: int = 90, sensors: Optional[List[str]] = None) -> List[dict]:
        """Fetch sensor logs from MinIO storage (if stored there)."""
        # Placeholder: implement MinIO GET logic if needed
        return []

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_ai_diagnostics(self, days: int = 90) -> List[dict]:
        """Fetch AI diagnostics from MinIO storage."""
        return []

    def insert_audit_record(self, table: str, payload: dict) -> Optional[dict]:
        """Insert an audit record (to local DB or MinIO as needed)."""
        return None
