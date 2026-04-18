"""
Core Configuration - Centralized Settings
Skill 01: Arquitectura Hexagonal - Capa Core
"""
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
    DEBUG: bool = False
    
    # Supabase Auth (Zero-Trust)
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CHANNEL_PREFIX: str = "mole_vision:"
    
    # Vision Model
    CNN_MODEL_PATH: str = "/app/models/cnn.tflite"
    CNN_LABELS_PATH: str = "/app/models/labels.json"
    CNN_NUM_THREADS: int = 4
    
    # Supabase Database (optional)
    SUPABASE_DB_NAME: str = ""
    SUPABASE_DB_USER: str = ""
    SUPABASE_DB_PASSWORD: str = ""
    SUPABASE_DB_HOST: str = ""
    SUPABASE_DB_PORT: int = 5432
    
    # CORS
    ORIGEN_PERMITIDO: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # Security - JWKS Cache
    JWKS_CACHE_TTL_SECONDS: int = 300  # 5 minutes


# Singleton instance
settings = Settings()