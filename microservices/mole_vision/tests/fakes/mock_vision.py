"""
Mock Vision Adapter – returns a deterministic DiagnosticResult.
Used when the real TFLite model file is missing or when VISION_BACKEND=mock.
"""

import structlog
from app.application.ports import VisionClientPort
from app.domain.entities import DiagnosticResult, ConditionCategory, SeverityLevel

logger = structlog.get_logger()

class MockVisionAdapter(VisionClientPort):
    """Simple mock that pretends every image is a healthy plant.
    Returns a fixed DiagnosticResult with high confidence.
    """

    def __init__(self, *args, **kwargs):
        # No heavy init required
        logger.info("mock_vision_adapter_loaded", reason="model not available or mock mode enabled")

    def is_ready(self) -> bool:
        return True

    async def analyze(self, image_bytes: bytes) -> DiagnosticResult:
        # Return a dummy result – plant_id empty, species unknown, healthy condition
        return DiagnosticResult(
            plant_id="",
            species="Planta Desconocida",
            condition="Saludable",
            condition_category=ConditionCategory.HEALTHY,
            severity=SeverityLevel.LOW,
            confidence=1.0,
            ph_predicted=None,
        )
