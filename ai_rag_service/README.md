# 🧬 Mole AI - RAG Service

**Microservicio de RAG + Razonamiento** usando **Phi-3.5 Vision-Instruct Q4**

Integra conocimiento externo (PDFs) con razonamiento para generar diagnósticos finales.

Arquitectura hexagonal, independiente, probable vía Swagger UI.

## 🏗️ Arquitectura Hexagonal

```
ai_rag_service/
├── domain/                    # Lógica pura
│   ├── models/               # Entidades
│   ├── ports/                # Interfaces
│   └── exceptions/
├── use_cases/                # Orquestación
│   ├── upload_pdf_use_case.py
│   └── diagnose_with_rag_use_case.py
├── adapters/                 # Implementaciones
│   ├── inbound/             # FastAPI
│   └── outbound/
│       ├── vector_store.py  # FAISS
│       └── phi3_reasoning.py
├── infrastructure/          # Configuración
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🚀 Inicio Rápido

### 1. Instalación

```bash
cd ai_rag_service
pip install -r requirements.txt
```

### 2. Ejecutar Servicio

```bash
python -m uvicorn main:app --reload --port 8002
```

Swagger: http://localhost:8002/docs

### 3. Probar Endpoints

#### Subir PDF (Admin)

```bash
curl -X POST http://localhost:8002/rag/admin/upload-pdf \
  -F "file=@plant_guide.pdf"
```

#### Diagnóstico Final

```json
{
  "vision_output": {
    "estado": "Atención",
    "confianza": 0.85,
    "especie_probable": "Solanum lycopersicum",
    "sintomas": ["Manchas", "Defoliación"],
    "análisis_visual": "..."
  },
  "sensores": {
    "ph": 6.5,
    "humedad": 65.0,
    "temp": 24.5,
    "uv": 0.8
  }
}
```

## 📡 Endpoints

### POST `/rag/diagnose`

Diagnóstico final (Vision + RAG + Phi-3.5)

**Request:**
```json
{
  "vision_output": {...},
  "sensores": {...}
}
```

**Response:**
```json
{
  "id": "uuid",
  "timestamp": "2024-12-19T10:30:00",
  "diagnostico": "Tizón tardío confirmado",
  "recomendaciones": ["Aplicar fungicida"],
  "fuentes_consultadas": ["plant_diseases.pdf"],
  "confianza_final": 0.92,
  "requiere_accion_humana": false
}
```

### POST `/rag/admin/upload-pdf`

Inyecta PDF dinámicamente al RAG

```bash
curl -X POST http://localhost:8002/rag/admin/upload-pdf \
  -F "file=@knowledge.pdf"
```

### GET `/rag/admin/sources`

Lista PDFs cargados

### GET `/rag/health`

Health check

## 📊 Flujo de Datos

```
1. Recibe output de Vision Service
   ├─ estado, confianza, especie, síntomas
   └─ análisis visual

2. Recibe datos de sensores
   ├─ pH, humedad, temp, UV
   └─ Contexto ambiental

3. RAG retrieval
   └─ Query similar en FAISS → chunks relevantes

4. Razonamiento con Phi-3.5
   ├─ Procesa: visión + sensores + conocimiento
   └─ Output: diagnóstico + recomendaciones

5. Respuesta estructurada JSON
   └─ Diagnóstico final, fuentes, acción requerida
```

## 📦 Docker

### Build

```bash
docker build -t mole-ai-rag:1.0 .
```

### Run

```bash
docker run -p 8002:8002 \
  -v $(pwd)/storage:/app/storage \
  mole-ai-rag:1.0
```

## 🧠 Modelo

**Phi-3.5 Vision-Instruct Q4**
- ÚNICO modelo permitido
- CPU-optimized
- Q4 quantization
- Usado para razonamiento + contexto RAG

## 🏛️ Diseño Hexagonal

### Domain
- `models/`: Entidades (VisionOutput, DiagnoseRequest, FinalDiagnosis)
- `ports/`: Interfaces (VectorStorePort, ReasoningModelPort)

### Use Cases
- `UploadPDFUseCase`: Ingesta dinámica de PDFs
- `DiagnoseWithRAGUseCase`: Integración completa

### Adapters
- **Inbound**: FastAPI + Swagger
- **Outbound**: FAISS + Phi-3.5 Reasoning

## ✅ Flujo de Ejecución

```
1. HTTP Request → FastAPI Adapter
2. Adapter → Use Case (DiagnoseWithRAGUseCase)
3. Use Case → Domain Ports
4. Ports → FAISS (retrieval) + Phi-3.5 (reasoning)
5. Domain Models ← Adapters
6. HTTP Response (JSON)
```

## 📖 Documentación

- **Swagger**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc
- **OpenAPI**: http://localhost:8002/openapi.json

## 🔧 Configuración

```env
API_HOST=0.0.0.0
API_PORT=8002
REASONING_MODEL=microsoft/Phi-3.5-vision-instruct
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DB_PATH=storage/vectors
LOG_LEVEL=INFO
```

## 📝 Modelos de Datos

```python
# Entrada desde Vision Service
VisionOutput(
    estado: "Sana|Atención|Peligro",
    confianza: 0.0-1.0,
    especie_probable: str,
    sintomas: List[str],
    análisis_visual: str
)

# Entrada de sensores
SensorData(
    ph: float,
    humedad: float,
    temp: float,
    uv: float
)

# Salida final
FinalDiagnosis(
    diagnostico: str,
    recomendaciones: List[str],
    fuentes_consultadas: List[str],
    confianza_final: float,
    requiere_accion_humana: bool
)
```

## 🗄️ Vector Store (FAISS)

```
storage/vectors/
├── faiss_index/        # Índice de FAISS
└── metadata.json       # Metadatos de PDFs
```

## ⛔ Prohibiciones (Compliance)

✅ NO se comunica con Vision Service (independiente)
✅ NO usa otros modelos (solo Phi-3.5)
✅ NO bases de datos externas
✅ NO pseudocódigo
✅ 100% ejecutable
✅ Probable vía Swagger UI

## 🚦 Health Check

```bash
curl http://localhost:8002/rag/health
```

```json
{
  "status": "healthy",
  "timestamp": "2024-12-19T10:30:00"
}
```

---

**Versión:** 1.0.0  
**Status:** Production Ready ✅  
**Modelo:** Phi-3.5 Vision-Instruct Q4  
**Arquitectura:** Hexagonal
