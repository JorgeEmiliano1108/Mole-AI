from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routers import router
import logging
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    logging.info("MS-2 RAG+CAG Service (mole_chat) iniciado.")
    yield
    # Lógica de apagado iría aquí si fuera necesaria

app = FastAPI(title="MS-2 RAG+CAG Service", version="1.0", lifespan=lifespan)

app.include_router(router)

_origen = os.getenv('ORIGEN_PERMITIDO', '')
if _origen:
    _allow_origins = [o.strip() for o in _origen.split(',') if o.strip()]
else:
    _allow_origins = []
    
_allow_credentials = os.getenv('CORS_ALLOW_CREDENTIALS', 'False').lower() in ('true', '1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['accept', 'authorization', 'content-type', 'x-csrftoken', 'x-requested-with']
)

@app.get('/config')
def _config() -> dict:
    status = "Running in Staging" if os.getenv('DEBUG', 'False').lower() == 'false' else 'Running in Development'
    port = os.getenv('PORT') or os.getenv('API_PORT') or None
    db_connected = bool(os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_NAME'))
    return {"status": status, "port": port, "db_connected": db_connected}