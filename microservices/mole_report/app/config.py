import os


class Settings:
    HOST: str = os.getenv("MS3_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MS3_PORT", "8003"))
    REDIS_URL: str = os.getenv("MS3_REDIS_URL", "redis://redis:6379")
    S3_ENDPOINT: str = os.getenv("MS3_S3_ENDPOINT")
    S3_ACCESS_KEY: str = os.getenv("MS3_S3_ACCESS_KEY")
    S3_SECRET_KEY: str = os.getenv("MS3_S3_SECRET_KEY")
    S3_BUCKET: str = os.getenv("MS3_S3_BUCKET")
    HUGGINGFACE_API_KEY: str = os.getenv("MS3_HF_KEY", "")
    SUPABASE_URL: str = os.getenv("MS3_SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("MS3_SUPABASE_KEY", "")


settings = Settings()
