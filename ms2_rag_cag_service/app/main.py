from fastapi import FastAPI
from ms2_rag_cag_service.app.routes import router
import logging

app = FastAPI(title="MS-2 RAG+CAG Service", version="1.0")

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)
    logging.info("MS-2 RAG+CAG Service iniciado.")
