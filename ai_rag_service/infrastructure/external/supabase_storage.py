"""
Supabase Storage Adapter — generates signed upload URLs.

The client (mobile/web) uploads the image directly to Supabase Storage
using the signed URL.  The backend never touches image bytes, saving
bandwidth and memory.
"""
import os
import uuid
import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_S3_BUCKET = os.getenv("SUPABASE_S3_BUCKET", "plant-images")
# Service-role key is needed for Storage Admin operations (signed URLs)
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


class SupabaseStorageError(Exception):
    pass


class SupabaseStorageAdapter:
    """Generates pre-signed URLs for Supabase Storage uploads."""

    def __init__(
        self,
        base_url: str = SUPABASE_URL,
        bucket: str = SUPABASE_S3_BUCKET,
        service_role_key: str = SUPABASE_SERVICE_ROLE_KEY,
        http_client: httpx.AsyncClient | None = None,
    ):
        # Supabase REST URL is the project URL, not the DB host
        self.base_url = base_url.rstrip("/")
        self.bucket = bucket
        self.service_role_key = service_role_key
        self._http = http_client

    async def generate_signed_upload_url(
        self,
        file_name: str,
        content_type: str = "image/jpeg",
        expires_in: int = 3600,
    ) -> dict:
        """Return a signed upload URL and the resulting storage path.

        If the Supabase service-role key is unavailable (local dev),
        returns a deterministic placeholder URL so the rest of the
        pipeline can still be exercised.
        """
        # Build a unique storage path: diagnostics/<date>/<uuid>_<file_name>
        today = datetime.utcnow().strftime("%Y-%m-%d")
        unique_name = f"{uuid.uuid4().hex[:12]}_{file_name}"
        storage_path = f"diagnostics/{today}/{unique_name}"

        if not self.service_role_key:
            logger.warning(
                "SUPABASE_SERVICE_ROLE_KEY not set — returning placeholder upload URL"
            )
            return {
                "upload_url": f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}",
                "storage_path": storage_path,
                "expires_in": expires_in,
            }

        url = (
            f"{self.base_url}/storage/v1/object/upload/sign"
            f"/{self.bucket}/{storage_path}"
        )
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "apikey": self.service_role_key,
        }

        if self._http is not None:
            resp = await self._http.post(url, headers=headers, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers)

        if resp.status_code not in (200, 201):
            raise SupabaseStorageError(
                f"Signed URL generation failed ({resp.status_code}): {resp.text}"
            )

        data = resp.json()
        signed_url = data.get("url") or data.get("signedURL", "")
        if not signed_url.startswith("http"):
            signed_url = f"{self.base_url}{signed_url}"

        return {
            "upload_url": signed_url,
            "storage_path": storage_path,
            "expires_in": expires_in,
        }
