"""
Core Configuration - Centralized Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str | None = None
    SECRET_KEY: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    SERVICE_NAME: str = "mole_chat"
    DEBUG: bool = True
    API_PORT: str = ""
    
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    REDIS_URL: str = "redis://mole_ai_redis:6379/0"
    
    LLM_MODEL_ID: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    
    TREFLE_API_TOKEN: str = ""
    
    ORIGEN_PERMITIDO: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # ── JWKS / JWT ES256 ─────────────────────────────────────────────────
    JWKS_URL: str = ""
    JWKS_CACHE_TTL_SECONDS: int = 300
    JWT_AUDIENCE: str = "authenticated"
    JWT_LEEWAY: int = 30
    JWT_ALGORITHM: str = "ES256"  # default ES256, fallback HS256 if no JWKS_URL

    # ── PostgreSQL + pgvector (Fase 3 — MLOps Pipeline) ──────────────────
    DATABASE_URL: str = ""

    # ── MinIO / S3 (Training asset download) ─────────────────────────────
    AWS_S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    TRAINING_BUCKET_NAME: str = "mole-training-data"

    # ── RAG Chunking ─────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 100


    # ── mTLS / API‑Key (ETSI EN 303 645) ──────────────────
    API_KEY: str = ""                     # Shared API key for device auth
    TLS_CERT_PATH: str = ""               # Client certificate for mTLS
    TLS_KEY_PATH: str = ""                # Client key for mTLS
    TLS_CA_PATH: str = ""                 # CA certificate for mTLS

    # ── LLM Memory & Performance Limits ──────────────────
    LLM_MAX_MEMORY_MB: int = 4096
    LLM_MAX_NEW_TOKENS: int = 512
    LLM_REQUEST_TIMEOUT: int = 30

    # ── NVIDIA NIM (OpenAI‑compatible) ───────────────────
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_CHAT_MODEL: str = "meta/llama-3.3-70b-instruct"
    NVIDIA_EMBEDDING_MODEL: str = "nvidia/nv-embedqa-e5-v5"

    # ── PDF Ingestion Limits ─────────────────────────────
    MAX_PDF_SIZE: int = 10 * 1024 * 1024   # 10 MiB in bytes
    MAX_PDF_PAGES: int = 200

    # ── Proxy / Rate Limiting ────────────────────────────
    PROXY_HEADER: str = "X-Forwarded-For"
    FALLBACK_IP: str = "127.0.0.1"
    CHAT_RATE_LIMIT: str = "15/minute"

    # ── Session & Cache TTL (seconds) ────────────────────
    SESSION_TTL: int = 900
    SENSOR_CACHE_TTL: int = 300

    # ── Redis Connection Timeouts ────────────────────────
    REDIS_SOCKET_TIMEOUT: int = 2
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 2

    # ── LLM Client Timeouts & Retries ────────────────────
    LLM_TIMEOUT: float = 120.0
    LLM_MAX_RETRIES: int = 0
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024
    LLM_TOP_P: float = 0.7

    # ── Circuit Breaker ──────────────────────────────────
    CB_FAIL_MAX: int = 3
    CB_RESET_TIMEOUT: int = 60

settings = Settings()
