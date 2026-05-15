import os


class Settings:
    HOST: str = os.getenv("MS3_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MS3_PORT", "8003"))
    REDIS_URL: str = os.getenv("MS3_REDIS_URL", "redis://mole_ai_redis:6379")
    # AWS S3 (native — MinIO removed)
    S3_ENDPOINT: str | None = os.getenv("MS3_S3_ENDPOINT") or None   # None → boto3 uses native AWS
    S3_ACCESS_KEY: str = os.getenv("MS3_S3_ACCESS_KEY", os.getenv("AWS_ACCESS_KEY_ID", ""))
    S3_SECRET_KEY: str = os.getenv("MS3_S3_SECRET_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
    S3_BUCKET: str = os.getenv("MS3_S3_BUCKET", os.getenv("AWS_STORAGE_BUCKET_NAME", "mole-ai-production"))

settings = Settings()

