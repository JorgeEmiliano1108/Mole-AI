"""
App-level dependencies and configuration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Application Layer

# Infrastructure Layer

def create_app() -> FastAPI:
    """Factory function to create FastAPI application"""
    app = FastAPI(
        title="Mole AI - RAG Backend-for-Backend",
        description="FastAPI microservice providing AI capabilities for Django",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

