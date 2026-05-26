import os
import json
import sys
from io import BytesIO
from pathlib import Path

# ensure project root is importable
sys.path.insert(0, str(Path.cwd()))

from fastapi.testclient import TestClient
from PIL import Image


def make_image_bytes(size=(224, 224), color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    # prepare fake model and labels
    tmp = Path("/tmp")
    model_path = tmp / "fake_model.tflite"
    labels_path = tmp / "fake_labels.json"
    model_path.write_bytes(b"\x00")
    labels_path.write_text(json.dumps({"0": {"species": "rose", "condition": "healthy", "severity": "low", "ph": 6.5}}))

    # inject dummy Interpreter into module before use
    import importlib

    mod = importlib.import_module("ms1_vision.infrastructure.external.cnn_vision_client")

    class DummyInterpreter:
        def __init__(self, model_path=None):
            self.model_path = model_path

        def allocate_tensors(self):
            return None

        def get_input_details(self):
            return [{"index": 0}]

        def get_output_details(self):
            return [{"index": 0}]

        def set_tensor(self, idx, data):
            pass

        def invoke(self):
            pass

        def get_tensor(self, idx):
            import numpy as np

            return np.array([[0.1, 0.9]])

    setattr(mod, "tflite", type("T", (), {"Interpreter": DummyInterpreter}))

    # ensure env vars point to fake files
    os.environ["CNN_MODEL_PATH"] = str(model_path)
    os.environ["CNN_LABELS_PATH"] = str(labels_path)

    # import app and run test client
    app_mod = importlib.import_module("ms1_vision.app.main")
    client = TestClient(app_mod.app)

    img_bytes = make_image_bytes()
    files = {"file": ("img.png", img_bytes, "image/png")}
    resp = client.post("/api/v1/vision/analyze", files=files)
    print("status", resp.status_code)
    print("json:", resp.json())

    # validate with pydantic DiagnosticModel
    from ms1_vision.domain.schemas import DiagnosticModel

    DiagnosticModel.model_validate(resp.json())
    print("Smoke test OK: response validated against DiagnosticModel")


if __name__ == "__main__":
    main()
