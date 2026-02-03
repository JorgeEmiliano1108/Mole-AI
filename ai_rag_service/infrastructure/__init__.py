"""Configuración del RAG Service"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de aplicación"""
    
    # API
    api_title: str = "Mole AI - RAG Service"
    api_description: str = "RAG + Razonamiento con Phi-3.5"
    api_version: str = "1.0.0"
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8002"))
    
    # Modelos
    reasoning_model: str = os.getenv("REASONING_MODEL", "microsoft/Phi-3.5-vision-instruct")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Vector DB
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "storage/vectors")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"


settings = Settings()
