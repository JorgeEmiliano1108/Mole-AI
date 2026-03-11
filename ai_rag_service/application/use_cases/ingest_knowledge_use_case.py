"""
Application Layer - Ingest Knowledge Use Case
"""
import logging
from typing import Dict, Any
from domain.ports import VectorStorePort, KnowledgeIngestionPort

logger = logging.getLogger(__name__)

class IngestKnowledgeUseCase:
    """Use case for ingesting knowledge into the RAG system"""
    
    def __init__(self, vector_store: VectorStorePort, ingestion_service: KnowledgeIngestionPort):
        self.vector_store = vector_store
        self.ingestion_service = ingestion_service
    
    async def execute(self, file_content: bytes, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ingest a file (PDF/Text) into the vector store.
        """
        try:
            logger.info(f"Starting ingestion for file: {filename}")
            
            # 1. Parse file
            chunks, chunk_metadatas = await self.ingestion_service.parse_file(file_content, filename)
            
            if not chunks:
                logger.warning(f"No content extracted from {filename}")
                return {"status": "failed", "reason": "No content extracted", "files_processed": 0}
            
            # 2. Enrich metadata
            final_metadatas = []
            for meta in chunk_metadatas:
                combined_meta = {**meta}
                if metadata:
                    combined_meta.update(metadata)
                final_metadatas.append(combined_meta)
            
            # 3. Store in Vector DB
            count = await self.vector_store.add_documents(chunks, final_metadatas)
            
            logger.info(f"Successfully ingested {count} chunks from {filename}")
            
            return {
                "status": "success",
                "filename": filename,
                "chunks_added": count,
                "category": metadata.get("category", "general") if metadata else "general"
            }
            
        except Exception as e:
            logger.error(f"Error ingesting knowledge: {str(e)}")
            raise
