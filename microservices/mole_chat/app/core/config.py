"""
Core Configuration - Centralized Settings
"""
from pydantic import Field
from pydantic.fields import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str | None = None
    SECRET_KEY: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )
    
    SERVICE_NAME: str = "mole_chat"
    DEBUG: bool = True
    API_PORT: str = ""
    
    # Identidad externa (IdP GoTrue-compatible). Legacy SUPABASE_* como fallback.
    SUPABASE_URL: str = Field(default="", validation_alias=AliasChoices("IDP_BASE_URL", "SUPABASE_URL"))
    SUPABASE_JWT_SECRET: str = Field(default="", validation_alias=AliasChoices("IDP_JWT_SECRET", "SUPABASE_JWT_SECRET"))
    
    REDIS_URL: str = "redis://mole_ai_redis:6379/0"
    
    TREFLE_API_TOKEN: str = Field(default="", validation_alias=AliasChoices("BOTANICAL_API_TOKEN", "TREFLE_API_TOKEN"))
    
    ORIGEN_PERMITIDO: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # ── JWKS / JWT ES256 ─────────────────────────────────────────────────
    JWKS_URL: str = ""
    JWKS_CACHE_TTL_SECONDS: int = 300
    JWT_AUDIENCE: str = "authenticated"
    JWT_LEEWAY: int = 30
    JWT_ALGORITHM: str = "ES256"  # default ES256, fallback HS256 if no JWKS_URL

    # ── PostgreSQL + pgvector (Fase 3 — MLOps Pipeline) ──────────────────
    # Genérico DB_URL, legacy DATABASE_URL.
    DATABASE_URL: str = Field(default="", validation_alias=AliasChoices("DB_URL", "DATABASE_URL"))

    # ── Object Storage S3v4 (Training asset download) ─────────────────────
    AWS_S3_ENDPOINT_URL: str = Field(default="", validation_alias=AliasChoices("OBJECT_STORAGE_ENDPOINT_URL", "AWS_S3_ENDPOINT_URL"))
    AWS_ACCESS_KEY_ID: str = Field(default="", validation_alias=AliasChoices("OBJECT_STORAGE_ACCESS_KEY", "AWS_ACCESS_KEY_ID"))
    AWS_SECRET_ACCESS_KEY: str = Field(default="", validation_alias=AliasChoices("OBJECT_STORAGE_SECRET_KEY", "AWS_SECRET_ACCESS_KEY"))
    TRAINING_BUCKET_NAME: str = Field(default="mole-training-data", validation_alias=AliasChoices("OBJECT_STORAGE_BUCKET_TRAINING", "TRAINING_BUCKET_NAME"))

    # ── RAG Chunking ─────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 100


    # ── mTLS / API‑Key (ETSI EN 303 645) ──────────────────
    # Genérico EDGE_API_KEY (el .env único), legacy API_KEY.
    API_KEY: str = Field(default="", validation_alias=AliasChoices("EDGE_API_KEY", "API_KEY"))  # Shared API key for device auth
    TLS_CERT_PATH: str = ""               # Client certificate for mTLS
    TLS_KEY_PATH: str = ""                # Client key for mTLS
    TLS_CA_PATH: str = ""                 # CA certificate for mTLS

    # ── LLM Memory & Performance Limits ──────────────────
    LLM_MAX_MEMORY_MB: int = 4096
    LLM_MAX_NEW_TOKENS: int = 512
    LLM_REQUEST_TIMEOUT: int = 30

    # ── LLM (API OpenAI-compatible: NIM, Ollama, vLLM) ───────────────────
    # Genérico LLM_*, legacy NVIDIA_*.
    NVIDIA_API_KEY: str = Field(default="", validation_alias=AliasChoices("LLM_API_KEY", "NVIDIA_API_KEY"))
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1", validation_alias=AliasChoices("LLM_BASE_URL", "NVIDIA_BASE_URL"))
    NVIDIA_CHAT_MODEL: str = Field(default="meta/llama-3.3-70b-instruct", validation_alias=AliasChoices("LLM_CHAT_MODEL", "NVIDIA_CHAT_MODEL"))
    NVIDIA_EMBEDDING_MODEL: str = Field(default="nvidia/nv-embedqa-e5-v5", validation_alias=AliasChoices("LLM_EMBEDDING_MODEL", "NVIDIA_EMBEDDING_MODEL"))

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

    # ── Orquestador LangGraph (V3, MRF04) ─────────────────
    # Apagado por defecto: el endpoint usa el caso de uso directo.
    # Encender solo tras validar puerta F4 (métricas + threshold).
    ORCHESTRATOR_ENABLED: bool = False
    ORCHESTRATOR_TIMEOUT_S: float = 30.0

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
