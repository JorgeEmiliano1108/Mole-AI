"""
Mock Vision Client — simulates CNN inference for local dev / MVP.
Replace with HuggingFace Inference API or TFLite Edge in production.
"""
import random
from domain.ports.diagnostic_ports import VisionClientPort

_MOCK_SPECIES = [
    "Solanum lycopersicum",
    "Capsicum annuum",
    "Lactuca sativa",
    "Cucumis sativus",
    "Phaseolus vulgaris",
]

_MOCK_CONDITIONS = [
    {"condition": "Healthy", "description": "No visible issues detected.", "severity": "low"},
    {"condition": "Nitrogen Deficiency", "description": "Yellowing of lower leaves.", "severity": "medium"},
    {"condition": "Powdery Mildew", "description": "White powdery spots on leaf surface.", "severity": "high"},
    {"condition": "Early Blight", "description": "Concentric ring lesions on leaves.", "severity": "high"},
]


class MockVisionClient(VisionClientPort):
    """Returns deterministic-ish fake CNN results for development."""

    async def analyze(self, image_url: str) -> dict:
        cond = random.choice(_MOCK_CONDITIONS)
        species = random.choice(_MOCK_SPECIES)
        confidence = round(random.uniform(0.70, 0.98), 2)
        ph = round(random.uniform(5.0, 7.5), 2)

        return {
            "species": species,
            "ph": ph,
            "condition": cond["condition"],
            "description": cond["description"],
            "severity": cond["severity"],
            "confidence": confidence,
            "predictions": [cond["condition"]],
            "confidence_scores": [confidence],
            "model_used": "mock-dual-cnn-v0",
        }
