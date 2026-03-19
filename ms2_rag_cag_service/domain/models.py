from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union


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
    sources: List[SourceMetadata]
    # Disclaimer can be a boolean flag or a textual message
    disclaimer: Union[bool, str]


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
