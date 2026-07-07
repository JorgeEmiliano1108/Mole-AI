from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import reports
from app.config import settings
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="MS-3 Reports Service", version="0.2.0")

# Prometheus metrics instrumentation
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# CORS configuration from environment
_origen = settings.origen_permitido
if _origen:
    _allow_origins = [o.strip() for o in _origen.split(',') if o.strip()]
else:
    _allow_origins = []
_allow_credentials = settings.cors_allow_credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['accept', 'authorization', 'content-type', 'x-csrftoken', 'x-requested-with']
)


@app.on_event("startup")
async def startup_event():
    # Place for startup connectors if needed
    pass


@app.on_event("shutdown")
async def shutdown_event():
    # Clean shutdown hooks
    pass


app.include_router(reports.router, tags=["reports"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.ms3_host, port=settings.ms3_port)


@app.get('/health')
def _health() -> dict:
    return {"status": "ok", "service": "mole_report"}


@app.get('/config')
def _config() -> dict:
    status = "Running in Staging" if not settings.debug else 'Running in Development'
    port = settings.ms3_port
    db_connected = bool(settings.database_url or settings.ms3_supabase_url)
    return {"status": status, "port": port, "db_connected": db_connected}
