import os
from ms1_vision.infrastructure.external.cnn_vision_client import CNNVisionClient, _INTERPRETERS


def test_singleton_interpreter_used(tmp_path, monkeypatch):
    # create fake model file path
    model_path = str(tmp_path / "fake.tflite")
    open(model_path, "wb").close()

    # monkeypatch tflite interpreter to a lightweight dummy with allocate_tensors
    class DummyInterpreter:
        def __init__(self, model_path=None):
            self.model_path = model_path
            self.allocated = False

        def allocate_tensors(self):
            self.allocated = True

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

    # replace tflite runtime Interpreter used by the module
    import ms1_vision.infrastructure.external.cnn_vision_client as mod

    monkeypatch.setattr(mod, "tflite", type("T", (), {"Interpreter": DummyInterpreter}))
    # clear any existing interpreters
    _INTERPRETERS.clear()

    c1 = CNNVisionClient(model_path)
    c2 = CNNVisionClient(model_path)
    assert c1.interpreter is c2.interpreter
