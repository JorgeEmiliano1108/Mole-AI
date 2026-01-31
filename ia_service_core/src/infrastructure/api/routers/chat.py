from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import numpy as np
from src.application.use_cases.chat_rag import ChatRAGUseCase
from src.infrastructure.api.dependencies import get_chat_use_case
from src.infrastructure.api.security import verify_internal_key
from src.infrastructure.vector.vector_store import vector_store
from src.infrastructure.external.ollama import OllamaAdapter

# Inicialización del Router
router = APIRouter() 

# Modelos de Petición (DTO)
class ChatRequest(BaseModel):
    query: str
    role: str = "teacher" 
    user_id: str = "anon"

class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    context: Optional[str] = None

class RAGIngestRequest(BaseModel):
    documents: List[Dict[str, Any]]

@router.post("/ask", dependencies=[Depends(verify_internal_key)])
async def ask_agent(
    request: ChatRequest,
    use_case: ChatRAGUseCase = Depends(get_chat_use_case)
):
    try:
        
        response_text = await use_case.run(request.query, user_role=request.role)
        
        return {
            "response": response_text,
            "meta": {
                "processed_by": "ia_service_core",
                "role_applied": request.role,
                "user_audit": request.user_id
            }
        }
    
    except Exception as e:
        
        print(f"Error crítico en Microservicio IA (/ask): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/query", dependencies=[Depends(verify_internal_key)])
async def rag_query(
    request: RAGQueryRequest
):
    """Endpoint principal de RAG con Ollama."""
    try:
        ollama = OllamaAdapter()
        
        # Obtener embedding de la consulta
        query_embedding = await ollama.get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Error generando embedding de consulta")
        
        # Buscar documentos relevantes
        query_vector = np.array(query_embedding)
        retrieved_docs = vector_store.search(query_vector, k=request.top_k)
        
        # Construir contexto enriquecido
        context_text = ""
        if request.context:
            context_text = f"Contexto adicional: {request.context}\n\n"
        
        if retrieved_docs:
            context_text += "Documentos relevantes:\n"
            for i, doc in enumerate(retrieved_docs, 1):
                context_text += f"{i}. {doc['text']}\n"
        
        # Prompt para el LLM
        prompt = f"""
Eres un experto en agricultura y herbolaria mexicana. Responde la siguiente pregunta basándote en el contexto proporcionado.

Contexto:
{context_text}

Pregunta: {request.query}

Responde de manera clara, concisa y precisa. Si no hay información suficiente en el contexto, indícalo.
"""
        
        # Generar respuesta con Ollama
        response = await ollama.generate_response(prompt)
        
        return {
            "response": response,
            "sources": [
                {
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "score": doc["score"],
                    "id": doc["id"]
                } for doc in retrieved_docs
            ],
            "meta": {
                "query": request.query,
                "retrieved_docs": len(retrieved_docs),
                "model": "llama3.1:8b-instruct"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en /rag/query: {e}")
        raise HTTPException(status_code=500, detail=f"Error en consulta RAG: {str(e)}")

@router.post("/rag/ingest", dependencies=[Depends(verify_internal_key)])
async def rag_ingest(
    request: RAGIngestRequest
):
    """Endpoint para ingestión de documentos en RAG."""
    try:
        ollama = OllamaAdapter()
        
        if not request.documents:
            raise HTTPException(status_code=400, detail="No se proporcionaron documentos")
        
        texts = []
        embeddings = []
        metadata_list = []
        
        # Procesar cada documento
        for doc in request.documents:
            text = doc.get("text", "")
            if not text.strip():
                continue
                
            texts.append(text)
            
            # Generar embedding
            embedding = await ollama.get_embedding(text)
            if not embedding:
                continue
                
            embeddings.append(embedding)
            
            # Preparar metadatos
            metadata = {
                "source": doc.get("source", "unknown"),
                "title": doc.get("title", ""),
                "type": doc.get("type", "text")
            }
            metadata_list.append(metadata)
        
        if not embeddings:
            raise HTTPException(status_code=400, detail="No se pudieron procesar los documentos")
        
        # Agregar al vector store
        embeddings_array = np.array(embeddings)
        vector_store.add_vectors(embeddings_array, texts, metadata_list)
        vector_store.save()
        
        return {
            "message": f"Se ingestaron {len(embeddings)} documentos exitosamente",
            "stats": vector_store.get_stats(),
            "processed": len(texts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en /rag/ingest: {e}")
        raise HTTPException(status_code=500, detail=f"Error en ingestión RAG: {str(e)}")

@router.get("/rag/stats", dependencies=[Depends(verify_internal_key)])
async def rag_stats():
    """Endpoint para obtener estadísticas del RAG."""
    try:
        return {
            "vector_store": vector_store.get_stats(),
            "models": {
                "llm": "llama3.1:8b-instruct",
                "embedding": "nomic-embed-text"
            }
        }
    except Exception as e:
        print(f"Error en /rag/stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")