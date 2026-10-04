"""FastAPI server que emula NVIDIA NIM para pruebas end-to-end."""
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.7


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    # Modo judge scripteado (Track C): si el llamador envía el header
    # X-Fake-Verdict con un JSON {"verdict": ..., "reason": ...}, se devuelve
    # tal cual para testear la ruta LLM-as-judge de forma determinista en CI.
    scripted = request.headers.get("X-Fake-Verdict")
    if scripted:
        return {"choices": [{"message": {"content": scripted}}]}
    return {
        "choices": [{"message": {"content": "Respuesta simulada desde fake NIM para pruebas E2E."}}]
    }


@app.post("/v1/embeddings")
async def embeddings():
    # pgvector_store.py usa vector(1024) — dimensión NVIDIA nv-embedqa-e5-v5
    return {"data": [{"embedding": [0.1] * 1024}]}
