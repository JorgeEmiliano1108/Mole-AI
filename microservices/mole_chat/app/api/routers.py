from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
import os
import aiofiles
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.schemas import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, IngestPDFRequest, IngestPDFResponse, SourcesResponse, ContextUpdateRequest
from app.infrastructure.adapters.faiss_vector_store import FAISSVectorStore

router = APIRouter()
vector_store = FAISSVectorStore()

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


# 📄 NUEVO: Endpoint para ingestar manuales/documentos
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
        doc_id = await vector_store.ingest_pdf(temp_path, file.filename)
        return IngestResponse(success=True, doc_id=doc_id, message=f"PDF {file.filename} indexado exitosamente.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PDF: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 🗑️ NUEVO: Endpoint para borrar documentos selectivamente
@router.delete("/api/v1/knowledge/pdf/{doc_id}", response_model=DeleteResponse)
async def delete_pdf_endpoint(
    doc_id: str, 
    current_user_id: str = Depends(get_current_user)
):
    success = await vector_store.delete_pdf_by_id(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Documento no encontrado o no pudo ser eliminado.")
        
    return DeleteResponse(success=True, message=f"Documento {doc_id} eliminado exitosamente del índice.")

@router.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "mole_chat"}