"""Excepciones del RAG Service"""


class RAGServiceException(Exception):
    """Excepción base"""
    pass


class PDFUploadException(RAGServiceException):
    """Error al subir PDF"""
    pass


class RAGRetrievalException(RAGServiceException):
    """Error al recuperar conocimiento"""
    pass


class DiagnoseException(RAGServiceException):
    """Error en diagnóstico final"""
    pass
