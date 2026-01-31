from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.api.routers import chat, upload, learn 

app = FastAPI(title="EscalafonIA System", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(upload.router, prefix="/api", tags=["Ingesta PDF"])
app.include_router(learn.router, prefix="/api", tags=["Aprendizaje Texto"])

@app.get("/health")
def health():
    return {"status": "ok"}