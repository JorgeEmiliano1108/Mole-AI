from typing import Any, Dict, Optional


class ExplainPhUseCase:
    def __init__(self, knowledge_repo: Any):
        self.knowledge_repo = knowledge_repo

    async def execute(self, ph_value: float, species: Optional[str] = None) -> Dict[str, Any]:
        # Minimal explainability stub: fetch tolerance and compare
        try:
            tolerance = None
            if species and hasattr(self.knowledge_repo, "get_ph_tolerance"):
                tolerance = await self.knowledge_repo.get_ph_tolerance(species)
        except Exception:
            tolerance = None

        status = "unknown"
        advice = ""
        if tolerance:
            opt = tolerance.get("optimal")
            if opt and abs(ph_value - opt) <= 0.5:
                status = "optimal"
                advice = "pH dentro de rango óptimo"
            else:
                status = "warning"
                advice = "pH fuera de rango óptimo"

        return {"ph": ph_value, "status": status, "advice": advice, "tolerance": tolerance}
