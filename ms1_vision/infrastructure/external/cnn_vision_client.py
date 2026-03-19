import io
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

try:
    import tflite_runtime.interpreter as tflite
except Exception:
    tflite = None

# Module-level interpreter cache to ensure a model is loaded once per process
_INTERPRETERS: Dict[str, "tflite.Interpreter"] = {}


class CNNVisionClient:
    def __init__(self, model_path: str, labels_path: Optional[str] = None) -> None:
        if tflite is None:
            raise RuntimeError("tflite_runtime is not available in this environment")
        # reuse interpreter if already created for this model path
        interp = _INTERPRETERS.get(model_path)
        if interp is None:
            interp = tflite.Interpreter(model_path=model_path)
            interp.allocate_tensors()
            setattr(interp, "_allocated", True)
            _INTERPRETERS[model_path] = interp
        self.interpreter = interp
        self.labels = self._load_labels(labels_path) if labels_path else {}

    def _load_labels(self, path: str) -> Dict[str, Any]:
        import json
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
        arr = np.asarray(image, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)

    def analyze(self, image_bytes: bytes) -> "VisionOutputModel":
        # Note: intentionally NO threading.Lock; concurrency handled by process workers
        from ms1_vision.domain.schemas import VisionOutputModel

        input_data = self._preprocess(image_bytes)
        input_index = self.interpreter.get_input_details()[0]["index"]
        output_index = self.interpreter.get_output_details()[0]["index"]
        self.interpreter.set_tensor(input_index, input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(output_index)[0]
        pred_idx = int(output.argmax())
        confidence = float(output.max())
        label_info = self.labels.get(str(pred_idx), {})
        result = {
            "species": label_info.get("species"),
            "condition": label_info.get("condition"),
            "severity": label_info.get("severity"),
            "ph_predicted": label_info.get("ph") if "ph" in label_info else None,
            "confidence": confidence,
            "pred_idx": pred_idx,
        }
        return VisionOutputModel.model_validate(result)
