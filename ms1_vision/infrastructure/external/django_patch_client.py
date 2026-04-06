import httpx
import asyncio
from typing import Any, Dict, Optional


class DjangoPatchClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def patch_ph_level(self, sensor_id: str, ph_level: float, token: Optional[str] = None) -> None:
        url = f"{self.base_url}/api/v1/sensor-data/{sensor_id}/"
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["X-Hardware-Api-Key"] = self.api_key
        # Only include Authorization if token is truthy
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # try once, retry once on failure
            for attempt in range(2):
                try:
                    resp = await client.patch(url, json={"ph_level": ph_level}, headers=headers)
                    if resp.status_code in (200, 204):
                        return
                except Exception:
                    # on last attempt, give up silently but caller should log
                    if attempt == 1:
                        return
                    await asyncio.sleep(0.5)

    def schedule_patch(self, sensor_id: str, ph_level: float, token: Optional[str] = None) -> None:
        try:
            asyncio.create_task(self.patch_ph_level(sensor_id, ph_level, token=token))
        except RuntimeError:
            # no running loop -- fire-and-forget cannot be scheduled
            # Let caller handle/log this situation
            raise
