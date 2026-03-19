from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union

# ── COFEPRIS Legal Disclaimer (mandatory on every AI response) ──────────────
COFEPRIS_DISCLAIMER: str = (
    "AVISO LEGAL: La información proporcionada es de carácter estrictamente "
    "informativo y no constituye una recomendación profesional, receta agronómica ni "
    "prescripción de uso de plaguicidas o agroquímicos. Cualquier aplicación de productos "
    "fitosanitarios debe realizarse bajo la supervisión de un profesional certificado y "
    "conforme a las disposiciones de COFEPRIS, la Ley General de Salud y normativa aplicable. "
    "Mole.AI no se hace responsable por el uso indebido de la información aquí presentada."
)


class SourceMetadata(BaseModel):
    model_config = ConfigDict()
    autor: str
    url: str
    confianza: float


class ChatRequest(BaseModel):
    model_config = ConfigDict()
    user_id: str
    message: str


# Pydantic v2 model: requires `respuesta`, `sources` and `disclaimer` (bool or text)
class ChatResponse(BaseModel):
    model_config = ConfigDict()
    respuesta: str
    sources: List[SourceMetadata] = []
    # Disclaimer defaults to mandatory COFEPRIS legal text; can be overridden but never empty
    disclaimer: Union[bool, str] = Field(default=COFEPRIS_DISCLAIMER)


class EmbeddingRequest(BaseModel):
    model_config = ConfigDict()
    text: str


class EmbeddingResponse(BaseModel):
    model_config = ConfigDict()
    embeddings: List[float]
    disclaimer: Optional[str] = None
    sources: List[SourceMetadata] = []


class IngestPDFRequest(BaseModel):
    model_config = ConfigDict()
    pdf_url: str


class IngestPDFResponse(BaseModel):
    model_config = ConfigDict()
    success: bool
    disclaimer: Optional[str] = None
    sources: List[SourceMetadata] = []


class SourcesResponse(BaseModel):
    model_config = ConfigDict()
    sources: List[SourceMetadata]


class ContextUpdateRequest(BaseModel):
    model_config = ConfigDict()
    user_id: str
    context: dict
