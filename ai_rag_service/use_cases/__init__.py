"""Use Cases del RAG Service"""

import logging
from typing import List
from ..domain.models import DiagnoseRequest, FinalDiagnosis, RAGChunk
from ..domain.ports import VectorStorePort, ReasoningModelPort
from ..domain.exceptions import RAGRetrievalException, DiagnoseException

logger = logging.getLogger(__name__)


class UploadPDFUseCase:
    """Use case: Ingestar PDF dinámicamente"""
    
    def __init__(self, vector_store: VectorStorePort):
        self.vector_store = vector_store
    
    async def execute(self, documents: List[str], metadata: dict) -> dict:
        """
        Sube documentos al vector store
        
        Args:
            documents: Lista de textos
            metadata: Metadatos del PDF
            
        Returns:
            Dict con resultado
        """
        try:
            logger.info(f"📤 Subiendo {len(documents)} chunks...")
            chunk_count = await self.vector_store.add_documents(
                documents,
                [metadata] * len(documents)
            )
            logger.info(f"✅ {chunk_count} chunks agregados")
            return {"status": "success", "chunks": chunk_count}
        except Exception as e:
            logger.error(f"❌ Error en upload: {str(e)}")
            raise


class RetrieveKnowledgeUseCase:
    """Use case: Recuperar conocimiento"""
    
    def __init__(self, vector_store: VectorStorePort):
        self.vector_store = vector_store
    
    async def execute(self, query: str, top_k: int = 3) -> List[RAGChunk]:
        """
        Recupera chunks relevantes
        
        Args:
            query: Pregunta/contexto
            top_k: Número de resultados
            
        Returns:
            Lista de chunks
        """
        try:
            logger.info(f"🔍 Retrieving conocimiento para: '{query[:50]}'")
            chunks = await self.vector_store.retrieve(query, top_k)
            logger.info(f"✅ {len(chunks)} chunks recuperados")
            return chunks
        except Exception as e:
            logger.error(f"❌ Error en retrieval: {str(e)}")
            raise RAGRetrievalException(f"Retrieval falló: {str(e)}")


class DiagnoseWithRAGUseCase:
    """Use case: Diagnóstico final con RAG + Phi-3.5"""
    
    def __init__(self, vector_store: VectorStorePort, reasoning_model: ReasoningModelPort):
        self.vector_store = vector_store
        self.reasoning_model = reasoning_model
    
    async def execute(self, request: DiagnoseRequest) -> FinalDiagnosis:
        """
        Ejecuta diagnóstico final
        
        Args:
            request: DiagnoseRequest con vision + sensores
            
        Returns:
            FinalDiagnosis con diagnóstico + recomendaciones
        """
        try:
            logger.info("🧬 Iniciando diagnóstico RAG...")
            
            # Verificar modelo listo
            if not await self.reasoning_model.is_ready():
                raise DiagnoseException("Modelo no listo")
            
            # Construir query
            query = f"Síntomas: {','.join(request.vision_output.sintomas)}. Especie: {request.vision_output.especie_probable}. pH: {request.sensores.ph}"
            
            # Recuperar contexto
            chunks = await self.vector_store.retrieve(query, top_k=3)
            context = "\n".join([f"- {c.fuente}: {c.contenido}" for c in chunks])
            
            # Diagnóstico con Phi-3.5
            logger.info("🧠 Ejecutando Phi-3.5...")
            diagnosis = await self.reasoning_model.diagnose(request, context)
            
            logger.info(f"✅ Diagnóstico final: {diagnosis.diagnostico[:100]}...")
            return diagnosis
            
        except Exception as e:
            logger.error(f"❌ Error en diagnóstico: {str(e)}")
            raise DiagnoseException(f"Diagnóstico falló: {str(e)}")
