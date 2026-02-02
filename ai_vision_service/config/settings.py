import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Servicio
    VISION_SERVICE_HOST: str = "0.0.0.0"
    VISION_SERVICE_PORT: int = 8001
    
    # Modelos YOLO
    YOLO_INFRARED_MODEL: str = "yolov8n.pt"
    YOLO_RGB_MODEL: str = "yolov8n.pt"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.5
    
    # Almacenamiento
    IMAGE_STORAGE_PATH: str = "./storage/images"
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Análisis
    WATER_STRESS_THRESHOLD: float = 0.3  # Umbral para detección de estrés hídrico
    PEST_DETECTION_THRESHOLD: float = 0.6
    
    # Base de Datos (compartida)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mole_ai_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "mole_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "mole_pass_2026")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"

settings = Settings()