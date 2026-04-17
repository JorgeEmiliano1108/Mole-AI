from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from ms1_vision.app.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="MS-1 Vision CNN & Gatekeeper")
    app.include_router(router)

    # CORS configuration from environment (strict: use ORIGEN_PERMITIDO)
    _origen = os.getenv('ORIGEN_PERMITIDO', '')
    if _origen:
        allow_origins = [o.strip() for o in _origen.split(',') if o.strip()]
    else:
        allow_origins = []
    allow_credentials = os.getenv('CORS_ALLOW_CREDENTIALS', 'False').lower() in ('true', '1')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
        allow_headers=['accept', 'authorization', 'content-type', 'x-csrftoken', 'x-requested-with']
    )

    # ensure model is loaded at startup (fail-fast if misconfigured)
    from ms1_vision.app.dependencies import get_vision_client

    # configure structured logging
    try:
        from ms1_vision.app.logging_config import configure_logging

        configure_logging()
    except Exception:
        pass

    @app.on_event("startup")
    def _ensure_model_loaded() -> None:
        # calling get_vision_client will instantiate CNNVisionClient and raise on failure
        get_vision_client()


    @app.get("/config")
    def _config() -> dict:
        status = "Running in Staging" if os.getenv('DEBUG', 'False').lower() == 'false' else 'Running in Development'
        port = os.getenv('PORT') or os.getenv('API_PORT') or None
        db_connected = bool(os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_NAME'))
        return {"status": status, "port": port, "db_connected": db_connected}

    return app


app = create_app()
