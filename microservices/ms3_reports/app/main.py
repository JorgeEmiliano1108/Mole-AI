from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import reports
from app.config import settings
import os

app = FastAPI(title="MS-3 Reports Service", version="0.1.0")

# CORS configuration from environment (strict: use ORIGEN_PERMITIDO)
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


@app.on_event("startup")
async def startup_event():
    # Place for startup connectors if needed
    pass


@app.on_event("shutdown")
async def shutdown_event():
    # Clean shutdown hooks
    pass


app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)


@app.get('/config')
def _config() -> dict:
    status = "Running in Staging" if os.getenv('DEBUG', 'False').lower() == 'false' else 'Running in Development'
    port = os.getenv('PORT') or getattr(settings, 'PORT', None)
    db_connected = bool(os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_NAME'))
    return {"status": status, "port": port, "db_connected": db_connected}
