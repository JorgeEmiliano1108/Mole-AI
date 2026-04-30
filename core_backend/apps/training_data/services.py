# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
S3 Training Service — Infrastructure adapter for MinIO/AWS S3.

Handles:
  - Presigned URL generation (PUT for uploads, GET for downloads)
  - Object existence verification (HEAD)
  - Bucket creation (idempotent)

Reuses the retry pattern from MS3's S3Adapter (tenacity + exponential backoff).
"""
import logging
import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class S3TrainingService:
    """
    Thin wrapper around boto3 for the training data pipeline.

    Usage:
        svc = S3TrainingService()
        url = svc.generate_presigned_put_url("documents/abc.pdf", "application/pdf")
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket_name: str | None = None,
        region: str | None = None,
    ):
        self.endpoint_url = endpoint_url or getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        self.bucket_name = bucket_name or getattr(settings, 'TRAINING_BUCKET_NAME', 'mole-training-data')
        self.region = region or getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')

        self._client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key or getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=secret_key or getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=self.region,
            config=boto3.session.Config(signature_version='s3v4'),
        )

    # ── Bucket Management ────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ClientError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def ensure_bucket_exists(self) -> None:
        """Idempotently ensure the training bucket exists (MinIO/AWS)."""
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
            return
        except ClientError as exc:
            error_code = exc.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchBucket', 'NotFound'):
                try:
                    self._client.create_bucket(Bucket=self.bucket_name)
                    logger.info("s3_bucket_created", extra={"bucket": self.bucket_name})
                    return
                except ClientError as ce:
                    ce_code = ce.response.get('Error', {}).get('Code', '')
                    if ce_code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
                        return
                    raise
            if error_code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists', '301'):
                return
            raise

    # ── Presigned URLs ───────────────────────────────────────────────────

    def generate_presigned_put_url(
        self,
        s3_key: str,
        content_type: str,
        max_content_length: int | None = None,
        ttl: int | None = None,
    ) -> str:
        """
        Generate a presigned PUT URL for direct frontend-to-S3 upload.

        NOTE: This is a pure signing operation — no network call is made.
        The bucket must exist when the client performs the actual PUT.
        Call ensure_bucket_exists() separately if needed.

        Args:
            s3_key: Full object key (e.g. 'documents/<uuid>.pdf')
            content_type: MIME type constraint
            max_content_length: Maximum file size in bytes (informational —
                                S3 conditions enforce via policy, not PUT URL)
            ttl: URL expiration in seconds (default: TRAINING_PRESIGNED_TTL)

        Returns:
            Presigned URL string
        """
        expires_in = ttl or getattr(settings, 'TRAINING_PRESIGNED_TTL', 900)

        url = self._client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'ContentType': content_type,
            },
            ExpiresIn=expires_in,
        )
        logger.info(
            "presigned_put_url_generated",
            extra={"s3_key": s3_key, "ttl": expires_in},
        )
        return url

    def generate_presigned_get_url(self, s3_key: str, ttl: int = 3600) -> str:
        """Generate a presigned GET URL for downloading an object."""
        return self._client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': self.bucket_name, 'Key': s3_key},
            ExpiresIn=ttl,
        )

    # ── Object Verification ──────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(ClientError),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def verify_object_exists(self, s3_key: str) -> dict:
        """
        HEAD the object to verify it was uploaded successfully.

        Returns:
            dict with keys: exists (bool), size (int), etag (str)
        """
        try:
            response = self._client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return {
                'exists': True,
                'size': response.get('ContentLength', 0),
                'etag': response.get('ETag', '').strip('"'),
                'content_type': response.get('ContentType', ''),
            }
        except ClientError as exc:
            error_code = exc.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchKey', 'NotFound'):
                return {'exists': False, 'size': 0, 'etag': '', 'content_type': ''}
            raise

    # ── Key Generation Helpers ───────────────────────────────────────────

    @staticmethod
    def generate_document_key(original_filename: str) -> str:
        """Generate a UUID-based S3 key for a training document."""
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'pdf'
        return f"documents/{uuid.uuid4().hex}.{ext}"

    @staticmethod
    def generate_image_key(original_filename: str) -> str:
        """Generate a UUID-based S3 key for a training image/ZIP."""
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
        return f"images/{uuid.uuid4().hex}.{ext}"
