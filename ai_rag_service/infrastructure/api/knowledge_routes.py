"""
API Routes - Knowledge Ingestion (PDF Upload)

Provides a dedicated router for knowledge base management.
The existing /knowledge/ingest in routes.py still works;
this file adds a cleaner /knowledge/ingest-pdf alias with
extra validation (file type, size limit).
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File

from application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase

logger = logging.getLogger(__name__)

knowledge_router = APIRouter(tags=["Knowledge Base"])

# Max file size: 20 MB
MAX_FILE_SIZE = 20 * 1024 * 1024


def create_knowledge_routes(ingest_use_case: IngestKnowledgeUseCase):
    """Factory with dependency injection for the knowledge routes."""

    @knowledge_router.post(
        "/knowledge/ingest-pdf",
        summary="Ingest a PDF into the RAG knowledge base",
        response_model=None,
    )
    async def ingest_pdf(file: UploadFile = File(...)):
        """
        Upload a .pdf file to be parsed, chunked (500 chars, 50 overlap),
        embedded, and stored in the FAISS vector store.

        Returns the number of chunks added.
        """
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Solo se aceptan archivos .pdf"
            )

        # Read content
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo excede el limite de {MAX_FILE_SIZE // (1024*1024)} MB"
            )

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="El archivo esta vacio")

        try:
            result = await ingest_use_case.execute(
                file_content=content,
                filename=file.filename,
                metadata={"category": "pdf_upload", "source": file.filename}
            )

            return {
                "status": result.get("status", "success"),
                "chunks_added": result.get("chunks_added", 0),
                "filename": file.filename,
            }

        except Exception as e:
            logger.error(f"PDF ingestion failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @knowledge_router.get(
        "/knowledge/sources",
        summary="List ingested knowledge sources",
        response_model=None,
    )
    async def list_sources():
        """Return metadata about all documents in the vector store."""
        try:
            if hasattr(ingest_use_case, 'vector_store'):
                sources = await ingest_use_case.vector_store.get_sources()
                return {"sources": sources, "total": len(sources)}
            return {"sources": [], "total": 0}
        except Exception as e:
            logger.error(f"Error listing sources: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return knowledge_router
