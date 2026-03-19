from ms2_rag_cag_service.domain.chat import CitationManagerPort
from ms2_rag_cag_service.domain.models import SourceMetadata

class CitationManager(CitationManagerPort):
    async def extract_sources(self, context: dict) -> list:
        # Extrae metadatos reales de contexto RAG/CAG
        # Aquí se debe implementar la lógica real de extracción
        # Placeholder: retorna fuente dummy
        return [SourceMetadata(autor="Desconocido", url="https://ejemplo.org", confianza=0.5)]
