class PlantAnalysisException(Exception):
    """Excepción base para análisis de plantas"""
    pass


class VisionAnalysisError(PlantAnalysisException):
    """Error en análisis visual"""
    pass


class KnowledgeRetrievalError(PlantAnalysisException):
    """Error en recuperación de conocimiento"""
    pass


class SensorDataError(PlantAnalysisException):
    """Error en datos de sensores"""
    pass


class PersistenceError(PlantAnalysisException):
    """Error en persistencia"""
    pass


class ModelLoadError(PlantAnalysisException):
    """Error en carga de modelos"""
    pass


class ConfidenceThresholdError(PlantAnalysisException):
    """Error en umbral de confianza"""
    pass


class InvalidImageError(PlantAnalysisException):
    """Error en formato de imagen"""
    pass


class InvalidSensorDataError(PlantAnalysisException):
    """Error en datos de sensores inválidos"""
    pass


class DatabaseConnectionError(PlantAnalysisException):
    """Error en conexión a base de datos"""
    pass


class ModelNotReadyError(PlantAnalysisException):
    """Modelo no listo para inferencia"""
    pass


class ServiceUnavailableError(PlantAnalysisException):
    """Servicio no disponible"""
    pass


class ConfigurationError(PlantAnalysisException):
    """Error de configuración"""
    pass