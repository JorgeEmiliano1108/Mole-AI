"""Excepciones del dominio de Vision Service"""


class VisionServiceException(Exception):
    """Excepción base del servicio de visión"""
    pass


class InvalidImageException(VisionServiceException):
    """Imagen inválida o no decodificable"""
    pass


class ModelNotReadyException(VisionServiceException):
    """Modelo Phi-3.5 no está listo"""
    pass


class AnalysisFailedException(VisionServiceException):
    """Análisis de imagen falló"""
    pass
