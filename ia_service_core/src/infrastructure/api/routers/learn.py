from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.application.use_cases.ingest_text import IngestTextUseCase
from src.infrastructure.api.dependencies import get_ingest_text_use_case

router = APIRouter()

class LearnRequest(BaseModel):
    text: str
    source: str = "Información General"  # Opcional, por defecto pone esto

@router.post("/learn")
async def learn_text(
    request: LearnRequest,
    use_case: IngestTextUseCase = Depends(get_ingest_text_use_case)
):
    try:
        # Delegamos al caso de uso
        result = await use_case.run(request.text, request.source)
        
        return {
            "status": "success",
            "message": "Información aprendida exitosamente.",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))