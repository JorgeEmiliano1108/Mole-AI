from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.api.limiter import limiter
from app.api.routers import router
from app.core.config import settings
import asyncio
import logging




@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    logging.info("MS-2 RAG+CAG Service iniciando...")

    # ── Startup: Initialize singletons (cold start ONCE) ─────────
    
    # 1. LLM Client
    from app.infrastructure.adapters.nvidia_client import LLMClient
    llm_client = LLMClient(model_name=settings.NVIDIA_CHAT_MODEL)
    app.state.llm_client = llm_client
    logging.info(f"LLM Client initialized: {settings.NVIDIA_CHAT_MODEL}")

    # 2. PgVectorStore (connection + indexes ONCE)
    from app.infrastructure.adapters.pgvector_store import PgVectorStore
    pgvector_store = PgVectorStore()
    await pgvector_store.initialize()
    pgvector_store.warmup()
    app.state.pgvector_store = pgvector_store
    logging.info("PgVectorStore initialized")

    # 3. Redis + Citation Manager
    from app.infrastructure.adapters.redis_sensor_cache_adapter import RedisSensorCacheAdapter
    from app.infrastructure.adapters.citation_manager import CitationManager
    redis_adapter = RedisSensorCacheAdapter(settings.REDIS_URL)
    app.state.redis_adapter = redis_adapter
    app.state.citation_manager = CitationManager()
    logging.info("Redis + CitationManager initialized")

    # 4. RAG Listener (non-blocking)
    rag_listener_task = None
    try:
        from app.infrastructure.adapters.rag_listener import start_rag_listener
        rag_listener_task = await start_rag_listener()
        logging.info("RAG Training Listener iniciado como asyncio.Task")
    except Exception as e:
        logging.error(f"Error iniciando RAG Listener: {e}")

    yield

    # ── Shutdown: Cancel listener + close pools ──────────────
    if rag_listener_task and not rag_listener_task.done():
        rag_listener_task.cancel()
        try:
            await rag_listener_task
        except asyncio.CancelledError:
            pass
        logging.info("RAG Training Listener detenido.")

    await pgvector_store.close()
    await redis_adapter.close()
    logging.info("Pools closed.")

app = FastAPI(title="MS-2 RAG+CAG Service", version="2.0", lifespan=lifespan)

# ── Rate Limiting ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Prometheus metrics instrumentation
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

app.include_router(router)

_origen = settings.ORIGEN_PERMITIDO
if _origen:
    _allow_origins = [o.strip() for o in _origen.split(',') if o.strip()]
else:
    _allow_origins = []

_allow_credentials = settings.CORS_ALLOW_CREDENTIALS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['accept', 'authorization', 'content-type', 'x-csrftoken', 'x-requested-with']
)

@app.get('/config')
def _config() -> dict:
    status = "Running in Staging" if not settings.DEBUG else "Running in Development"
    port = settings.API_PORT
    db_connected = bool(settings.DATABASE_URL or settings.SUPABASE_URL)
    return {"status": status, "port": port, "db_connected": db_connected}