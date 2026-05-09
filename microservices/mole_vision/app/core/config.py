"""
Core Configuration - Centralized Settings
Skill 01: Arquitectura Hexagonal - Capa Core
"""
from typing import Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada del microservicio.
    Todas las variables de entorno se cargan aquí.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Service
    SERVICE_NAME: str = "mole_vision"
    DEBUG: bool = True
    
    
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""  
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CHANNEL_PREFIX: str = "mole_vision:"
    
    # Vision Model
    CNN_MODEL_PATH: str = "/app/models/model.tflite"
    CNN_LABELS_PATH: str = "/app/models/labels.json"
    CNN_NUM_THREADS: int = 4
    
    # RNF-02: Defensa Anti-DoS
    INFERENCE_TIMEOUT_SECONDS: float = 2.0
    
    # Supabase Database
    SUPABASE_DB_NAME: Optional[str] = None
    SUPABASE_DB_USER: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    SUPABASE_DB_HOST: Optional[str] = None
    SUPABASE_DB_PORT: int = 5432
    
    # CORS
    ORIGEN_PERMITIDO: str = "*"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret")
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # Security - JWKS Cache
    JWKS_CACHE_TTL_SECONDS: int = 300

    # ── MinIO / S3 (Training asset download — Fase 3) ────────────────────
    AWS_S3_ENDPOINT_URL: str = "http://mole_ai_minio:9000"
    AWS_ACCESS_KEY_ID: str = "admin"
    AWS_SECRET_ACCESS_KEY: str = "password123"
    TRAINING_BUCKET_NAME: str = "mole-training-data"

    # ── Fine-Tuning Pipeline ─────────────────────────────────────────────
    CNN_BASE_MODEL_PATH: str = "/app/models/cnn_base.h5"
    TRAINING_EPOCHS: int = 5
    TRAINING_BATCH_SIZE: int = 16
    TRAINING_LEARNING_RATE: float = 0.0001
    TRAINING_OUTPUT_DIR: str = "/app/models/checkpoints"
    TRAINING_IMAGE_SIZE: int = 224


# Singleton instance
settings = Settings()