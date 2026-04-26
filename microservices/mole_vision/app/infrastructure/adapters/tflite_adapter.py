"""
Infrastructure Layer - Adapter: TFLite Vision
Arquitectura Hexagonal - Implementa VisionClientPort
Async - run_in_threadpool para CPU-bound con Timeout Anti-DoS
"""
import io
import json
import asyncio
from typing import Dict, Optional
import numpy as np
from PIL import Image
import structlog
from fastapi import HTTPException

from app.application.ports import VisionClientPort
from app.domain.entities import DiagnosticResult, SeverityLevel, ConditionCategory
from app.core.config import settings

logger = structlog.get_logger()

try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
except ImportError:
    TFLITE_AVAILABLE = False
    logger.warning("tflite_runtime no está disponible. Verifique su entorno Docker.")

class TFLiteVisionAdapter(VisionClientPort):
    """
    Adaptador para inferencia con TensorFlow Lite.
    Implementa VisionClientPort de forma asíncrona.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        labels_path: Optional[str] = None,
        num_threads: Optional[int] = None,
    ):
        if not TFLITE_AVAILABLE:
            raise RuntimeError("tflite_runtime not available")
        
        self.model_path = model_path or settings.CNN_MODEL_PATH
        self.labels_path = labels_path or settings.CNN_LABELS_PATH
        self.num_threads = num_threads or settings.CNN_NUM_THREADS
        self.timeout_sec = settings.INFERENCE_TIMEOUT_SECONDS
        
        self._interpreter = tflite.Interpreter(
            model_path=self.model_path,
            num_threads=self.num_threads,
        )
        self._interpreter.allocate_tensors()
        
        self._input_index = self._interpreter.get_input_details()[0]["index"]
        self._output_index = self._interpreter.get_output_details()[0]["index"]
        
        self._labels = self._load_labels()
        
        logger.info("tflite_model_loaded", model_path=self.model_path)
    
    def _load_labels(self) -> Dict:
        if not self.labels_path:
            return {}
        try:
            with open(self.labels_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("labels_load_failed", error=str(e))
            return {}
    
    def is_ready(self) -> bool:
        return self._interpreter is not None
    
    async def analyze(self, image_bytes: bytes) -> DiagnosticResult:
        """
        Ejecuta la inferencia de forma asíncrona.
        Mecanismo de Timeout explícito
        """
        from starlette.concurrency import run_in_threadpool
        try:
            # Ejecutamos la tarea pesada con un límite de tiempo
            return await asyncio.wait_for(
                run_in_threadpool(self._do_inference, image_bytes),
                timeout=self.timeout_sec
            )
        except asyncio.TimeoutError:
            logger.error("inference_timeout", timeout=self.timeout_sec)
            raise HTTPException(
                status_code=503, 
                detail={"title": "Service Unavailable", "message": "Inference Timeout"}
            )
    
    def _do_inference(self, image_bytes: bytes) -> DiagnosticResult:
        """Lógica síncrona bloqueante de inferencia TFLite con Umbral de Confianza."""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
        input_data = np.asarray(img, dtype=np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)
        
        self._interpreter.set_tensor(self._input_index, input_data)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_index)[0]
        
        pred_idx = int(output.argmax())
        confidence = float(output.max())
        
        CONFIDENCE_THRESHOLD = 0.80  
        
        if confidence < CONFIDENCE_THRESHOLD:
            # Si el modelo duda, forzamos el resultado a Desconocido
            return DiagnosticResult(
                plant_id="",  
                species="Planta u Objeto Desconocido",
                condition="No se pudo analizar con certeza",
                condition_category=ConditionCategory.UNKNOWN,
                severity=SeverityLevel.MEDIUM,
                confidence=confidence, 
                ph_predicted=None,
            )
            
        label_info = self._labels.get(str(pred_idx), {})
        if isinstance(label_info, str):
            label_info = {
                "species": "Desconocida",
                "condition": label_info,
                "severity": "medium",
            }
        
        species = label_info.get("species", "Desconocida")
        condition = label_info.get("condition", "No identificada")
        
        severity_str = label_info.get("severity", "medium").lower()
        try:
            severity = SeverityLevel(severity_str)
        except ValueError:
            severity = SeverityLevel.MEDIUM
            
        condition_category = self._map_condition_to_category(condition)
        
        raw_ph = label_info.get("ph")
        ph_predicted: Optional[float] = None
        if raw_ph is not None:
            try:
                ph_predicted = float(raw_ph)
            except (ValueError, TypeError):
                ph_predicted = None
        
        return DiagnosticResult(
            plant_id="",  
            species=species,
            condition=condition,
            condition_category=condition_category,
            severity=severity,
            confidence=confidence,
            ph_predicted=ph_predicted,
        )
    
    def _map_condition_to_category(self, condition: str) -> ConditionCategory:
        condition_lower = condition.lower()
        if "saludable" in condition_lower or "healthy" in condition_lower:
            return ConditionCategory.HEALTHY
        elif "enfermedad" in condition_lower or "disease" in condition_lower:
            return ConditionCategory.DISEASE
        elif "deficiencia" in condition_lower or "deficiency" in condition_lower:
            return ConditionCategory.NUTRIENT_DEFICIENCY
        elif "plaga" in condition_lower or "pest" in condition_lower:
            return ConditionCategory.PEST
        elif "estrés" in condition_lower or "stress" in condition_lower:
            return ConditionCategory.ENVIRONMENTAL_STRESS
        return ConditionCategory.UNKNOWN