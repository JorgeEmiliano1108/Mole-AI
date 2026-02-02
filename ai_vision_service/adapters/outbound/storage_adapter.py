import os
import json
from typing import Dict, Any
from datetime import datetime
import hashlib

from ..ports.output import ImageStoragePort, VisionRepositoryPort
from ..domain.models import ImageAnalysis, VectorDocument
from ..domain.exceptions import VisionException
from ..config.settings import settings

class FileSystemImageStorageAdapter(ImageStoragePort):
    """Adaptador para almacenamiento de imágenes en sistema de archivos"""
    
    def __init__(self):
        self.storage_path = settings.IMAGE_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def save_image(self, image_id: str, image_bytes: bytes, metadata: Dict[str, Any]) -> bool:
        """Guarda imagen en sistema de archivos"""
        try:
            image_path = os.path.join(self.storage_path, f"{image_id}.jpg")
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            # Guardar metadatos
            metadata_path = os.path.join(self.storage_path, f"{image_id}_metadata.json")
            metadata['saved_at'] = datetime.now().isoformat()
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
        except Exception as e:
            raise VisionException(f"Error guardando imagen {image_id}: {str(e)}")
    
    async def get_image(self, image_id: str) -> bytes:
        """Recupera imagen del almacenamiento"""
        try:
            image_path = os.path.join(self.storage_path, f"{image_id}.jpg")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Imagen {image_id} no encontrada")
            
            with open(image_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise VisionException(f"Error recuperando imagen {image_id}: {str(e)}")

class SimpleVisionRepositoryAdapter(VisionRepositoryPort):
    """Adaptador simple de persistencia (JSON para desarrollo)"""
    
    def __init__(self):
        self.storage_path = settings.IMAGE_STORAGE_PATH
        self.analysis_file = os.path.join(self.storage_path, "analysis_history.json")
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Inicializar archivo si no existe
        if not os.path.exists(self.analysis_file):
            with open(self.analysis_file, 'w') as f:
                json.dump({}, f)
    
    async def save_analysis(self, analysis: ImageAnalysis) -> bool:
        """Guarda resultado del análisis"""
        try:
            # Cargar análisis existentes
            with open(self.analysis_file, 'r') as f:
                analyses = json.load(f)
            
            # Convertir análisis a diccionario
            analysis_dict = {
                "image_id": analysis.image_id,
                "analysis_type": analysis.analysis_type,
                "plant_type": analysis.plant_type,
                "health_status": analysis.health_status,
                "confidence": analysis.confidence,
                "detections": analysis.detections,
                "recommendations": analysis.recommendations,
                "processed_at": analysis.processed_at.isoformat()
            }
            
            # Guardar nuevo análisis
            analyses[analysis.image_id] = analysis_dict
            
            with open(self.analysis_file, 'w') as f:
                json.dump(analyses, f, indent=2)
            
            return True
        except Exception as e:
            raise VisionException(f"Error guardando análisis: {str(e)}")
    
    async def get_analysis(self, image_id: str) -> ImageAnalysis:
        """Recupera análisis anterior"""
        try:
            with open(self.analysis_file, 'r') as f:
                analyses = json.load(f)
            
            if image_id not in analyses:
                raise FileNotFoundError(f"Análisis para {image_id} no encontrado")
            
            data = analyses[image_id]
            return ImageAnalysis(
                image_id=data["image_id"],
                analysis_type=data["analysis_type"],
                plant_type=data["plant_type"],
                health_status=data["health_status"],
                confidence=data["confidence"],
                detections=data["detections"],
                recommendations=data["recommendations"],
                processed_at=datetime.fromisoformat(data["processed_at"])
            )
        except Exception as e:
            raise VisionException(f"Error recuperando análisis: {str(e)}")
    
    async def search_similar_images(self, image_vector: list, limit: int = 5) -> list:
        """Busca imágenes similares (implementación simple basada en metadatos)"""
        try:
            with open(self.analysis_file, 'r') as f:
                analyses = json.load(f)
            
            # Búsqueda simple basada en tipo de planta y estado de salud
            similar = []
            for image_id, data in analyses.items():
                similar.append(VectorDocument(
                    doc_id=image_id,
                    content=json.dumps(data),
                    metadata={
                        "plant_type": data["plant_type"],
                        "health_status": data["health_status"],
                        "analysis_type": data["analysis_type"]
                    }
                ))
            
            return similar[:limit]
        except Exception as e:
            raise VisionException(f"Error buscando imágenes similares: {str(e)}")