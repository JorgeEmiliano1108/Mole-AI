from src.application.ports.output import VisionService, VectorRepository
from src.domain.prompts import PromptTemplates
from src.domain.models import AnalisisVision

class PlantVisionUseCase:
    def __init__(self, vision_service: VisionService, db: VectorRepository):
        self.vision = vision_service
        self.db = db

    async def run(self, image_bytes: bytes, plant_context: str = "") -> AnalisisVision:
        """
        Analiza una imagen de planta usando visión por computadora y RAG.
        
        Args:
            image_bytes: Bytes de la imagen de la planta
            plant_context: Información adicional sobre la planta (opcional)
        
        Returns:
            AnalisisVision con diagnóstico y recomendaciones
        """
        
        # 1. Obtener descripción visual del modelo de visión
        image_description = await self.vision.analyze_image(image_bytes)
        
        if not image_description:
            return AnalisisVision(
                imagen_id="unknown",
                diagnostico="No se pudo analizar la imagen",
                recomendaciones=["Intenta con mejor iluminación o ángulo"],
                confianza=0.0
            )
        
        # 2. Buscar contexto relevante en la base de conocimiento
        query_vector = await self.vision.get_embedding(image_description)
        context_chunks = []
        
        if query_vector:
            context_chunks = await self.db.search_similarity(query_vector, limit=3)
        
        context_text = "\n---\n".join(context_chunks) if context_chunks else ""
        
        # 3. Generar prompt con descripción y contexto
        full_prompt = PromptTemplates.get_vision_prompt(
            image_description, 
            f"{plant_context}\n\nCONTEXTO DE CONOCIMIENTO:\n{context_text}"
        )
        
        # 4. Obtener análisis detallado del LLM
        analysis = await self.vision.generate_analysis(full_prompt)
        
        # 5. Parsear respuesta y crear objeto de análisis
        return AnalisisVision(
            imagen_id=f"img_{hash(image_bytes)}",
            tipo_planta=self._extract_plant_type(analysis),
            diagnostico=analysis,
            recomendaciones=self._extract_recommendations(analysis),
            confianza=0.85
        )
    
    def _extract_plant_type(self, analysis: str) -> str:
        if "chile" in analysis.lower():
            return "Chile (Capsicum)"
        elif "maíz" in analysis.lower() or "maiz" in analysis.lower():
            return "Maíz (Zea mays)"
        elif "aguacate" in analysis.lower():
            return "Aguacate (Persea americana)"
        elif "tomate" in analysis.lower():
            return "Tomate (Solanum lycopersicum)"
        return "Planta no identificada"
    
    def _extract_recommendations(self, analysis: str) -> list:
        recomendaciones = []
        lines = analysis.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['recomienda', 'sugiere', 'aplica', 'usa']):
                recomendaciones.append(line.strip())
        return recomendaciones[:5] if recomendaciones else ["Consulta con un especialista para tratamiento específico"]