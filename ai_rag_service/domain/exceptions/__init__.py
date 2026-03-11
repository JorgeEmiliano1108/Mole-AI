"""Excepciones del RAG Service"""


class RAGServiceException(Exception):
    """Excepción base"""


class PDFUploadException(RAGServiceException):
    """Error al subir PDF"""


class RAGRetrievalException(RAGServiceException):
    """Error al recuperar conocimiento"""


class DiagnoseException(RAGServiceException):
    """Error en diagnóstico final"""
