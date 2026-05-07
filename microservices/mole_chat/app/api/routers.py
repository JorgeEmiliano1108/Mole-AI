from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
import os
import re
import aiofiles
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.schemas import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, IngestPDFRequest, IngestPDFResponse, SourcesResponse, ContextUpdateRequest
from app.infrastructure.adapters.pgvector_store import PgVectorStore
from app.infrastructure.adapters.llm_client import LLMClient
from app.infrastructure.adapters.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from app.infrastructure.adapters.citation_manager import CitationManager
from app.core.config import settings

router = APIRouter()

# Singleton objects are now in app.state (initialized in lifespan)
# Dependency injection functions to get them from app.state
def _get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client

def _get_pgvector_store(request: Request) -> PgVectorStore:
    return request.app.state.pgvector_store

def _get_redis_adapter(request: Request) -> RedisSensorCacheAdapter:
    return request.app.state.redis_adapter

def _get_citation_manager(request: Request) -> CitationManager:
    return request.app.state.citation_manager


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
async def chat_endpoint(
    request: ChatRequest, 
    current_user_id: str = Depends(get_current_user),
    llm_client: LLMClient = Depends(_get_llm_client),
    vector_store: PgVectorStore = Depends(_get_pgvector_store),
    redis_adapter: RedisSensorCacheAdapter = Depends(_get_redis_adapter),
    citation_manager: CitationManager = Depends(_get_citation_manager),
):
    if request.user_id != current_user_id:
        raise HTTPException(
            status_code=403, 
            detail="Operación prohibida: El user_id de la petición no coincide con la firma del token."
        )
    
    # NOM-059-SEMARNAT Compliance Check (Regex Interception)
    NOM059_PATTERN = re.compile(
        r"(extraer|traficar|comercializar|extracción|vender|comprar).*(biznaga|cactácea|mamífero|especie protegida|NOM-059|prickly pear|succulent|protegida)|(biznaga|cactácea|mamífero|especie protegida|NOM-059|prickly pear|succulent|protegida)",
        re.IGNORECASE
    )
    if NOM059_PATTERN.search(request.message):
        raise HTTPException(
            status_code=403,
            detail="Solicitud prohibida: esta consulta viola la NOM-059-SEMARNAT. Para información oficial, consulte la lista SEMARNAT."
        )
    
    try:
        # Load system prompt
        from app.infrastructure.adapters.prompt_loader import load_prompt
        try:
            system_prompt = load_prompt("agronomist")
        except Exception:
            system_prompt = (
                "Eres Mole.AI, un asistente agrónomo experto especializado en flora. "
                "REGLA DE ORO: Si la información proporcionada en el CONTEXTO DISPONIBLE "
                "(sensores, base local o Trefle API) no contiene la respuesta, DEBES "
                "responder textualmente: 'No tengo suficiente información científica "
                "para responder esto con seguridad.' "
                "NUNCA inventes nombres científicos, tratamientos ni propiedades."
            )
        
        # Create use case with injected dependencies
        use_case = MoleAIChatUseCase(
            llm_client=llm_client,
            vector_store=vector_store,
            redis_adapter=redis_adapter,
            citation_manager=citation_manager,
            system_prompt=system_prompt
        )
        
        response = await use_case.ainvoke(request)
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