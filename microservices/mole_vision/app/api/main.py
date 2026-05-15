"""
API Layer - Main Entry Point
Fase 3 (NVIDIA NIM): Migrated from TFLite to cloud vision inference.
"""
import asyncio
import os
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.routers import router


def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=get_real_ip)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

slogger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan: manages startup and shutdown of the vision service.

    Startup:
      1. Pre-load the TFLite vision model (inference)
      2. Start the Vision Training Listener (Redis Pub/Sub → fine-tuning)

    Shutdown:
      1. Cancel the listener task
      2. Shutdown the ProcessPoolExecutor
    """
    slogger.info("service_starting", service=settings.SERVICE_NAME)

    # ── Startup: Verify NVIDIA NIM adapter ready ─────────────────────
    try:
        from app.infrastructure.adapters.nvidia_vision_adapter import NvidiaVisionAdapter
        adapter = NvidiaVisionAdapter()
        slogger.info("nvidia_vision_adapter_ready", ready=adapter.is_ready())
    except Exception as e:
        slogger.error("vision_adapter_init_failed", error=str(e))

    # ── Startup: Launch Vision Training Listener ─────────────────────
    listener_task = None
    try:
        from app.infrastructure.adapters.vision_listener import start_vision_listener
        listener_task = await start_vision_listener()
        slogger.info("vision_training_listener_started")
    except Exception as e:
        slogger.error("vision_listener_start_failed", error=str(e))

    yield

    # ── Shutdown: Cancel listener ────────────────────────────────────
    if listener_task and not listener_task.done():
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        slogger.info("vision_training_listener_stopped")

    # ── Shutdown: Cleanup ProcessPoolExecutor ─────────────────────────
    try:
        from app.infrastructure.adapters.vision_listener import _training_executor
        _training_executor.shutdown(wait=False)
        slogger.info("training_executor_shutdown")
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mole-Vision API",
        description="Vision CNN Service with Zero-Trust Security & MLOps Pipeline",
        version="2.1.0",
        lifespan=lifespan,
    )
    
    app.include_router(router)

    # ── Rate Limiting ──────────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS from settings
    allow_origins = []
    if settings.ORIGEN_PERMITIDO:
        allow_origins = [o.strip() for o in settings.ORIGEN_PERMITIDO.split(",") if o.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["accept", "authorization", "content-type", "x-csrftoken", "x-requested-with"],
    )
    
    @app.get("/config")
    def config() -> dict:
        """Información de configuración del servicio."""
        return {
            "status": "Production" if not settings.DEBUG else "Development",
            "service": settings.SERVICE_NAME,
        }
    
    # Prometheus metrics instrumentation
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    
    return app


app = create_app()