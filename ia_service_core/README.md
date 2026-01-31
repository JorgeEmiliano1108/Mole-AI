# Mole AI - Microservicio de Inteligencia Artificial

Microservicio especializado en diagnóstico agrícola multimodal con capacidades de RAG (Retrieval-Augmented Generation) basado en Ollama.

## Arquitectura

- **Framework**: FastAPI
- **LLM**: llama3.1:8b-instruct (Ollama)
- **Embeddings**: nomic-embed-text
- **Vector Store**: FAISS (local)
- **Comunicación**: REST API (JSON)

## Requisitos Previos

1. Python 3.9+
2. Ollama instalado y corriendo
   ```bash
   # Instalar Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Iniciar servicio Ollama
   ollama serve
   ```

## Instalación

### 1. Clonar el proyecto
```bash
git clone <repo-url>
cd ia_service_core
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Descargar modelos Ollama
```bash
# LLM principal (8B parameters - óptimo para edge/local)
ollama pull llama3.1:8b-instruct

# Modelo de embeddings ligero
ollama pull nomic-embed-text
```

### 4. Verificar configuración
```bash
./check_models.sh
```

## Ejecución

### Desarrollo
```bash
uvicorn src.infrastructure.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción (Docker)
```bash
docker build -t mole-ai-service .
docker run -p 8000:8000 --env-file .env mole-ai-service
```

## Endpoints Principales

### RAG - Retrieval Augmented Generation

#### POST /api/rag/query
Realiza consultas con contexto enriquecido.

```json
{
  "query": "¿Qué tratamiento recomiendas para la milpa con plagas?",
  "top_k": 5,
  "context": "Cultivo en región central de México"
}
```

**Respuesta:**
```json
{
  "response": "Basado en los documentos sobre herbolaria mexicana...",
  "sources": [
    {
      "text": "Extracto del documento relevante...",
      "score": 0.89,
      "id": 42
    }
  ],
  "meta": {
    "query": "¿Qué tratamiento recomiendas...",
    "retrieved_docs": 3,
    "model": "llama3.1:8b-instruct"
  }
}
```

#### POST /api/rag/ingest
Ingesta documentos para enriquecer la base de conocimiento.

```json
{
  "documents": [
    {
      "text": "El neem es efectivo contra áfidos en maíz...",
      "source": "herbolaria_mexicana.pdf",
      "title": "Tratamientos con neem",
      "type": "text"
    }
  ]
}
```

#### GET /api/rag/stats
Estadísticas del sistema RAG.

```json
{
  "vector_store": {
    "total_vectors": 1250,
    "dimension": 768,
    "index_type": "FAISS IndexFlatL2"
  },
  "models": {
    "llm": "llama3.1:8b-instruct",
    "embedding": "nomic-embed-text"
  }
}
```

### API existente

#### POST /api/ask
Endpoint legacy de chat (mantiene compatibilidad).

## Variables de Entorno

Crear archivo `.env`:
```bash
# Base de datos PostgreSQL
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mole_ai_db

# Configuración Ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b-instruct
EMBEDDING_MODEL=nomic-embed-text

# Configuración RAG
RAG_TOP_K=5
RAG_CONTEXT_LENGTH=4000
```

## Estructura del Proyecto

```
ia_service_core/
├── src/
│   ├── domain/                 # Modelos de dominio
│   ├── application/           # Casos de uso
│   ├── infrastructure/
│   │   ├── api/              # Endpoints FastAPI
│   │   ├── external/         # Adaptadores externos (Ollama)
│   │   ├── vector/           # Almacenamiento vectorial FAISS
│   │   └── config/           # Configuración
├── requirements.txt
├── Dockerfile
└── README.md
```

## Flujo RAG

1. **Ingestión**: Documentos → Embeddings → FAISS
2. **Consulta**: Query → Embedding → Búsqueda FAISS → Contexto → LLM
3. **Generación**: Prompt enriquecido → llama3.1 → Respuesta contextual

## Mejoras Posibles

