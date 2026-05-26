"""
S3 Downloader — MinIO/AWS S3 asset retrieval for the Vision pipeline.

Downloads training image ZIPs from MinIO for CNN fine-tuning.
Supports both in-memory download (small files) and disk download
(large ZIPs that need extraction).

LFPDPPP Compliance:
  - Downloaded content is processed locally and cleaned after training
  - Only metadata (s3_key, bucket) appears in logs
"""
import io
import logging
import os
import shutil
import uuid
import zipfile
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger("ms1.s3_downloader")


class S3Downloader:
    """
    Download objects from MinIO/S3 for vision training.

    Usage:
        dl = S3Downloader()
        dataset_path = dl.download_and_extract_zip(s3_key="images/abc.zip")
        # → /tmp/training_<uuid>/tomate_sana/img1.jpg, etc.
    """

    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="us-east-1",
            config=boto3.session.Config(signature_version="s3v4"),
        )

    @retry(
        retry=retry_if_exception_type((ClientError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def download(self, s3_key: str, bucket: Optional[str] = None) -> bytes:
        """Download an S3 object into memory (for small files)."""
        bucket = bucket or settings.TRAINING_BUCKET_NAME
        buffer = io.BytesIO()
        self._client.download_fileobj(Bucket=bucket, Key=s3_key, Fileobj=buffer)
        buffer.seek(0)
        content = buffer.read()

        logger.info(
            "s3_object_downloaded",
            extra={"s3_key": s3_key, "bucket": bucket, "size_bytes": len(content)},
        )
        return content

    @retry(
        retry=retry_if_exception_type((ClientError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def download_to_path(self, s3_key: str, dest_path: str, bucket: Optional[str] = None) -> str:
        """Download an S3 object to a specific local path (for large files)."""
        bucket = bucket or settings.TRAINING_BUCKET_NAME
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        self._client.download_file(Bucket=bucket, Key=s3_key, Filename=dest_path)

        size = os.path.getsize(dest_path)
        logger.info(
            "s3_object_downloaded_to_disk",
            extra={"s3_key": s3_key, "dest": dest_path, "size_bytes": size},
        )
        return dest_path

    def download_and_extract_zip(
        self, s3_key: str, bucket: Optional[str] = None
    ) -> str:
        """
        Download a ZIP from S3, extract it, and return the extraction directory.

        Expected ZIP structure (PlantVillage convention):
            dataset.zip/
            ├── tomate_sana/
            │   ├── img001.jpg
            │   └── img002.jpg
            ├── tomate_tizon/
            │   ├── img003.jpg
            │   └── img004.jpg
            └── ...

        Returns:
            Path to the extraction directory (e.g. /tmp/training_<uuid>/)
        """
        session_id = uuid.uuid4().hex[:12]
        base_dir = f"/tmp/training_{session_id}"
        zip_path = f"{base_dir}/dataset.zip"

        os.makedirs(base_dir, exist_ok=True)

        # Download ZIP to disk (could be >100MB)
        self.download_to_path(s3_key, zip_path, bucket)

        # Extract
        extract_dir = f"{base_dir}/dataset"
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Security: prevent zip-slip attacks
            for member in zf.namelist():
                member_path = os.path.realpath(os.path.join(extract_dir, member))
                if not member_path.startswith(os.path.realpath(extract_dir)):
                    raise ValueError(f"Zip slip detected: {member}")
            zf.extractall(extract_dir)

        # Remove ZIP to save space
        os.remove(zip_path)

        # Find the actual dataset root (might be nested one level)
        entries = os.listdir(extract_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(extract_dir, entries[0])):
            # ZIP contained a single root folder — descend into it
            dataset_root = os.path.join(extract_dir, entries[0])
        else:
            dataset_root = extract_dir

        logger.info(
            "zip_extracted",
            extra={
                "s3_key": s3_key,
                "dataset_root": dataset_root,
                "classes": os.listdir(dataset_root),
            },
        )
        return dataset_root

    @staticmethod
    def cleanup(path: str) -> None:
        """Remove a temporary training directory."""
        try:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
                logger.info("training_dir_cleaned", extra={"path": path})
        except Exception as e:
            logger.warning("cleanup_failed", extra={"path": path, "error": str(e)})
