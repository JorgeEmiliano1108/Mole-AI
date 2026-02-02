import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from PIL import Image
import io
import base64
from ultralytics import YOLO

from ..ports.input import ImageAnalyzerPort
from ..domain.models import ImageAnalysis, AnalysisType, PlantType, HealthStatus
from ..domain.exceptions import ImageProcessingError, ModelLoadError, UnsupportedImageFormat
from ..config.settings import settings

class YOLOAdapter(ImageAnalyzerPort):
    """Adaptador YOLOv8 para análisis de imágenes de plantas"""
    
    def __init__(self):
        try:
            self.infrared_model = YOLO(settings.YOLO_INFRARED_MODEL)
            self.rgb_model = YOLO(settings.YOLO_RGB_MODEL)
        except Exception as e:
            raise ModelLoadError(f"Error cargando modelos YOLO: {str(e)}")
    
    async def analyze_image_base64(self, image_b64: str, analysis_type: AnalysisType) -> ImageAnalysis:
        """Analiza imagen en formato base64"""
        try:
            image_bytes = self._decode_base64(image_b64)
            image_array = self._bytes_to_array(image_bytes)
            image_id = ImageAnalysis.generate_id(image_bytes)
            
            if analysis_type == AnalysisType.INFRARED:
                return await self._analyze_infrared(image_array, image_bytes, image_id)
            else:
                return await self._analyze_rgb(image_array, image_bytes, image_id)
                
        except Exception as e:
            raise ImageProcessingError(f"Error analizando imagen: {str(e)}")
    
    async def detect_plant_type(self, image_b64: str) -> PlantType:
        """Detecta el tipo de planta usando características visuales"""
        try:
            image_bytes = self._decode_base64(image_b64)
            image_array = self._bytes_to_array(image_bytes)
            
            # Análisis básico basado en características de color y forma
            hsv = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
            
            # Análisis de distribución de color
            green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
            green_ratio = cv2.countNonZero(green_mask) / (image_array.shape[0] * image_array.shape[1])
            
            # Detección simple basada en patrones
            if green_ratio > 0.3:
                return PlantType.CHILE  # Chile típico mexicano
            elif self._detect_maize_pattern(image_array):
                return PlantType.MAIZ
            elif self._detect_avocado_pattern(image_array):
                return PlantType.AGUACATE
            else:
                return PlantType.DESCONOCIDA
                
        except Exception as e:
            raise ImageProcessingError(f"Error detectando tipo de planta: {str(e)}")
    
    async def detect_health_issues(self, image_b64: str, plant_type: str) -> List[Dict[str, Any]]:
        """Detecta problemas de salud en la planta"""
        try:
            image_bytes = self._decode_base64(image_b64)
            image_array = self._bytes_to_array(image_bytes)
            
            results = []
            
            # Detección de plagas usando YOLO
            detections = self.rgb_model(image_array)
            for detection in detections[0].boxes.data.tolist():
                x1, y1, x2, y2, confidence, class_id = detection
                if confidence > settings.MODEL_CONFIDENCE_THRESHOLD:
                    results.append({
                        "type": "pest",
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                        "class_name": self.rgb_model.names[int(class_id)]
                    })
            
            # Detección de estrés hídrico (análisis de color)
            if self._detect_water_stress(image_array):
                results.append({
                    "type": "water_stress",
                    "confidence": 0.7,
                    "severity": "medium",
                    "description": "Posible estrés hídrico detectado"
                })
            
            # Detección de deficiencias nutricionales
            if self._detect_nutrient_deficiency(image_array):
                results.append({
                    "type": "nutrient_deficiency",
                    "confidence": 0.6,
                    "description": "Síntomas de posible deficiencia nutricional"
                })
            
            return results
            
        except Exception as e:
            raise ImageProcessingError(f"Error detectando problemas de salud: {str(e)}")
    
    async def _analyze_infrared(self, image_array: np.ndarray, image_bytes: bytes, image_id: str) -> ImageAnalysis:
        """Análisis especializado para imágenes infrarrojas"""
        # Convertir a escala de grises para análisis infrarrojo
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        
        # Detectar zonas de baja reflectancia (estrés hídrico)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Calcular proporción de zonas estresadas
        stress_pixels = cv2.countNonZero(binary)
        total_pixels = gray.shape[0] * gray.shape[1]
        stress_ratio = stress_pixels / total_pixels
        
        # Determinar estado de salud
        if stress_ratio > settings.WATER_STRESS_THRESHOLD:
            health_status = HealthStatus.STRESS_WATER
            confidence = min(0.9, stress_ratio * 2)
            recommendations = [
                "Aumentar la frecuencia de riego inmediatamente",
                "Verificar el sistema de riego por goteo",
                "Aplicar mantillo para conservar humedad",
                "Monitorear durante los próximos 3-5 días"
            ]
        else:
            health_status = HealthStatus.HEALTHY
            confidence = 0.8
            recommendations = ["Planta en buen estado de hidratación"]
        
        detections = [{
            "type": "water_stress_analysis",
            "stress_ratio": stress_ratio,
            "threshold_used": settings.WATER_STRESS_THRESHOLD,
            "description": f"Análisis de estrés hídrico: {stress_ratio:.2%}"
        }]
        
        return ImageAnalysis(
            image_id=image_id,
            analysis_type=AnalysisType.INFRARED,
            plant_type=PlantType.ENDemICA_MEXICANA,
            health_status=health_status,
            confidence=confidence,
            detections=detections,
            recommendations=recommendations
        )
    
    async def _analyze_rgb(self, image_array: np.ndarray, image_bytes: bytes, image_id: str) -> ImageAnalysis:
        """Análisis especializado para imágenes RGB"""
        # Usar YOLO para detección de plagas y enfermedades
        results = self.rgb_model(image_array)
        detections = []
        total_confidence = 0
        
        for result in results[0].boxes.data.tolist():
            x1, y1, x2, y2, confidence, class_id = result
            if confidence > settings.MODEL_CONFIDENCE_THRESHOLD:
                detections.append({
                    "type": "pest_detection",
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                    "class_name": self.rgb_model.names[int(class_id)]
                })
                total_confidence += confidence
        
        # Análisis de salud general
        if len(detections) > 0:
            health_status = HealthStatus.PEST_DETECTION
            avg_confidence = total_confidence / len(detections)
            recommendations = [
                "Aplicar pesticida orgánico inmediatamente",
                "Aislar planta si es posible",
                "Monitorear plantas vecinas",
                "Revisar condiciones de ventilación"
            ]
        else:
            health_status = HealthStatus.HEALTHY
            avg_confidence = 0.8
            recommendations = ["No se detectaron plagas visibles"]
        
        return ImageAnalysis(
            image_id=image_id,
            analysis_type=AnalysisType.RGB,
            plant_type=PlantType.DESCONOCIDA,
            health_status=health_status,
            confidence=avg_confidence,
            detections=detections,
            recommendations=recommendations
        )
    
    def _decode_base64(self, image_b64: str) -> bytes:
        """Decodifica imagen base64 a bytes"""
        try:
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[1]
            return base64.b64decode(image_b64)
        except Exception as e:
            raise UnsupportedImageFormat(f"Error decodificando base64: {str(e)}")
    
    def _bytes_to_array(self, image_bytes: bytes) -> np.ndarray:
        """Convierte bytes a array numpy/OpenCV"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise UnsupportedImageFormat(f"Error convirtiendo imagen: {str(e)}")
    
    def _detect_maize_pattern(self, image_array: np.ndarray) -> bool:
        """Detección simple de patrón de maíz"""
        hsv = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
        yellow_mask = cv2.inRange(hsv, (20, 100, 100), (30, 255, 255))
        yellow_ratio = cv2.countNonZero(yellow_mask) / (image_array.shape[0] * image_array.shape[1])
        return yellow_ratio > 0.15
    
    def _detect_avocado_pattern(self, image_array: np.ndarray) -> bool:
        """Detección simple de patrón de aguacate"""
        hsv = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
        green_dark_mask = cv2.inRange(hsv, (40, 50, 50), (70, 200, 150))
        return cv2.countNonZero(green_dark_mask) > 10000
    
    def _detect_water_stress(self, image_array: np.ndarray) -> bool:
        """Detecta signos de estrés hídrico en RGB"""
        hsv = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
        brown_mask = cv2.inRange(hsv, (10, 50, 50), (20, 255, 200))
        brown_ratio = cv2.countNonZero(brown_mask) / (image_array.shape[0] * image_array.shape[1])
        return brown_ratio > 0.1
    
    def _detect_nutrient_deficiency(self, image_array: np.ndarray) -> bool:
        """Detecta signos de deficiencia nutricional"""
        hsv = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
        yellow_green_mask = cv2.inRange(hsv, (25, 50, 50), (35, 255, 200))
        yellow_ratio = cv2.countNonZero(yellow_green_mask) / (image_array.shape[0] * image_array.shape[1])
        return 0.05 < yellow_ratio < 0.2