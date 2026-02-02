from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class DataPersistencePort(ABC):
    """Puerto para persistencia de datos de diagnóstico"""
    
    @abstractmethod
    async def save_diagnosis(self, diagnosis_data: Dict[str, Any]) -> bool:
        """Guarda diagnóstico en base de datos"""
        pass
    
    @abstractmethod
    async def get_diagnosis(self, diagnosis_id: str) -> Dict[str, Any]:
        """Recupera diagnóstico por ID"""
        pass
    
    @abstractmethod
    async def get_plant_history(self, plant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera historial de diagnósticos de una planta"""
        pass

class SensorDataPort(ABC):
    """Puerto para gestión de datos de sensores"""
    
    @abstractmethod
    async def save_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """Guarda datos de sensores"""
        pass
    
    @abstractmethod
    async def get_sensor_data(self, device_id: str, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        """Recupera datos históricos de sensores"""
        pass
    
    @abstractmethod
    async def get_latest_sensor_data(self, device_id: str) -> Dict[str, Any]:
        """Obtiene datos más recientes de un dispositivo"""
        pass