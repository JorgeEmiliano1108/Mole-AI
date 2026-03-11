"""Domain Services: Citation Manager for Verifiable Sources"""

import logging
from typing import Dict, List
from datetime import datetime
from urllib.parse import quote

from domain.models import RAGChunk

logger = logging.getLogger(__name__)


class CitationManager:
    """Maneja formato y verificación de citas en las respuestas RAG"""
    
    def __init__(self):
        self.citation_cache = {}  # Cache para evitar verificaciones repetidas
        
    def format_citation(self, chunk: RAGChunk) -> Dict:
        """Helper to get source string from chunk metadata"""
        """
        Formatea una cita verificable con todos los metadatos necesarios
        
        Args:
            chunk: RAGChunk con información de la fuente
            
        Returns:
            Dict con cita formateada y verificable
        """
        try:
            source = chunk.metadata.get('source', '') if chunk else ''
            if not chunk or not source:
                return self._create_unknown_citation()
            
            source_type = self._identify_source_type(source)
            
            if source_type == "GBIF":
                return self._format_gbif_citation(chunk)
            elif source_type == "USDA":
                return self._format_usda_citation(chunk)
            elif source_type == "PDF":
                return self._format_pdf_citation(chunk)
            elif source_type == "CONABIO":
                return self._format_conabio_citation(chunk)
            else:
                return self._format_generic_citation(chunk)
                
        except Exception as e:
            logger.error(f"❌ Error formateando cita: {str(e)}")
            return self._create_error_citation(chunk.metadata.get('source', 'unknown'), str(e))
    
    def _identify_source_type(self, source: str) -> str:
        """Identifica el tipo de fuente"""
        if source.startswith("GBIF:"):
            return "GBIF"
        elif source.startswith("USDA:"):
            return "USDA"
        elif source.startswith("PDF:"):
            return "PDF"
        elif source.startswith("CONABIO:"):
            return "CONABIO"
        elif source.startswith("test_plants"):
            return "LOCAL_TEST"
        else:
            return "UNKNOWN"
    
    def _format_gbif_citation(self, chunk: RAGChunk) -> Dict:
        """Formatea cita GBIF verificable"""
        try:
            source = chunk.metadata.get('source', '')
            gbif_key = source.split(":")[1]
            
            # Extraer metadata del chunk si existen
            metadata = getattr(chunk, 'metadata', {})
            
            return {
                "type": "GBIF",
                "id": gbif_key,
                "title": metadata.get("canonical_name", f"GBIF Species {gbif_key}"),
                "url": f"https://www.gbif.org/species/{gbif_key}",
                "api_url": f"https://api.gbif.org/v1/species/{gbif_key}",
                "verification": "Direct link to live GBIF database",
                "confidence": chunk.score,
                "last_verified": datetime.now().isoformat(),
                "data_quality": metadata.get("data_quality", "unknown"),
                "taxonomic_status": metadata.get("taxonomic_status", "unknown"),
                "canonical_name": metadata.get("canonical_name"),
                "family": metadata.get("family"),
                "genus": metadata.get("genus"),
                "short_citation": f"[GBIF:{gbif_key}](https://www.gbif.org/species/{gbif_key})",
                "full_citation": f"Global Biodiversity Information Facility (GBIF). Species ID: {gbif_key}. URL: https://www.gbif.org/species/{gbif_key}. Accessed: {datetime.now().strftime('%Y-%m-%d')}."
            }
        except Exception as e:
            return self._create_error_citation(chunk.metadata.get('source', 'unknown'), f"GBIF formatting error: {str(e)}")
    
    def _format_usda_citation(self, chunk: RAGChunk) -> Dict:
        """Formatea cita USDA verificable"""
        try:
            source = chunk.metadata.get('source', '')
            usda_symbol = source.split(":")[1]
            
            metadata = getattr(chunk, 'metadata', {})
            
            return {
                "type": "USDA",
                "id": usda_symbol,
                "title": metadata.get("scientific_name", f"USDA Plant {usda_symbol}"),
                "url": f"https://plants.usda.gov/java/profile?symbol={usda_symbol}",
                "api_url": f"https://plants.usda.gov/java/nameSearch?keywordForm={quote(metadata.get('common_name', usda_symbol))}",
                "verification": "Official USDA Plants Database",
                "confidence": chunk.score,
                "last_verified": datetime.now().isoformat(),
                "scientific_name": metadata.get("scientific_name"),
                "common_name": metadata.get("common_name"),
                "symbol": usda_symbol,
                "source_type": "government_official",
                "short_citation": f"[USDA:{usda_symbol}](https://plants.usda.gov/java/profile?symbol={usda_symbol})",
                "full_citation": f"USDA Natural Resources Conservation Service. Plant Profile: {metadata.get('scientific_name', usda_symbol)} (Symbol: {usda_symbol}). URL: https://plants.usda.gov/java/profile?symbol={usda_symbol}. Accessed: {datetime.now().strftime('%Y-%m-%d')}."
            }
        except Exception as e:
            return self._create_error_citation(chunk.metadata.get('source', 'unknown'), f"USDA formatting error: {str(e)}")
    
    def _format_pdf_citation(self, chunk: RAGChunk) -> Dict:
        """Formatea cita de PDF verificable"""
        try:
            source = chunk.metadata.get('source', '')
            pdf_info = source.split(":", 1)[1]
            metadata = getattr(chunk, 'metadata', {})
            
            return {
                "type": "PDF",
                "id": metadata.get("pdf_name", pdf_info),
                "title": metadata.get("title", f"Document: {pdf_info}"),
                "source": metadata.get("source", "Local PDF"),
                "uploaded_by": metadata.get("uploaded_by", "Unknown"),
                "upload_date": metadata.get("timestamp", datetime.now().isoformat()),
                "chunk_index": metadata.get("chunk_index", 0),
                "page_range": metadata.get("page_range", "N/A"),
                "verification": f"Local document chunk {metadata.get('chunk_index', 0)}",
                "confidence": chunk.score,
                "last_verified": datetime.now().isoformat(),
                "file_type": "application/pdf",
                "source_type": "local_document",
                "short_citation": f"[PDF:{pdf_info}]",
                "full_citation": f"Local PDF Document: {metadata.get('title', pdf_info)}. Uploaded by {metadata.get('uploaded_by', 'Unknown')} on {metadata.get('timestamp', datetime.now().strftime('%Y-%m-%d'))}. Chunk {metadata.get('chunk_index', 0)}."
            }
        except Exception as e:
            return self._create_error_citation(chunk.metadata.get('source', 'unknown'), f"PDF formatting error: {str(e)}")
    
    def _format_conabio_citation(self, chunk: RAGChunk) -> Dict:
        """Formatea cita CONABIO verificable"""
        try:
            source = chunk.metadata.get('source', '')
            conabio_id = source.split(":")[1]
            metadata = getattr(chunk, 'metadata', {})
            
            return {
                "type": "CONABIO",
                "id": conabio_id,
                "title": metadata.get("scientific_name", f"CONABIO Species {conabio_id}"),
                "url": f"https://www.conabio.gob.mx/species/{conabio_id}",
                "verification": "Comisión Nacional para el Conocimiento y Uso de la Biodiversidad",
                "confidence": chunk.score,
                "last_verified": datetime.now().isoformat(),
                "scientific_name": metadata.get("scientific_name"),
                "source_type": "government_mexican_official",
                "short_citation": f"[CONABIO:{conabio_id}](https://www.conabio.gob.mx/species/{conabio_id})",
                "full_citation": f"CONABIO - Comisión Nacional para el Conocimiento y Uso de la Biodiversidad. Species ID: {conabio_id}. URL: https://www.conabio.gob.mx/species/{conabio_id}. Accessed: {datetime.now().strftime('%Y-%m-%d')}."
            }
        except Exception as e:
            return self._create_error_citation(chunk.metadata.get('source', 'unknown'), f"CONABIO formatting error: {str(e)}")
    
    def _format_local_test_citation(self, chunk: RAGChunk) -> Dict:
        """Formatea cita de datos de prueba locales"""
        return {
            "type": "LOCAL_TEST",
            "id": "test_plants",
            "title": "Test Knowledge Base - Plant Diseases",
            "source": "Local test data",
            "verification": "Local test knowledge - not for production use",
            "confidence": chunk.score,
            "last_verified": datetime.now().isoformat(),
            "source_type": "test_data",
            "short_citation": "[TEST_DATA]",
            "full_citation": "Local Test Knowledge Base - Plant Diseases. For development and testing only."
        }
    
    def _format_generic_citation(self, chunk: RAGChunk) -> Dict:
        """Formatea cita genérica"""
        return {
            "type": "UNKNOWN",
            "id": chunk.metadata.get('source', 'unknown'),
            "title": f"Source: {chunk.metadata.get('source', 'unknown')}",
            "verification": "Unverified source - verify manually",
            "confidence": chunk.score,
            "last_verified": datetime.now().isoformat(),
            "source_type": "unverified",
            "short_citation": f"[{chunk.metadata.get('source', 'unknown')}]",
            "full_citation": f"Source: {chunk.metadata.get('source', 'unknown')}. Confidence: {chunk.score}. Please verify source manually."
        }
    
    def _create_unknown_citation(self) -> Dict:
        """Crea cita para fuente desconocida"""
        return {
            "type": "UNKNOWN",
            "id": "unknown",
            "title": "Unknown Source",
            "verification": "Source information not available",
            "confidence": 0.0,
            "last_verified": datetime.now().isoformat(),
            "source_type": "unknown",
            "short_citation": "[UNKNOWN_SOURCE]",
            "full_citation": "Unknown source - citation information not available."
        }
    
    def _create_error_citation(self, fuente: str, error: str) -> Dict:
        """Crea cita con información de error"""
        return {
            "type": "ERROR",
            "id": fuente,
            "title": f"Citation Error - {fuente}",
            "verification": f"Citation formatting failed: {error}",
            "confidence": 0.0,
            "last_verified": datetime.now().isoformat(),
            "error": error,
            "source_type": "error",
            "short_citation": f"[ERROR:{fuente}]",
            "full_citation": f"CITATION ERROR for source {fuente}: {error}"
        }
    
    def format_response_citations(self, chunks: List[RAGChunk]) -> List[Dict]:
        """
        Formatea todas las citas para una respuesta RAG
        
        Args:
            chunks: Lista de RAGChunks recuperados
            
        Returns:
            Lista de citas formateadas
        """
        citations = []
        
        for chunk in chunks:
            citation = self.format_citation(chunk)
            citations.append(citation)
            
        logger.info(f"📚 Formateadas {len(citations)} citas")
        return citations
    
    def create_bibliography_section(self, chunks: List[RAGChunk]) -> str:
        """
        Crea una sección de bibliografía formateada
        
        Args:
            chunks: Lista de RAGChunks recuperados
            
        Returns:
            String con bibliografía formateada
        """
        if not chunks:
            return "\n\n**Fuentes:** No se encontraron fuentes verificables.\n"
        
        citations = self.format_response_citations(chunks)
        bib_lines = ["\n\n**Fuentes Consultadas:**\n"]
        
        for i, citation in enumerate(citations, 1):
            bib_lines.append(f"\n{i}. **{citation['title']}**\n")
            bib_lines.append(f"   - Tipo: {citation['type']}\n")
            bib_lines.append(f"   - URL: {citation['url'] if 'url' in citation else 'N/A'}\n")
            bib_lines.append(f"   - Confianza: {citation['confidence']:.2f}\n")
            bib_lines.append(f"   - Verificación: {citation['verification']}\n")
            
            # Agregar información específica por tipo
            if citation['type'] == 'GBIF' and 'family' in citation:
                bib_lines.append(f"   - Familia: {citation['family']}\n")
            elif citation['type'] == 'USDA' and 'scientific_name' in citation:
                bib_lines.append(f"   - Nombre Científico: {citation['scientific_name']}\n")
        
        return "".join(bib_lines)
    
    def verify_citation_url(self, url: str) -> Dict:
        """
        Verifica que una URL de cita sea accesible
        
        Args:
            url: URL a verificar
            
        Returns:
            Dict con resultado de verificación
        """
        try:
            import httpx
            
            with httpx.Client(timeout=10.0) as client:
                response = client.head(url)
                
                return {
                    "url": url,
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "content_type": response.headers.get("content-type", "unknown"),
                    "verified_at": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "url": url,
                "accessible": False,
                "error": str(e),
                "verified_at": datetime.now().isoformat()
            }