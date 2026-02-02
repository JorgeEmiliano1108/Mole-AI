class RAGException(Exception):
    """Excepción base para el servicio RAG"""
    pass

class LLMServiceError(RAGException):
    """Error en el servicio de LLM"""
    pass

class VectorDBError(RAGException):
    """Error en la base de datos vectorial"""
    pass

class KnowledgeBaseError(RAGException):
    """Error en la base de conocimiento"""
    pass

class DiagnosticError(RAGException):
    """Error en el proceso de diagnóstico"""
    pass

class InsufficientContextError(RAGException):
    """Contexto insuficiente para diagnóstico"""
    pass

class InvalidSensorDataError(RAGException):
    """Datos de sensores inválidos"""
    pass

class DocumentProcessingError(RAGException):
    """Error procesando documento"""
    pass

class EmbeddingGenerationError(RAGException):
    """Error generando embeddings"""
    pass