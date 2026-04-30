"""
S3 Downloader — MinIO/AWS S3 asset retrieval for the RAG pipeline.

Downloads training documents (PDFs) from MinIO into memory
for processing by the RAG ingestion pipeline.

LFPDPPP Compliance:
  - Downloaded content is processed in-memory and never persisted locally
  - Only metadata (s3_key, bucket) transits through logs
"""
import io
import logging

import boto3
from botocore.exceptions import ClientError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger("ms2.s3_downloader")


class S3Downloader:
    """
    Download objects from MinIO/S3 for RAG processing.

    Usage:
        dl = S3Downloader()
        pdf_bytes = dl.download(s3_key="documents/abc.pdf", bucket="mole-training-data")
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
    def download(self, s3_key: str, bucket: str | None = None) -> bytes:
        """
        Download an S3 object into memory.

        Args:
            s3_key: Full S3 object key (e.g. 'documents/<uuid>.pdf')
            bucket: Bucket name (default: TRAINING_BUCKET_NAME)

        Returns:
            Raw bytes of the downloaded object
        """
        bucket = bucket or settings.TRAINING_BUCKET_NAME
        buffer = io.BytesIO()

        self._client.download_fileobj(
            Bucket=bucket,
            Key=s3_key,
            Fileobj=buffer,
        )
        buffer.seek(0)
        content = buffer.read()

        logger.info(
            "s3_object_downloaded",
            extra={"s3_key": s3_key, "bucket": bucket, "size_bytes": len(content)},
        )
        return content

    def head(self, s3_key: str, bucket: str | None = None) -> dict:
        """HEAD an object to get metadata without downloading."""
        bucket = bucket or settings.TRAINING_BUCKET_NAME
        try:
            resp = self._client.head_object(Bucket=bucket, Key=s3_key)
            return {
                "exists": True,
                "size": resp.get("ContentLength", 0),
                "content_type": resp.get("ContentType", ""),
            }
        except ClientError:
            return {"exists": False, "size": 0, "content_type": ""}
