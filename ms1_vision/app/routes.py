from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from ms1_vision.app.dependencies import get_diagnostic_use_case
from ms1_vision.application.use_cases.create_diagnostic_use_case import CreateDiagnosticUseCase
from ms1_vision.domain.schemas import DiagnosticModel

router = APIRouter(prefix="/api/v1/vision")


@router.post("/analyze", response_model=DiagnosticModel)
async def analyze_vision(
    file: UploadFile = File(...),
    use_case: CreateDiagnosticUseCase = Depends(get_diagnostic_use_case),
) -> DiagnosticModel:
    image_bytes = await file.read()
    try:
        result = await use_case.execute(image_bytes=image_bytes, plant_id="unknown")
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

