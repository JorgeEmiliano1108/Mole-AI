# 🎯 Mole AI - Vision Service

**Microservicio de análisis visual de plantas** usando **Phi-3.5 Vision-Instruct Q4**

Arquitectura hexagonal, independiente, probable vía Swagger UI.

## 🏗️ Arquitectura Hexagonal

```
ai_vision_service/
├── domain/                    # Lógica de negocio pura
│   ├── models/               # Entidades del dominio
│   ├── ports/                # Interfaces (abstracciones)
│   └── exceptions/           # Excepciones de negocio
├── use_cases/                # Orquestación de lógica
│   └── analyze_plant_vision.py
├── adapters/                 # Implementaciones concretas
│   ├── inbound/             # FastAPI / HTTP
│   └── outbound/            # Phi-3.5 Model, etc
├── infrastructure/          # Configuración
├── main.py                  # Entry point FastAPI
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🚀 Inicio Rápido

### 1. Instalación Local

```bash
cd ai_vision_service
pip install -r requirements.txt
```

### 2. Ejecutar Servicio

```bash
python -m uvicorn main:app --reload --port 8001
```

Swagger UI estará en: **http://localhost:8001/docs**

### 3. Probar con Swagger

1. Abre http://localhost:8001/docs
2. Expande `POST /vision/analyze`
3. Click en "Try it out"
4. Pega una imagen en base64 en `image_base64`
5. Click en "Execute"

## 📡 Endpoints

### POST `/vision/analyze`

Analiza imagen de planta

**Request:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSU..."
}
```

**Response:**
```json
{
  "id": "uuid-123",
  "timestamp": "2024-12-19T10:30:00",
  "estado": "Atención",
  "confianza": 0.85,
  "sintomas": [
    {
      "nombre": "Manchas oscuras",
      "confianza": 0.9,
      "descripcion": "Manchas necróticas en hojas"
    }
  ],
  "especie_probable": "Solanum lycopersicum",
  "análisis_visual": "..."
}
```

### GET `/vision/health`

Health check

```json
{
  "status": "healthy",
  "model_ready": true,
  "timestamp": "2024-12-19T10:30:00"
}
```

### GET `/`

Información del servicio

## 📦 Docker

### Build

```bash
docker build -t mole-ai-vision:1.0 .
```

### Run

```bash
docker run -p 8001:8001 mole-ai-vision:1.0
```

Swagger: http://localhost:8001/docs

## 🧠 Modelo

**Phi-3.5 Vision-Instruct Q4**
- Únicamente modelo permitido
- CPU-optimized
- Q4 quantization

## 🏛️ Diseño Hexagonal

### Domain (Puro)
- `models/`: Entidades (PlantState, VisionAnalysisResult)
- `ports/`: Interfaces (VisionModelPort)
- `exceptions/`: Errores de negocio

### Use Cases
- `analyze_plant_vision.py`: Lógica de orquestación
- Depende SOLO de puertos del domain

### Adapters
- **Inbound**: FastAPI router (HTTP)
- **Outbound**: Phi-3.5 implementation

### Infrastructure
- Configuración (settings)
- Inyección de dependencias

## ✅ Flujo de Ejecución

```
1. HTTP Request → FastAPI Adapter (Inbound)
2. Adapter → Use Case
3. Use Case → Domain Ports
4. Ports → Phi-3.5 Adapter (Outbound)
5. Phi-3.5 → Análisis
6. Response → Domain Model
7. Domain Model → Adapter
8. Adapter → HTTP Response (JSON)
```

## 📖 Documentación Automática

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

## 🔧 Desarrollo

### Estructura de Código

```python
# domain/models/__init__.py
@dataclass
class VisionAnalysisResult:
    estado: PlantState        # Sana | Atención | Peligro
    confianza: float          # 0.0-1.0
    sintomas: List[Symptom]
    especie_probable: str
    análisis_visual: str

# domain/ports/__init__.py
class VisionModelPort(ABC):
    async def analyze_image(request) -> VisionAnalysisResult
    async def is_ready() -> bool

# adapters/outbound/__init__.py
class Phi3VisionAdapter(VisionModelPort):
    async def analyze_image(request):
        # Implementación con Phi-3.5

# adapters/inbound/__init__.py
@router.post("/vision/analyze")
async def analyze_plant(request):
    result = await use_case.execute(request)
    return response
```

### Testing

```python
# Prueba unitaria del use case
@pytest.mark.asyncio
async def test_analyze_plant():
    mock_model = MockVisionModel()
    use_case = AnalyzePlantVisionUseCase(mock_model)
    result = await use_case.execute(request)
    assert result.estado == PlantState.SANA
```

## 📝 Variables de Ambiente

```env
# API
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO

# Modelo
MODEL_NAME=microsoft/Phi-3.5-vision-instruct
```

## ⛔ Prohibiciones (Cumplimiento)

✅ NO hay lógica fuera del microservicio
✅ NO se comunica con otros servicios (solo local)
✅ NO usa otros modelos (solo Phi-3.5)
✅ NO usa BD externas
✅ NO hay pseudocódigo (100% ejecutable)
✅ Probable ÚNICAMENTE vía Swagger UI

## 📊 Estados de Planta

| Estado | Descripción |
|--------|-------------|
| **Sana** | Sin problemas, buena salud |
| **Atención** | Problemas moderados, requiere monitoreo |
| **Peligro** | Problemas graves, intervención urgente |

## 🚦 Health Check

```bash
curl http://localhost:8001/vision/health
```

Respuesta:
```json
{
  "status": "healthy",
  "model_ready": true,
  "timestamp": "2024-12-19T10:30:00"
}
```

---

**Versión:** 1.0.0  
**Status:** Production Ready ✅  
**Modelo:** Phi-3.5 Vision-Instruct Q4  
**Arquitectura:** Hexagonal
