from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    ms3_host: str = "0.0.0.0"
    ms3_port: int = 8003
    ms3_redis_url: str = "redis://mole_ai_redis:6379"
    ms3_celery_broker_url: Optional[str] = None
    ms3_celery_result_backend: Optional[str] = None
    ms3_task_soft_time_limit: int = 600

    ms3_storage_backend: str = "minio"
    ms3_s3_endpoint: Optional[str] = None
    ms3_s3_access_key: str = ""
    ms3_s3_secret_key: str = ""
    ms3_s3_bucket: str = "mole-ai-production"

    ms3_supabase_url: Optional[str] = None
    ms3_supabase_key: Optional[str] = None

    nvidia_api_key: Optional[str] = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_report_model: str = "meta/llama-3.3-70b-instruct"

    origen_permitido: str = ""
    cors_allow_credentials: bool = False
    debug: bool = False
    database_url: Optional[str] = None
    jwt_secret_key: str = ""

    model_config = {"env_prefix": ""}

    @classmethod
    def from_env(cls) -> "Settings":
        import os

        s = cls()
        s.jwt_secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SUPABASE_JWT_SECRET") or ""
        s.debug = os.getenv("DEBUG", "False").lower() == "true"
        s.database_url = os.getenv("DATABASE_URL")

        if not s.ms3_s3_access_key:
            s.ms3_s3_access_key = os.getenv("AWS_ACCESS_KEY_ID") or ""
        if not s.ms3_s3_secret_key:
            s.ms3_s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or ""
        if not s.ms3_s3_bucket:
            s.ms3_s3_bucket = os.getenv("AWS_STORAGE_BUCKET_NAME") or "mole-ai-production"
        return s


settings = Settings.from_env()
