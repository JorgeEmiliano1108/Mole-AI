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

        def _first(*names: str, default: str = "") -> str:
            """Primera var definida y no vacía (genérica primero, legacy después)."""
            for name in names:
                value = os.getenv(name)
                if value:
                    return value
            return default

        s = cls()
        s.jwt_secret_key = _first("JWT_SECRET_KEY", "IDP_JWT_SECRET", "SUPABASE_JWT_SECRET")
        s.debug = os.getenv("DEBUG", "False").lower() == "true"
        s.database_url = _first("DB_URL", "DATABASE_URL") or None
        # El default histórico apuntaba al host inexistente `mole_ai_redis`;
        # REDIS_URL del entorno (compose) manda salvo override explícito ms3_redis_url.
        if s.ms3_redis_url == "redis://mole_ai_redis:6379":
            s.ms3_redis_url = _first("REDIS_URL", default=s.ms3_redis_url)

        if not s.ms3_s3_access_key:
            s.ms3_s3_access_key = _first("OBJECT_STORAGE_ACCESS_KEY", "AWS_ACCESS_KEY_ID")
        if not s.ms3_s3_secret_key:
            s.ms3_s3_secret_key = _first("OBJECT_STORAGE_SECRET_KEY", "AWS_SECRET_ACCESS_KEY")
        if not s.ms3_s3_bucket:
            s.ms3_s3_bucket = _first("OBJECT_STORAGE_BUCKET_REPORTS", "OBJECT_STORAGE_BUCKET_MEDIA", "AWS_STORAGE_BUCKET_NAME", default="mole-ai-production")
        if not s.ms3_s3_endpoint:
            s.ms3_s3_endpoint = _first("OBJECT_STORAGE_ENDPOINT_URL") or None
        if not s.ms3_supabase_url:
            s.ms3_supabase_url = _first("IDP_BASE_URL", "SUPABASE_URL") or None
        if not s.ms3_supabase_key:
            s.ms3_supabase_key = _first("IDP_SERVICE_KEY", "SUPABASE_KEY") or None
        if not s.nvidia_api_key:
            s.nvidia_api_key = _first("LLM_API_KEY", "NVIDIA_API_KEY") or None
        s.nvidia_base_url = _first("LLM_BASE_URL", "NVIDIA_BASE_URL", default=s.nvidia_base_url)
        return s


settings = Settings.from_env()
