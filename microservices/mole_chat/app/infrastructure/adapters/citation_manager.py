"""
Citation Manager Adapter
Extrae las fuentes reales basadas en el contexto que se inyectó al LLM.
"""
from app.domain.chat import CitationManagerPort
from app.domain.schemas import SourceMetadata

class CitationManager(CitationManagerPort):
    async def extract_sources(self, context: dict) -> list:
        sources = []
        
        # 1. ¿Usó datos de sensores (CAG)?
        cag_data = context.get("telemetria_sensores", "")
        if cag_data and cag_data != "No hay datos de sensores en vivo.":
             sources.append(SourceMetadata(
                autor="Sensores IoT Edge (Redis)",
                url="local://telemetria",
                confianza=0.99
            ))

        # 2. ¿Usó manuales locales PDF (RAG)?
        local_data = context.get("base_conocimiento_local", "")
        if local_data and local_data != "No hay documentos locales relevantes.":
            sources.append(SourceMetadata(
                autor="Base de Conocimiento Mole.AI",
                url="local://pgvector",
                confianza=0.85
            ))
            
        # 3. ¿Usó la API externa?
        trefle_data = context.get("base_conocimiento_externa", "")
        if trefle_data and "Trefle.io" in trefle_data:
            sources.append(SourceMetadata(
                autor="Trefle.io Botanical API",
                url="https://trefle.io",
                confianza=0.90
            ))

        return sources
