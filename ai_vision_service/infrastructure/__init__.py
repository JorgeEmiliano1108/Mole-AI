"""Configuración e inyección de dependencias"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de aplicación"""
    
    # API
    api_title: str = "Mole AI - Vision Service"
    api_description: str = "Análisis visual de plantas con Phi-3.5"
    api_version: str = "1.0.0"
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8001"))
    
    # Modelo
    model_name: str = os.getenv("MODEL_NAME", "microsoft/Phi-3.5-vision-instruct")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"


settings = Settings()
