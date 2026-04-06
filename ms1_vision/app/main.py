from fastapi import FastAPI
from ms1_vision.app.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="MS-1 Vision CNN & Gatekeeper")
    app.include_router(router)

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

    return app


app = create_app()
