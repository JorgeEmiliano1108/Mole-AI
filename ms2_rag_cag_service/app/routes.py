# FastAPI endpoints for MS-2 RAG+CAG Service
from fastapi import APIRouter, HTTPException
from ms2_rag_cag_service.application.chat_usecase import MoleAIChatUseCase
from ms2_rag_cag_service.domain.models import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, IngestPDFRequest, IngestPDFResponse, SourcesResponse, ContextUpdateRequest

router = APIRouter()

@router.post("/api/v1/mole-ai/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = await MoleAIChatUseCase().ainvoke(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings_endpoint(request: EmbeddingRequest):
    # ...implementation placeholder...
    return EmbeddingResponse(embeddings=[], disclaimer="COFEPRIS: Esta respuesta es informativa.", sources=[])

@router.post("/api/v1/knowledge/ingest-pdf", response_model=IngestPDFResponse)
async def ingest_pdf_endpoint(request: IngestPDFRequest):
    # ...implementation placeholder...
    return IngestPDFResponse(success=True, disclaimer="COFEPRIS: Esta respuesta es informativa.", sources=[])

@router.get("/api/v1/knowledge/sources", response_model=SourcesResponse)
async def sources_endpoint():
    # ...implementation placeholder...
    return SourcesResponse(sources=[])

@router.post("/api/v1/mole-ai/context")
async def context_update_endpoint(request: ContextUpdateRequest):
    # ...implementation placeholder...
    return {"success": True}

@router.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "ms2_rag_cag"}
