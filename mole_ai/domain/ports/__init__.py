from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models.plant import PlantDiagnosis, SensorData, PlantImage


class VisionProviderPort(ABC):
    """Puerto para análisis visual de plantas"""
    
    @abstractmethod
    async def analyze_plant_image(
        self, 
        image: PlantImage, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analiza imagen de planta y retorna resultado visual"""
        pass


class KnowledgeRetrievalPort(ABC):
    """Puerto para recuperación de conocimiento agronómico"""
    
    @abstractmethod
    async def get_relevant_knowledge(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Recupera conocimiento relevante basado en query"""
        pass


class SensorDataPort(ABC):
    """Puerto para gestión de datos de sensores"""
    
    @abstractmethod
    async def get_latest_sensor_data(
        self, 
        plant_id: Optional[str] = None
    ) -> SensorData:
        """Obtiene datos más recientes de sensores"""
        pass
    
    @abstractmethod
    async def save_sensor_data(
        self, 
        sensor_data: SensorData
    ) -> bool:
        """Persiste datos de sensores"""
        pass


class DiagnosticPersistencePort(ABC):
    """Puerto para persistencia de diagnósticos"""
    
    @abstractmethod
    async def save_diagnosis(
        self, 
        diagnosis: PlantDiagnosis
    ) -> str:
        """Guarda diagnóstico y retorna ID"""
        pass
    
    @abstractmethod
    async def get_diagnosis_history(
        self, 
        plant_id: str, 
        limit: int = 10
    ) -> List[PlantDiagnosis]:
        """Obtiene historial de diagnósticos de una planta"""
        pass


class ModelManagementPort(ABC):
    """Puerto para gestión de modelos de IA"""
    
    @abstractmethod
    async def load_model(self, model_name: str) -> bool:
        """Carga modelo especificado"""
        pass
    
    @abstractmethod
    async def is_model_ready(self) -> bool:
        """Verifica si modelo está listo para inferencia"""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo actual"""
        pass


class NotificationPort(ABC):
    """Puerto para envío de notificaciones"""
    
    @abstractmethod
    async def send_alert(
        self, 
        diagnosis: PlantDiagnosis, 
        recipients: List[str]
    ) -> bool:
        """Envía alerta basada en diagnóstico"""
        pass