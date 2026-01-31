from src.infrastructure.persistence.vector_repo import PostgresVectorRepo
from src.infrastructure.external.ollama import OllamaAdapter
from src.application.use_cases.chat_rag import ChatRAGUseCase
from src.application.use_cases.ingest_doc import IngestDocUseCase
from src.application.use_cases.ingest_text import IngestTextUseCase

# Instancias Globales
db_instance = PostgresVectorRepo()
llm_instance = OllamaAdapter()

def get_chat_use_case() -> ChatRAGUseCase:
    """Inyecta DB y LLM al caso de uso de Chat"""
    return ChatRAGUseCase(db=db_instance, llm=llm_instance)

def get_ingest_use_case() -> IngestDocUseCase:
    """Inyecta DB y LLM al caso de uso de Ingesta"""
    return IngestDocUseCase(db=db_instance, llm=llm_instance)

def get_ingest_text_use_case() -> IngestTextUseCase:
    return IngestTextUseCase(db=db_instance, llm=llm_instance)