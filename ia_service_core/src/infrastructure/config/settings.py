import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de Datos
    DB_USER: str = os.getenv("POSTGRES_USER", "user")
    DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    DB_HOST: str = os.getenv("POSTGRES_HOST", "db")
    DB_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME: str = os.getenv("POSTGRES_DB", "escalafon_db")

    # IA (Ollama)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.1:8b-instruct")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    
    # RAG Configuration
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_CONTEXT_LENGTH: int = int(os.getenv("RAG_CONTEXT_LENGTH", "4000"))

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()