import os
import boto3
from urllib.parse import urlparse
from botocore.exceptions import ClientError


class S3Adapter:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        self.endpoint = endpoint
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    @classmethod
    def from_env(cls):
        from app.config import settings

        return cls(
            settings.S3_ENDPOINT,
            settings.S3_ACCESS_KEY,
            settings.S3_SECRET_KEY,
            settings.S3_BUCKET,
        )

    def upload_bytes(self, data: bytes, key: str) -> str:
        # Ensure the target bucket exists (idempotent). This prevents
        # race conditions where tasks try to upload before the bucket
        # has been created by infra or other services.
        self._ensure_bucket_exists()
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data, ACL="private")
        return key

    def _ensure_bucket_exists(self) -> None:
        """Idempotently ensure the configured bucket exists.

        This first attempts a HEAD on the bucket. If the bucket is missing
        it will attempt to create it. Creation errors that indicate the
        bucket is already owned/exists are treated as success. Other
        ClientError cases are re-raised so calling code can handle them.
        """
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            return
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            # Common codes for missing bucket/providers
            if error_code in ("404", "NoSuchBucket", "NotFound"):
                try:
                    # Some S3 providers (MinIO) accept create_bucket without
                    # additional args; AWS may require LocationConstraint in
                    # certain regions but boto3 will handle defaults in many
                    # cases. Try a plain create first.
                    self.s3.create_bucket(Bucket=self.bucket)
                    return
                except ClientError as ce:
                    ce_code = ce.response.get("Error", {}).get("Code", "")
                    # Bucket already exists/owned by you — treat as success
                    if ce_code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                        return
                    # Otherwise fall through and try a final head check
                    try:
                        self.s3.head_bucket(Bucket=self.bucket)
                        return
                    except Exception:
                        raise
            # If the error indicates ownership/redirect, treat bucket as present
            if error_code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists", "301"):
                return
            # Re-raise unexpected errors (403, permissions, etc.)
            raise

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in
        )
