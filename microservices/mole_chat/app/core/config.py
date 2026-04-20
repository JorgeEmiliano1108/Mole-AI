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
    
    REDIS_URL: str = "redis://redis:6379/0"
    
    LLM_MODEL_ID: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    HUGGINGFACE_API_KEY: str = ""
    HF_INFERENCE_API_URL: str = "https://router.huggingface.co/hf-inference/v1"
    HF_API_TIMEOUT: int = 30
    
    TREFLE_API_TOKEN: str = ""
    
    ORIGEN_PERMITIDO: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    
    JWKS_CACHE_TTL_SECONDS: int = 300


settings = Settings()