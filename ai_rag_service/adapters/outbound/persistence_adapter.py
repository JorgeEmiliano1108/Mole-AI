import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..ports.output import DataPersistencePort, SensorDataPort
from ..domain.models import PlantDiagnosis, SensorData
from ..domain.exceptions import RAGException

class JSONPersistenceAdapter(DataPersistencePort):
    """Adaptador simple de persistencia en JSON para desarrollo"""
    
    def __init__(self):
        self.storage_path = "./storage/persistence"
        self.diagnoses_file = os.path.join(self.storage_path, "diagnoses.json")
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Inicializar archivo si no existe
        if not os.path.exists(self.diagnoses_file):
            with open(self.diagnoses_file, 'w') as f:
                json.dump({}, f)
    
    async def save_diagnosis(self, diagnosis_data: Dict[str, Any]) -> bool:
        """Guarda diagnóstico en archivo JSON"""
        try:
            # Cargar diagnósticos existentes
            with open(self.diagnoses_file, 'r') as f:
                diagnoses = json.load(f)
            
            # Agregar nuevo diagnóstico
            diagnosis_id = diagnosis_data.get("diagnosis_id", str(uuid.uuid4()))
            diagnosis_data["saved_at"] = datetime.now().isoformat()
            diagnoses[diagnosis_id] = diagnosis_data
            
            # Guardar en archivo
            with open(self.diagnoses_file, 'w') as f:
                json.dump(diagnoses, f, indent=2)
            
            return True
        except Exception as e:
            raise RAGException(f"Error guardando diagnóstico: {str(e)}")
    
    async def get_diagnosis(self, diagnosis_id: str) -> Dict[str, Any]:
        """Recupera diagnóstico por ID"""
        try:
            with open(self.diagnoses_file, 'r') as f:
                diagnoses = json.load(f)
            
            if diagnosis_id not in diagnoses:
                raise FileNotFoundError(f"Diagnóstico {diagnosis_id} no encontrado")
            
            return diagnoses[diagnosis_id]
        except Exception as e:
            raise RAGException(f"Error recuperando diagnóstico: {str(e)}")
    
    async def get_plant_history(self, plant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera historial de diagnósticos de una planta"""
        try:
            with open(self.diagnoses_file, 'r') as f:
                diagnoses = json.load(f)
            
            # Filtrar por planta_id y ordenar por fecha
            plant_diagnoses = [
                diagnosis for diagnosis in diagnoses.values()
                if diagnosis.get("plant_id") == plant_id
            ]
            
            # Ordenar por fecha (más recientes primero)
            plant_diagnoses.sort(
                key=lambda x: x.get("created_at", ""), 
                reverse=True
            )
            
            return plant_diagnoses[:limit]
        except Exception as e:
            raise RAGException(f"Error recuperando historial: {str(e)}")

class JSONSensorDataAdapter(SensorDataPort):
    """Adaptador simple para datos de sensores en JSON"""
    
    def __init__(self):
        self.storage_path = "./storage/persistence"
        self.sensors_file = os.path.join(self.storage_path, "sensor_data.json")
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Inicializar archivo si no existe
        if not os.path.exists(self.sensors_file):
            with open(self.sensors_file, 'w') as f:
                json.dump({"sensor_readings": []}, f)
    
    async def save_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """Guarda datos de sensores"""
        try:
            # Cargar datos existentes
            with open(self.sensors_file, 'r') as f:
                data = json.load(f)
            
            # Agregar nueva lectura
            sensor_data["saved_at"] = datetime.now().isoformat()
            data["sensor_readings"].append(sensor_data)
            
            # Mantener solo últimos 1000 registros para evitar crecimiento infinito
            if len(data["sensor_readings"]) > 1000:
                data["sensor_readings"] = data["sensor_readings"][-1000:]
            
            # Guardar en archivo
            with open(self.sensors_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            raise RAGException(f"Error guardando datos de sensores: {str(e)}")
    
    async def get_sensor_data(self, device_id: str, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        """Recupera datos históricos de sensores"""
        try:
            with open(self.sensors_file, 'r') as f:
                data = json.load(f)
            
            # Filtrar por dispositivo y rango de fechas
            filtered_data = []
            for reading in data.get("sensor_readings", []):
                reading_date = datetime.fromisoformat(reading.get("timestamp", ""))
                
                if (reading.get("device_id") == device_id and
                    from_date <= reading_date <= to_date):
                    filtered_data.append(reading)
            
            # Ordenar por fecha ascendente
            filtered_data.sort(key=lambda x: x.get("timestamp", ""))
            
            return filtered_data
        except Exception as e:
            raise RAGException(f"Error recuperando datos históricos: {str(e)}")
    
    async def get_latest_sensor_data(self, device_id: str) -> Dict[str, Any]:
        """Obtiene datos más recientes de un dispositivo"""
        try:
            with open(self.sensors_file, 'r') as f:
                data = json.load(f)
            
            # Filtrar por dispositivo y obtener el más reciente
            device_readings = [
                reading for reading in data.get("sensor_readings", [])
                if reading.get("device_id") == device_id
            ]
            
            if not device_readings:
                return {}
            
            # Ordenar por timestamp descendente y tomar el primero
            device_readings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return device_readings[0]
            
        except Exception as e:
            raise RAGException(f"Error obteniendo datos recientes: {str(e)}")