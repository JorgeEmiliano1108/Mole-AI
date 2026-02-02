from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .adapters.outbound.yolo_adapter import YOLOAdapter
from .adapters.outbound.storage_adapter import FileSystemImageStorageAdapter, SimpleVisionRepositoryAdapter
from .adapters.inbound.api import create_vision_controller
from .use_cases.image_analysis import ImageAnalysisUseCase, PlantTypeDetectionUseCase
from .config.settings import settings

# Variables globales para los servicios
image_analyzer = None
storage = None
repository = None
image_analysis_use_case = None
plant_detection_use_case = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y limpieza de la aplicación"""
    global image_analyzer, storage, repository, image_analysis_use_case, plant_detection_use_case
    
    try:
        # Inicializar adaptadores y servicios
        image_analyzer = YOLOAdapter()
        storage = FileSystemImageStorageAdapter()
        repository = SimpleVisionRepositoryAdapter()
        
        # Inicializar casos de uso
        image_analysis_use_case = ImageAnalysisUseCase(
            image_analyzer=image_analyzer,
            storage=storage,
            repository=repository
        )
        plant_detection_use_case = PlantTypeDetectionUseCase(
            image_analyzer=image_analyzer
        )
        
        print("✅ Servicio de Visión Mole AI iniciado correctamente")
        yield
        
    except Exception as e:
        print(f"❌ Error iniciando servicio de visión: {str(e)}")
        raise
    finally:
        # Limpieza si es necesario
        print("🔄 Servicio de Visión Mole AI detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="Mole AI Vision Service",
    description="Servicio de análisis de imágenes para diagnóstico de plantas endémicas mexicanas",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear controlador con inyección de dependencias
def get_vision_controller():
    """Obtener instancia del controlador con dependencias inyectadas"""
    if not image_analysis_use_case:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")
    
    return create_vision_controller(image_analyzer)

# Incluir rutas
from .adapters.inbound.api import router as vision_router

# Modificar las rutas para incluir las dependencias
app.include_router(vision_router, prefix="/api/v1", tags=["Vision Analysis"])

# Endpoint de salud personalizado
@app.get("/health")
async def health_check():
    """Verificación de salud del servicio"""
    try:
        return {
            "status": "healthy",
            "service": "Mole AI Vision Service",
            "version": "1.0.0",
            "models_loaded": image_analyzer is not None,
            "storage_ready": storage is not None
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Servicio no disponible: {str(e)}")

# Endpoint raíz
@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Mole AI Vision Service",
        "description": "Análisis de imágenes con YOLOv8 para diagnóstico de plantas",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze",
            "upload": "/api/v1/analyze/upload",
            "detect_plant": "/api/v1/detect-plant"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.VISION_SERVICE_HOST,
        port=settings.VISION_SERVICE_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )