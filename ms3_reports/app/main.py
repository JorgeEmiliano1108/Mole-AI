from fastapi import FastAPI
from app.api.v1 import reports
from app.config import settings

app = FastAPI(title="MS-3 Reports Service", version="0.1.0")


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
