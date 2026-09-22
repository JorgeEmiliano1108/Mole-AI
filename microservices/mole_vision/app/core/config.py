"""
Core Configuration - Centralized Settings
Skill 01: Arquitectura Hexagonal - Capa Core
"""
from typing import Optional
import os
from pydantic import Field
from pydantic.fields import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada del microservicio.
    Todas las variables de entorno se cargan aquí.
    Nombres genéricos (IDP_/LLM_/OBJECT_STORAGE_) con legacy como fallback.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )
    
    # Service
    SERVICE_NAME: str = "mole_vision"
    DEBUG: bool = True
    
    
    SUPABASE_URL: str = Field(default="", validation_alias=AliasChoices("IDP_BASE_URL", "SUPABASE_URL"))
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CHANNEL_PREFIX: str = "mole_vision:"
    
    # Vision Model
    CNN_MODEL_PATH: str = "/app/models/model.tflite"
    CNN_LABELS_PATH: str = "/app/models/labels.json"
    CNN_NUM_THREADS: int = 4
    
    # RNF-02: Defensa Anti-DoS
    INFERENCE_TIMEOUT_SECONDS: float = 2.0
    

    # CORS
    ORIGEN_PERMITIDO: str = "*"
    JWT_SECRET_KEY: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # Security - JWKS Cache
    JWKS_CACHE_TTL_SECONDS: int = 300

    # ── Object Storage S3v4 (Training asset download — Fase 3) ──────────
    AWS_S3_ENDPOINT_URL: str = Field(default="", validation_alias=AliasChoices("OBJECT_STORAGE_ENDPOINT_URL", "AWS_S3_ENDPOINT_URL"))
    AWS_ACCESS_KEY_ID: str = Field(default="", validation_alias=AliasChoices("OBJECT_STORAGE_ACCESS_KEY", "AWS_ACCESS_KEY_ID"))
    AWS_SECRET_ACCESS_KEY: str = Field(default="", validation_alias=AliasChoices("OBJECT_STORAGE_SECRET_KEY", "AWS_SECRET_ACCESS_KEY"))
    TRAINING_BUCKET_NAME: str = Field(default="mole-training-data", validation_alias=AliasChoices("OBJECT_STORAGE_BUCKET_TRAINING", "TRAINING_BUCKET_NAME"))

    # ── LLM visión (API OpenAI-compatible) ────────────────────────────────
    NVIDIA_API_KEY: str = Field(default="", validation_alias=AliasChoices("LLM_API_KEY", "NVIDIA_API_KEY"))
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1", validation_alias=AliasChoices("LLM_BASE_URL", "NVIDIA_BASE_URL"))
    NVIDIA_CHAT_MODEL: str = Field(default="meta/llama-3.3-70b-instruct", validation_alias=AliasChoices("LLM_CHAT_MODEL", "NVIDIA_CHAT_MODEL"))
    NVIDIA_VISION_MODEL: str = Field(default="meta/llama-3.2-11b-vision-instruct", validation_alias=AliasChoices("LLM_VISION_MODEL", "NVIDIA_VISION_MODEL"))

    # ── Fine-Tuning Pipeline ─────────────────────────────────────────────
    CNN_BASE_MODEL_PATH: str = "/app/models/cnn_base.h5"
    TRAINING_EPOCHS: int = 5
    TRAINING_BATCH_SIZE: int = 16
    TRAINING_LEARNING_RATE: float = 0.0001
    TRAINING_OUTPUT_DIR: str = "/app/models/checkpoints"
    TRAINING_IMAGE_SIZE: int = 224


# Singleton instance
settings = Settings()