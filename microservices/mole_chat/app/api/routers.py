from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
import os
import aiofiles
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.schemas import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, IngestPDFRequest, IngestPDFResponse, SourcesResponse, ContextUpdateRequest
from app.infrastructure.adapters.pgvector_store import PgVectorStore

router = APIRouter()

# Lazy-initialized pgvector store (replaces module-level FAISS instance)
_pgvector_store: PgVectorStore | None = None

async def _get_pgvector_store() -> PgVectorStore:
    global _pgvector_store
    if _pgvector_store is None:
        _pgvector_store = PgVectorStore()
        await _pgvector_store.initialize()
    return _pgvector_store


# Modelos de respuesta exclusivos para PDFs
class IngestResponse(BaseModel):
    success: bool
    doc_id: str
    message: str

class DeleteResponse(BaseModel):
    success: bool
    message: str


# ✅ RESTAURADO: El motor principal de Chat protegido con Zero-Trust
@router.post("/api/v1/mole-ai/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user_id: str = Depends(get_current_user)):
    if request.user_id != current_user_id:
        raise HTTPException(
            status_code=403, 
            detail="Operación prohibida: El user_id de la petición no coincide con la firma del token."
        )
    try:
        response = await MoleAIChatUseCase().ainvoke(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 📄 Endpoint para ingestar manuales/documentos (vía HTTP upload directo)
# NOTA: La vía principal de ingesta es ahora el RAG Listener (Redis Pub/Sub).
# Este endpoint se mantiene como fallback para uploads manuales sin MinIO.
@router.post("/api/v1/knowledge/ingest-pdf", response_model=IngestResponse)
async def ingest_pdf_endpoint(
    file: UploadFile = File(...), 
    current_user_id: str = Depends(get_current_user)
):
    
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")
    
    temp_path = f"/tmp/{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        
    try:
        # Use pgvector store for ingestion
        from app.infrastructure.adapters.rag_listener import _extract_text_from_pdf
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from app.core.config import settings
        import uuid

        store = await _get_pgvector_store()

        with open(temp_path, "rb") as f:
            pdf_bytes = f.read()

        text = _extract_text_from_pdf(pdf_bytes)
        if not text.strip():
            raise ValueError("PDF vacío o no contiene texto extraíble.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        )
        chunks = splitter.split_text(text)
        doc_id = str(uuid.uuid4())

        await store.insert_chunks(
            doc_id=doc_id,
            s3_key=f"manual_upload/{file.filename}",
            source_name=file.filename,
            chunks=chunks,
        )

        return IngestResponse(success=True, doc_id=doc_id, message=f"PDF {file.filename} indexado exitosamente ({len(chunks)} chunks).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PDF: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 🗑️ Endpoint para borrar documentos selectivamente
@router.delete("/api/v1/knowledge/pdf/{doc_id}", response_model=DeleteResponse)
async def delete_pdf_endpoint(
    doc_id: str, 
    current_user_id: str = Depends(get_current_user)
):
    store = await _get_pgvector_store()
    deleted = await store.delete_by_doc_id(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Documento no encontrado o no pudo ser eliminado.")
        
    return DeleteResponse(success=True, message=f"Documento {doc_id} eliminado exitosamente del índice ({deleted} chunks).")

@router.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "mole_chat"}