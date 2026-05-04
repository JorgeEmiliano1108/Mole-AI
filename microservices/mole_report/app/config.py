import os


class Settings:
    HOST: str = os.getenv("MS3_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MS3_PORT", "8003"))
    # B3 FIX: hostname corregido al container_name real de Docker
    REDIS_URL: str = os.getenv("MS3_REDIS_URL", "redis://mole_ai_redis:6379")
    # MinIO S3-compatible storage (local)
    S3_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    S3_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    S3_BUCKET: str = os.getenv("MINIO_BUCKET", "mole-ai-storage")
    HUGGINGFACE_API_KEY: str = os.getenv("MS3_HF_KEY", "")

settings = Settings()

