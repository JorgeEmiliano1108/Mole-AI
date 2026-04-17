import io
import logging
from typing import Dict, Any, Optional, Union, List, TYPE_CHECKING
from PIL import Image
import numpy as np
import threading

# Importación exclusiva para el análisis estático del IDE (evita errores circulares)
if TYPE_CHECKING:
    from ms1_vision.domain.schemas import VisionOutputModel

# Configuración de trazabilidad para auditoría de IA
logger = logging.getLogger("ms1_vision.cnn_vision_client")

try:
    import tflite_runtime.interpreter as tflite
except Exception:
    tflite = None

# Cache de intérpretes usando Any para evitar falsos positivos en el Linter
_INTERPRETERS: Dict[str, Any] = {}
_INTERPRETER_LOCKS: Dict[str, threading.Lock] = {}

class CNNVisionClient:
    def __init__(self, model_path: str, labels_path: Optional[str] = None) -> None:
        if tflite is None:
            raise RuntimeError("tflite_runtime is not available in this environment")
        
        global _INTERPRETERS
        global _INTERPRETER_LOCKS
        
        interp = _INTERPRETERS.get(model_path)
        if interp is None:
            interp = tflite.Interpreter(model_path=model_path)
            interp.allocate_tensors()
            setattr(interp, "_allocated", True)
            _INTERPRETERS[model_path] = interp
            _INTERPRETER_LOCKS[model_path] = threading.Lock()
            
        self.interpreter = interp
        self._lock = _INTERPRETER_LOCKS.get(model_path) or threading.Lock()
        self.labels = self._load_labels(labels_path) if labels_path else {}

    def _load_labels(self, path: str) -> Union[Dict[str, Any], List[Any]]:
        import json
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as e:
            logger.error("Fallo crítico al cargar labels.json en %s: %s", path, e, exc_info=True)
            return {}

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
        arr = np.asarray(image, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)

    def analyze(self, image_bytes: bytes) -> "VisionOutputModel":
        from ms1_vision.domain.schemas import VisionOutputModel

        input_data = self._preprocess(image_bytes)
        
        with self._lock:
            input_index = self.interpreter.get_input_details()[0]["index"]
            output_index = self.interpreter.get_output_details()[0]["index"]
            self.interpreter.set_tensor(input_index, input_data)
            self.interpreter.invoke()
            output = self.interpreter.get_tensor(output_index)[0]
            
        pred_idx = int(output.argmax())
        confidence = float(output.max())
        
        try:
            if isinstance(self.labels, list):
                label_info = self.labels[pred_idx]
            elif isinstance(self.labels, dict):
                label_info = self.labels.get(str(pred_idx), {})
            else:
                label_info = {}
                
            if isinstance(label_info, str):
                label_info = {
                    "species": "Desconocida", 
                    "condition": label_info, 
                    "severity": "No evaluada"
                }
            elif not isinstance(label_info, dict):
                label_info = {}
                
        except (IndexError, ValueError, TypeError) as e:
            logger.error("Inconsistencia al mapear el tensor con la etiqueta. Index: %s, Error: %s", pred_idx, e, exc_info=True)
            label_info = {}

        result = {
            "species": label_info.get("species", "Desconocida"),
            "condition": label_info.get("condition", "No identificada"),
            "severity": label_info.get("severity", "No evaluada"),
            "ph_predicted": label_info.get("ph") if "ph" in label_info else None,
            "confidence": confidence,
            "pred_idx": pred_idx,
        }
        
        logger.info("Inferencia exitosa. Diagnóstico: %s (Confianza: %.2f)", result["condition"], confidence)
        
        # Desempaquetado universal: Compatible con Pydantic v1 y v2
        return VisionOutputModel(**result)