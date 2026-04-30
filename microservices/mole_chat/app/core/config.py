"""
Core Configuration - Centralized Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    SERVICE_NAME: str = "mole_chat"
    DEBUG: bool = True
    
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # B3 FIX: hostname corregido al container_name real de Docker
    REDIS_URL: str = "redis://mole_ai_redis:6379/0"
    
    LLM_MODEL_ID: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    HUGGINGFACE_API_KEY: str = ""
    HF_INFERENCE_API_URL: str = "https://router.huggingface.co/hf-inference/v1"
    HF_API_TIMEOUT: int = 30
    
    TREFLE_API_TOKEN: str = ""
    
    ORIGEN_PERMITIDO: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    
    JWKS_CACHE_TTL_SECONDS: int = 300

    # ── PostgreSQL + pgvector (Fase 3 — MLOps Pipeline) ──────────────────
    # C4 FIX: hostname corregido de 'db' → 'mole_ai_db' (container_name real)
    DATABASE_URL: str = "postgresql://postgres:postgres@mole_ai_db:5432/mole_ai_db"

    # ── Embeddings ───────────────────────────────────────────────────────
    EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 = 384d

    # ── MinIO / S3 (Training asset download) ─────────────────────────────
    AWS_S3_ENDPOINT_URL: str = "http://mole_ai_minio:9000"
    AWS_ACCESS_KEY_ID: str = "admin"
    AWS_SECRET_ACCESS_KEY: str = "password123"
    TRAINING_BUCKET_NAME: str = "mole-training-data"

    # ── RAG Chunking ─────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 100


settings = Settings()