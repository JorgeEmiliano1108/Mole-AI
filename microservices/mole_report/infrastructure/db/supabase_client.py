import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings


class SupabaseClient:
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or settings.ms3_supabase_url
        self.key = key or settings.ms3_supabase_key
        self._client = httpx.Client(timeout=30.0)

    @classmethod
    def from_env(cls):
        return cls(settings.ms3_supabase_url, settings.ms3_supabase_key)

    def _headers(self) -> dict:
        return {
            "apikey": self.key or "",
            "Authorization": f"Bearer {self.key or ''}",
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_sensor_logs(self, days: int = 90, sensors: Optional[List[str]] = None) -> List[dict]:
        """
        Fetch sensor_logs rows for the past `days` days. Returns list of dicts with at least
        `timestamp`, `sensor`, `value` fields.
        """
        if not self.url:
            return []
        since = datetime.utcnow() - timedelta(days=days)
        since_iso = since.isoformat() + "Z"
        params = {"select": "timestamp,sensor,value", "timestamp": f"gte.{since_iso}"}
        # supabase expects query string like ?select=...&timestamp=gte.<iso>
        sensors_filter = ""
        if sensors:
            # build IN filter
            sensors_csv = ",".join([f'"{s}"' for s in sensors])
            sensors_filter = f"&sensor=in.({sensors_csv})"
        endpoint = f"{self.url}/rest/v1/sensor_logs?select=timestamp,sensor,value&timestamp=gte.{since_iso}{sensors_filter}"
        resp = self._client.get(endpoint, headers=self._headers())
        if resp.status_code != 200:
            return []
        return resp.json()

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_ai_diagnostics(self, days: int = 90) -> List[dict]:
        if not self.url:
            return []
        since = datetime.utcnow() - timedelta(days=days)
        since_iso = since.isoformat() + "Z"
        endpoint = f"{self.url}/rest/v1/ai_diagnostics?select=timestamp,sensor,anomaly,notes&timestamp=gte.{since_iso}"
        resp = self._client.get(endpoint, headers=self._headers())
        if resp.status_code != 200:
            return []
        return resp.json()

    def insert_audit_record(self, table: str, payload: dict) -> Optional[dict]:
        """Insert an audit record into Supabase REST table `table`.
        Returns the inserted row (if Supabase returns it) or None on failure.
        """
        if not self.url:
            return None
        endpoint = f"{self.url}/rest/v1/{table}"
        headers = self._headers()
        # ask supabase to return representation
        headers["Prefer"] = "return=representation"
        resp = self._client.post(endpoint, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            try:
                j = resp.json()
                if isinstance(j, list) and len(j) > 0:
                    return j[0]
                return j
            except Exception:
                return None
        return None
