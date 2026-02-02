import os
import json
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from ...ports.input import VectorDBPort, KnowledgeBasePort
from ...domain.models import KnowledgeDocument
from ...domain.exceptions import VectorDBError, KnowledgeBaseError
from ...config.settings import settings

class ChromaDBAdapter(VectorDBPort):
    """Adaptador para ChromaDB - Base de datos vectorial"""
    
    def __init__(self):
        self.collection_name = settings.COLLECTION_NAME
        self.storage_path = settings.VECTOR_DB_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.storage_path)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Base de conocimiento Mole AI"}
            )
        except ImportError:
            raise VectorDBError("ChromaDB no está instalado. Instalar con: pip install chromadb")
        except Exception as e:
            raise VectorDBError(f"Error inicializando ChromaDB: {str(e)}")
    
    async def add_document(self, doc_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Agrega documento con su embedding"""
        try:
            # Validar embedding
            if not embedding:
                raise VectorDBError("Embedding vacío")
            
            # Agregar a ChromaDB
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            return True
        except Exception as e:
            raise VectorDBError(f"Error agregando documento {doc_id}: {str(e)}")
    
    async def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Busca documentos similares por embedding con fallback inteligente"""
        try:
            if not query_embedding:
                raise VectorDBError("Query embedding vacío")
            
            # Buscar en ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Formatear resultados
            similar_docs = []
            for i in range(len(results["ids"][0])):
                similarity = 1 - results["distances"][0][i]  # Convertir distancia a similitud
                similar_docs.append({
                    "doc_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": similarity
                })
            
            # Fallback: si no hay resultados o baja similitud, búsqueda más amplia
            if not similar_docs or all(doc["similarity"] < 0.3 for doc in similar_docs):
                fallback_results = await self._fallback_search(query_embedding, limit * 2)
                if fallback_results:
                    similar_docs = fallback_results
            
            return similar_docs
        except Exception as e:
            raise VectorDBError(f"Error buscando documentos similares: {str(e)}")
    
    async def _fallback_search(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda de fallback con criterios más relajados"""
        try:
            # Búsqueda con mayor límite y sin filtrado de similitud estricto
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Si aún no hay resultados, devolver documentos aleatorios/relevantes
            if not results["ids"][0]:
                return await self._get_fallback_documents(limit)
            
            # Formatear con metadata de fallback
            fallback_docs = []
            for i in range(len(results["ids"][0])):
                similarity = 1 - results["distances"][0][i]
                fallback_docs.append({
                    "doc_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": {
                        **results["metadatas"][0][i],
                        "fallback": True,
                        "fallback_reason": "low_similarity"
                    },
                    "similarity": similarity
                })
            
            return fallback_docs[:5]  # Limitar a 5 resultados de fallback
            
        except Exception:
            # Fallback final: documentos generales
            return await self._get_fallback_documents(5)
    
    async def _get_fallback_documents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene documentos de fallback cuando no hay resultados vectoriales"""
        try:
            # Obtener todos los documentos (hasta el límite)
            all_results = self.collection.get(
                limit=limit,
                include=["documents", "metadatas", "ids"]
            )
            
            if not all_results["ids"]:
                return []
            
            fallback_docs = []
            for i in range(len(all_results["ids"])):
                fallback_docs.append({
                    "doc_id": all_results["ids"][i],
                    "content": all_results["documents"][i],
                    "metadata": {
                        **all_results["metadatas"][i],
                        "fallback": True,
                        "fallback_reason": "no_vector_results"
                    },
                    "similarity": 0.0  # Sin similitud calculada
                })
            
            return fallback_docs
            
        except Exception as e:
            # Último recurso: responder con documentos genéricos
            return [{
                "doc_id": "fallback_generic",
                "content": "No se encontró información específica en la base de conocimientos. Se recomienda consultar con un experto agrónomo para obtener información detallada sobre este caso particular.",
                "metadata": {
                    "fallback": True,
                    "fallback_reason": "database_error",
                    "source": "system_fallback"
                },
                "similarity": 0.0
            }]
    
    async def delete_document(self, doc_id: str) -> bool:
        """Elimina documento por ID"""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            raise VectorDBError(f"Error eliminando documento {doc_id}: {str(e)}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la colección"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "storage_path": self.storage_path
            }
        except Exception as e:
            raise VectorDBError(f"Error obteniendo estadísticas: {str(e)}")

class SimpleKnowledgeBaseAdapter(KnowledgeBasePort):
    """Adaptador simple para base de conocimiento usando ChromaDB"""
    
    def __init__(self, vector_db: VectorDBPort, llm_provider):
        self.vector_db = vector_db
        self.llm_provider = llm_provider
        self.storage_path = settings.DOCUMENT_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Archivo de metadatos
        self.metadata_file = os.path.join(self.storage_path, "documents_metadata.json")
        self._init_metadata_file()
    
    def _init_metadata_file(self):
        """Inicializa archivo de metadatos"""
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)
    
    async def ingest_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Ingresa documento a la base de conocimiento"""
        try:
            # Generar ID único
            doc_id = metadata.get("doc_id") or str(uuid.uuid4())
            
            # Generar embedding
            embedding = await self.llm_provider.get_embedding(content)
            
            # Guardar documento en archivo
            doc_file = os.path.join(self.storage_path, f"{doc_id}.txt")
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Agregar a base vectorial
            success = await self.vector_db.add_document(doc_id, content, embedding, metadata)
            
            if success:
                # Actualizar metadatos
                await self._update_metadata(doc_id, metadata)
            
            return success
        except Exception as e:
            raise KnowledgeBaseError(f"Error ingiriendo documento: {str(e)}")
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca información relevante en la base de conocimiento"""
        try:
            # Generar embedding de la consulta
            query_embedding = await self.llm_provider.get_embedding(query)
            
            # Buscar documentos similares
            results = await self.vector_db.search_similar(query_embedding, limit)
            
            # Filtrar por umbral de similitud
            filtered_results = [
                result for result in results
                if result["similarity"] >= settings.RAG_SIMILARITY_THRESHOLD
            ]
            
            return filtered_results
        except Exception as e:
            raise KnowledgeBaseError(f"Error buscando conocimiento: {str(e)}")
    
    async def delete_document(self, doc_id: str) -> bool:
        """Elimina documento de la base de conocimiento"""
        try:
            # Eliminar de base vectorial
            vector_success = await self.vector_db.delete_document(doc_id)
            
            # Eliminar archivo
            doc_file = os.path.join(self.storage_path, f"{doc_id}.txt")
            if os.path.exists(doc_file):
                os.remove(doc_file)
            
            # Actualizar metadatos
            await self._remove_metadata(doc_id)
            
            return vector_success
        except Exception as e:
            raise KnowledgeBaseError(f"Error eliminando documento: {str(e)}")
    
    async def get_document_content(self, doc_id: str) -> str:
        """Obtiene contenido de un documento"""
        try:
            doc_file = os.path.join(self.storage_path, f"{doc_id}.txt")
            if not os.path.exists(doc_file):
                raise FileNotFoundError(f"Documento {doc_id} no encontrado")
            
            with open(doc_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise KnowledgeBaseError(f"Error leyendo documento: {str(e)}")
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """Lista todos los documentos en la base de conocimiento"""
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            return [
                {"doc_id": doc_id, **data}
                for doc_id, data in metadata.items()
            ]
        except Exception as e:
            raise KnowledgeBaseError(f"Error listando documentos: {str(e)}")
    
    async def _update_metadata(self, doc_id: str, metadata: Dict[str, Any]):
        """Actualiza metadatos de un documento"""
        try:
            with open(self.metadata_file, 'r') as f:
                all_metadata = json.load(f)
            
            metadata["updated_at"] = datetime.now().isoformat()
            all_metadata[doc_id] = metadata
            
            with open(self.metadata_file, 'w') as f:
                json.dump(all_metadata, f, indent=2)
        except Exception as e:
            raise KnowledgeBaseError(f"Error actualizando metadatos: {str(e)}")
    
    async def _remove_metadata(self, doc_id: str):
        """Elimina metadatos de un documento"""
        try:
            with open(self.metadata_file, 'r') as f:
                all_metadata = json.load(f)
            
            if doc_id in all_metadata:
                del all_metadata[doc_id]
                
                with open(self.metadata_file, 'w') as f:
                    json.dump(all_metadata, f, indent=2)
        except Exception as e:
            raise KnowledgeBaseError(f"Error eliminando metadatos: {str(e)}")