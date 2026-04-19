import os
import json
import redis
from typing import Optional


class JobMetadataStore:
    def __init__(self, client: redis.Redis):
        self._r = client

    @classmethod
    def from_env(cls):
        url = os.getenv("MS3_REDIS_URL") or "redis://redis:6379"
        r = redis.from_url(url, decode_responses=True)
        return cls(r)

    def _key(self, job_id: str) -> str:
        return f"jobs:{job_id}"

    def create_job(self, job_id: str):
        data = {"status": "QUEUED", "progress": 0}
        self._r.hset(self._key(job_id), mapping=data)

    def update_status(self, job_id: str, status: str):
        self._r.hset(self._key(job_id), mapping={"status": status})

    def set_progress(self, job_id: str, progress: int):
        self._r.hset(self._key(job_id), mapping={"progress": int(progress)})

    def set_result(self, job_id: str, s3_path: str):
        self._r.hset(self._key(job_id), mapping={"pdf_s3_path": s3_path})

    def set_error(self, job_id: str, msg: str):
        self._r.hset(self._key(job_id), mapping={"error_message": msg})

    def get_job(self, job_id: str) -> Optional[dict]:
        data = self._r.hgetall(self._key(job_id))
        if not data:
            return None
        # convert numeric
        if "progress" in data:
            try:
                data["progress"] = int(data["progress"])
            except Exception:
                data["progress"] = 0
        return data