### Corto Plazo (1-2 semanas)
- **Batch processing**: Endpoint para ingestión masiva de PDFs
- **Caching**: Redis cache para consultas frecuentes
- **Chunking inteligente**: División semántica de documentos
- **Metadata filtering**: Búsqueda por categoría/fuente

### Mediano Plazo (1-2 meses)
- **Hybrid search**: Combinar búsqueda semántica + keyword
- **Re-ranking**: Modelo secundario para mejorar precisión
- **Streaming**: Respuestas progresivas del LLM
- **Monitoring**: Métricas de uso y rendimiento

### Largo Plazo (3+ meses)
- **Multi-modal**: Imágenes de sensores + texto
- **Fine-tuning**: Adaptar modelo a dominio agrícola
- **Graph RAG**: Incorporar relaciones entre conceptos
- **Edge deployment**: Optimización para dispositivos de campo

### Mejoras Técnicas Específicas

#### RAG
- **Vector stores alternativos**: ChromaDB, Pinecone (cloud)
- **Embeddings especializados**: Modelos finetuneados en español agrícola
- **Query expansion**: Expandir consultas con sinónimos agrícolas
- **Context compression**: Optimizar tamaño de contexto para LLM

#### Performance
- **Async batch processing**: Procesamiento paralelo de embeddings
- **Model quantization**: Reducir uso de memoria del LLM
- **Load balancing**: Distribución de consultas Ollama
- **Connection pooling**: Optimizar conexiones a base de datos

#### Seguridad
- **API Key rotation**: Sistema de claves temporales
- **Rate limiting**: Límites por usuario/endpoint
- **Input validation**: Validación estricta de consultas
- **Audit logging**: Registro completo de operaciones

#### Operaciones
- **Health checks**: Monitoreo de servicio Ollama
- **Auto-scaling**: Escalado automático basado en carga
- **Backup/Restore**: Persistencia de vectores en S3
- **CI/CD**: Pipeline automático de despliegue

## Integración con Django

### Configuración del consumidor

```python
# Django settings.py
MOLE_AI_CONFIG = {
    'base_url': 'http://localhost:8000',
    'api_key': os.getenv('MOLE_AI_API_KEY'),
    'timeout': 30
}

# Cliente Python
import httpx

class MoleAIClient:
    def __init__(self):
        self.base_url = settings.MOLE_AI_CONFIG['base_url']
        self.headers = {
            'X-API-Key': settings.MOLE_AI_CONFIG['api_key']
        }
    
    async def query_rag(self, query: str, context: str = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/rag/query",
                json={"query": query, "context": context},
                headers=self.headers
            )
            return response.json()
```

## Monitoreo y Logs

### Logs importantes
- `/api/rag/query`: Consultas, documentos recuperados, tiempo de respuesta
- `/api/rag/ingest`: Documentos procesados, errores de embedding
- Ollama connection timeouts, FAISS index operations

### Métricas clave
- Query latency (p50, p95)
- Retrieval precision/relevance
- Document ingestion throughput
- Memory usage (FAISS index size)

## Troubleshooting

### Problemas comunes

#### Ollama no responde
```bash
# Verificar servicio
curl http://localhost:11434/api/tags

# Reiniciar Ollama
pkill ollama && ollama serve
```

#### Error de embeddings
- Verificar modelo: `ollama list`
- Reinstalar: `ollama pull nomic-embed-text`

#### FAISS index corruption
```bash
# Eliminar índice dañado
rm data/vector_store.faiss data/vector_metadata.pkl
# Se recreará automáticamente en el siguiente uso
```

#### Memory errors
- Reducir RAG_TOP_K
- Usar modelo más pequeño: llama3.1:8b → 3b

## Contribución

1. Fork del proyecto
2. Feature branch: `git checkout -b feature/mejora`
3. Tests: `pytest tests/`
4. Commit: `git commit -m "feat: agregar mejora X"`
5. PR con template específico

## Licencia

MIT License - Ver archivo LICENSE