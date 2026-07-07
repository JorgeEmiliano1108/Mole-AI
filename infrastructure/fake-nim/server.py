"""FastAPI server que emula NVIDIA NIM para pruebas end-to-end."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.7


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    return {
        "choices": [{"message": {"content": "Respuesta simulada desde fake NIM para pruebas E2E."}}]
    }


@app.post("/v1/embeddings")
async def embeddings():
    # pgvector_store.py usa vector(1024) — dimensión NVIDIA nv-embedqa-e5-v5
    return {"data": [{"embedding": [0.1] * 1024}]}
