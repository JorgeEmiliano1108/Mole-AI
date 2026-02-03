"""Adapter Outbound: Vector Store (FAISS)"""

import logging
import os
from typing import List
from pathlib import Path
import json

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from ...domain.models import RAGChunk
from ...domain.ports import VectorStorePort

logger = logging.getLogger(__name__)


class FAISSVectorStoreAdapter(VectorStorePort):
    """Implementación de VectorStorePort usando FAISS"""
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model
        self.embeddings = None  # ⚡ LAZY LOAD - No descargar embeddings en startup
        self.vector_store_path = Path(os.getenv("VECTOR_DB_PATH", "storage/vectors"))
        self.metadata_path = self.vector_store_path / "metadata.json"
        self.vector_store = None
        self.metadata = {}
        
        # Crear directorios
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ FAISS Vector Store ready (lazy embeddings)")
    
    async def _ensure_embeddings(self):
        """Lazy load embeddings on first use"""
        if self.embeddings is None:
            logger.debug("⚡ Inicializando embeddings en primera solicitud...")
            import asyncio
            self.embeddings = await asyncio.to_thread(
                HuggingFaceEmbeddings,
                model_name=self.embedding_model
            )
    
    async def add_documents(self, documents: List[str], metadata: List[dict]) -> int:
        """Agrega documentos al vector store"""
        try:
            import asyncio
            
            # Lazy load embeddings si necesario
            await self._ensure_embeddings()
            
            # Crear chunks con metadatos
            from langchain.schema import Document
            docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(documents, metadata)
            ]
            
            # Vectorizar
            if self.vector_store is None:
                self.vector_store = await asyncio.to_thread(
                    FAISS.from_documents,
                    docs,
                    self.embeddings
                )
            else:
                await asyncio.to_thread(
                    self.vector_store.add_documents,
                    docs
                )
            
            # Registrar metadata
            if metadata and len(metadata) > 0:
                source = metadata[0].get("source", "unknown")
                self.metadata[source] = {
                    "chunks": len(documents),
                    "category": metadata[0].get("category", "general"),
                    "timestamp": str(__import__('datetime').datetime.now().isoformat())
                }
            
            # Persistir
            self._save_vectorstore()
            
            return len(documents)
            
        except Exception as e:
            logger.error(f"❌ Error en add_documents: {str(e)}")
            raise
    
    async def retrieve(self, query: str, top_k: int = 3) -> List[RAGChunk]:
        """Recupera chunks similares"""
        try:
            import asyncio
            
            # Lazy load embeddings si necesario
            await self._ensure_embeddings()
            
            if self.vector_store is None:
                logger.warning("⚠️ Vector store vacío")
                return []
            
            # Similarity search
            results = await asyncio.to_thread(
                self.vector_store.similarity_search,
                query,
                k=top_k
            )
            
            # Convertir a RAGChunk
            chunks = [
                RAGChunk(
                    contenido=doc.page_content,
                    fuente=doc.metadata.get("source", "Unknown"),
                    confianza=0.8  # Placeholder
                )
                for doc in results
            ]
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error en retrieve: {str(e)}")
            return []
    
    async def get_sources(self) -> List[dict]:
        """Retorna fuentes cargadas"""
        sources = []
        for pdf_name, info in self.metadata.items():
            sources.append({
                "name": pdf_name,
                "chunks": info.get("chunks", 0),
                "category": info.get("category", "general")
            })
        return sources
    
    def _load_vectorstore(self):
        """Carga vector store desde disco"""
        try:
            index_path = self.vector_store_path / "faiss_index"
            
            if index_path.exists():
                self.vector_store = FAISS.load_local(
                    str(index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"📥 Vector store cargado")
            
            if self.metadata_path.exists():
                with open(self.metadata_path, "r") as f:
                    self.metadata = json.load(f)
                    
        except Exception as e:
            logger.warning(f"⚠️ No hay vector store previo: {str(e)}")
    
    def _save_vectorstore(self):
        """Persiste vector store"""
        try:
            if self.vector_store is None:
                return
            
            index_path = self.vector_store_path / "faiss_index"
            self.vector_store.save_local(str(index_path))
            
            with open(self.metadata_path, "w") as f:
                json.dump(self.metadata, f)
                
        except Exception as e:
            logger.error(f"❌ Error guardando vector store: {str(e)}")
