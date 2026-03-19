from fastapi import FastAPI
from ms1_vision.app.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="MS-1 Vision CNN & Gatekeeper")
    app.include_router(router)
    return app


app = create_app()
