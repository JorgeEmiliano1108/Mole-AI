class VisionException(Exception):
    """Excepción base para el servicio de visión"""
    pass

class ImageProcessingError(VisionException):
    """Error en el procesamiento de imagen"""
    pass

class ModelLoadError(VisionException):
    """Error cargando modelos de IA"""
    pass

class UnsupportedImageFormat(VisionException):
    """Formato de imagen no soportado"""
    pass

class InsufficientConfidenceError(VisionException):
    """Confianza insuficiente en la detección"""
    pass