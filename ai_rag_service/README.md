# Mole AI - Backend for Backend Service

## 📋 **Overview**

FastAPI microservice siguiendo **Arquitectura Hexagonal (Clean Architecture)** que proporciona capacidades de IA para aplicaciones Django consumidoras.

## 🏗️ **Arquitectura**

```
ai_rag_service/
├── domain/                    # Lógica de negocio pura
│   ├── models.py             # Entidades (EmbeddingRequest, ChatRequest, etc.)
│   └── ports.py              # Interfaces abstractas (EmbeddingPort, LLMGenerationPort)
├── application/               # Casos de uso (orchestración)
│   └── use_cases.py          # GenerateEmbeddingUseCase, GenerateChatUseCase
├── infrastructure/           # Implementaciones concretas
│   ├── ai/                   # Servicios de IA
│   │   ├── embeddings.py     # SentenceTransformerEmbeddingAdapter
│   │   ├── llm.py           # Phi35LLMAdapter
│   │   └── model_manager.py  # ModelManagerAdapter
│   └── api/                  # Capa HTTP
│       ├── contracts.py      # DTOs Pydantic
│       └── routes.py         # Endpoints FastAPI
└── main_refactored.py        # Orquestador principal
```

## 🔌 **API Endpoints**

### **1. Generar Embeddings**
```http
POST /v1/embeddings
Content-Type: application/json

{
    "text": "¿Cómo puedo cuidar una planta de menta en casa?"
}
```

**Response:**
```json
{
    "vector": [0.12, -0.45, 0.78, ...],  // 768 dimensiones
    "dimension": 768,
    "model_used": "sentence-transformers/all-mpnet-base-v2",
    "processing_time_ms": 45.2
}
```

### **2. Generar Respuesta Chat**
```http
POST /v1/chat/generate
Content-Type: application/json

{
    "query": "¿Cómo riego la menta?",
    "context": [
        "La menta necesita humedad constante pero sin encharcamiento.",
        "Es mejor regar por la mañana para evitar hongos."
    ],
    "max_tokens": 512,
    "temperature": 0.7
}
```

**Response:**
```json
{
    "answer": "Para regar tu menta correctamente, mantén el suelo húmedo pero no encharcado...",
    "model_used": "microsoft/Phi-3.5-vision-instruct",
    "tokens_generated": 127,
    "processing_time_ms": 2341.5
}
```

### **3. Health Check**
```http
GET /v1/health
```

**Response:**
```json
{
    "is_healthy": true,
    "uptime_seconds": 1234.56,
    "version": "1.0.0",
    "models": [
        {
            "model": "sentence-transformers/all-mpnet-base-v2",
            "is_loaded": true,
            "loading_time_ms": 2340.5,
            "memory_usage_mb": 456.7
        },
        {
            "model": "microsoft/Phi-3.5-vision-instruct",
            "is_loaded": true,
            "loading_time_ms": 45678.2,
            "memory_usage_mb": 2345.6
        }
    ]
}
```

## 🐍 **Uso con Django**

### **Ejemplo en Django `ai_models/views.py`:**

```python
import httpx
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

AI_SERVICE_URL = "http://localhost:8002"

@api_view(['POST'])
def llm_chat_view(request):
    """Endpoint Django que consume el B4B service"""
    
    try:
        question = request.data.get('question', '')
        
        # 1. Generar embedding con el B4B service
        embedding_response = httpx.post(
            f"{AI_SERVICE_URL}/v1/embeddings",
            json={"text": question},
            timeout=30.0
        ).json()
        
        embedding = embedding_response['vector']
        
        # 2. Buscar en Supabase usando el embedding
        context_chunks = search_in_supabase(embedding)
        
        # 3. Generar respuesta con el B4B service
        chat_response = httpx.post(
            f"{AI_SERVICE_URL}/v1/chat/generate",
            json={
                "query": question,
                "context": [chunk['content'] for chunk in context_chunks]
            },
            timeout=60.0
        ).json()
        
        return Response({
            "question": question,
            "answer": chat_response['answer'],
            "sources": context_chunks,
            "models_used": {
                "embeddings": embedding_response['model_used'],
                "llm": chat_response['model_used']
            },
            "processing_times": {
                "embedding_ms": embedding_response.get('processing_time_ms'),
                "llm_ms": chat_response.get('processing_time_ms')
            }
        })
        
    except Exception as e:
        return Response(
            {"error": f"Error processing request: {str(e)}"},
            status=500
        )

def search_in_supabase(embedding, threshold=0.5, limit=5):
    """Buscar vectores similares en Supabase"""
    # Implementación de búsqueda vectorial con pgvector
    supabase.rpc('search_botanical_knowledge', {
        'query_embedding': embedding,
        'match_threshold': threshold,
        'max_results': limit
    }).execute()
    
    return response.data
```

## 🚀 **Iniciar el Servicio**

```bash
# 1. Instalar dependencias
cd ai_rag_service
pip install -r requirements.txt

# 2. Iniciar servicio
python main_refactored.py

# 3. O con uvicorn
uvicorn main_refactored:app --host 0.0.0.0 --port 8002 --reload
```

## 🧪 **Probar el Servicio**

```bash
# Ejecutar test simple
python test_refactored.py

# O probar con curl
curl -X POST "http://localhost:8002/v1/embeddings" \
     -H "Content-Type: application/json" \
     -d '{"text": "test text"}'

curl -X POST "http://localhost:8002/v1/chat/generate" \
     -H "Content-Type: application/json" \
     -d '{"query": "hello", "context": ["test context"]}'
```

## 🔧 **Ventajas de la Refactorización**

✅ **Arquitectura Limpia**: Separación clara entre dominio, aplicación e infraestructura  
✅ **Backend for Backend**: Diseñado específicamente para ser consumido por Django  
✅ **Modelos Cargados una vez**: Optimización con lifespan events  
✅ **Sin Dependencias de BD**: Django maneja Supabase, este servicio solo hace IA  
✅ **Contratos Claros**: DTOs Pydantic para validación  
✅ **Logging y Monitoring**: Tiempos de procesamiento y estado de modelos  
✅ **Escalabilidad**: Fácil añadir nuevos modelos o endpoints  

## 📝 **Notas Importantes**

- **Modelos cargados al inicio**: Los modelos se cargan una vez y se reutilizan
- **Timeouts configurados**: 10 minutos para carga de modelos, timeouts por request
- **Memory management**: Uso de `psutil` para monitorizar memoria
- **Error handling**: Respuestas de error consistentes
- **CORS configurado**: Ajustar origins para producción

Este servicio está diseñado para ser **stateless** y **escalable**, perfecto para microservicios de IA en arquitecturas híbridas Django + FastAPI.