import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Servicio
    RAG_SERVICE_HOST: str = "0.0.0.0"
    RAG_SERVICE_PORT: int = 8002
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-r1:latest")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    
    # LLM Parameters (Críticos para Mole AI)
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))  # Baja creatividad
    LLM_CONTEXT_WINDOW: int = int(os.getenv("LLM_CONTEXT_WINDOW", "4096"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    
    # RAG Configuration
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_CONTEXT_LENGTH: int = int(os.getenv("RAG_CONTEXT_LENGTH", "4000"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
    
    # Vector Database
    VECTOR_DB_PATH: str = "./storage/vectors"
    COLLECTION_NAME: str = "mole_ai_knowledge"
    
    # Document Storage
    DOCUMENT_STORAGE_PATH: str = "./storage/documents"
    MAX_DOCUMENT_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Base de Datos (compartida)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mole_ai_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "mole_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "mole_pass_2026")
    
    # System Prompt (Fijo para Mole AI)
    MOLE_AI_SYSTEM_PROMPT: str = """
    Eres Mole AI, un experto agrónomo especializado en plantas endémicas de México. 
    Tu objetivo es diagnosticar la salud de la planta basándote EXCLUSIVAMENTE en los 
    datos de sensores proporcionados y el contexto recuperado (RAG). Si detectas una 
    plaga o estrés hídrico, sugiere remedios orgánicos. No inventes información.
    """
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"

settings = Settings()