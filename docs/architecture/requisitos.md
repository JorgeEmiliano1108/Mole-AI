# Requisitos del Ecosistema Mole.AI (Global)

## 1. Requisitos Funcionales

### 1.1 Autenticación y Autorización

| ID | Nombre | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|------------------------|----------| ---- |
| RF-01 | Login SSO Supabase | Autenticación centralizada via Supabase | Retorna JWT válido | CRÍTICA |
| RF-02 | Validación JWT Local | Validación offline sin dependencia de red | Validación exitosa | CRÍTICA |
| RF-03 | JWKS Caching | Cacheo de llaves públicas JWKS | TTL 300s configurado | CRÍTICA |
| RF-04 | JWT ES256 | Algoritmo asimétrico de curva elíptica | decode() con ES256 | CRÍTICA |
| RF-05 | HTTPBearer | Extracción de token del header Authorization | Depends(HTTPBearer) | CRÍTICA |
| RF-06 | Validación Cruzada | user_id request vs token match | Retorna 403 si mismatch | CRÍTICA |
| RF-07 | Anti-DoS Lock | Lock asíncrono en JWKS refresh | asyncio.Lock() activo | ALTA |
| RF-08 | Consentimiento LFPDPPP | Registro de consentimiento explícito | data_consent=True | CRÍTICA |

### 1.2 IoT Edge - Sensores

| ID | Nombre | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|------------------------|----------| ---- |
| RF-09 | Ingesta MQTT | Recepción de datos via MQTT (Mosquitto) | Mensajes en tópico mole/+/telemetry | CRÍTICA |
| RF-10 | Edge Node | Suscriptor MQTT en Python (paho-mqtt) | Conexión establecida | CRÍTICA |
| RF-11 | REST Ingest | Endpoint Django /api/sensors/ingest | POST sensor data | CRÍTICA |
| RF-12 | Wide-Table Storage | Almacenamiento flexible de lecturas | Modelo SensorLog | CRÍTICA |
| RF-13 | Time-Series Query | Consultas por plant_id y rango de fechas | Filtrado funcional | ALTA |
| RF-14 | Sensor Types | soil_humidity, air_humidity, air_temperature, uv_index, light_level, ph_level | Campos presentes | CRÍTICA |

### 1.3 mole_vision - Visión Artificial

| ID | Nombre | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|------------------------|----------| ---- |
| RF-15 | Diagnóstico Fitosanitario | Análisis de imagen con CNN TFLite | Retorna species + condition | CRÍTICA |
| RF-16 | Inferencia Async | Ejecución en ThreadPool (run_in_threadpool) | No bloquea event loop | CRÍTICA |
| RF-17 | EXIF Sanitization | Limpieza de metadatos GPS/EXIF | exif.clear() | CRÍTICA |
| RF-18 | Confidence Threshold | Umbral 80% para resultados válidos | confidence >= 0.80 | ALTA |
| RF-19 | Timeout Control | Timeout configurable (default 2s) | asyncio.wait_for() | ALTA |
| RF-20 | Análisis Tira pH | Estimación colorimétrica de pH | Retorna estimated_ph | ALTA |
| RF-21 | Publicación Redis | Evento diagnostic.completed | Publicación exitosa | ALTA |

### 1.4 mole_chat - Chat/RAG

| ID | Nombre | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|------------------------|----------| ---- |
| RF-22 | Chat Conversacional | Endpoint /api/v1/mole-ai/chat | Retorna ChatResponse | CRÍTICA |
| RF-23 | RAG Retrieval | Búsqueda en FAISS vector store | Contexto relevante | CRÍTICA |
| RF-24 | CAG Context | Cacheo de contexto Redis (mqtt:context:{user_id}) | Telemetry cacheada | ALTA |
| RF-25 | Fallback Trefle.io | API botánica si FAISS falla | Busca en internet | MEDIA |
| RF-26 | Multi-Source Context | Agregación sensores + RAG + external | Prompt con 3 fuentes | ALTA |
| RF-27 | Ingesta PDFs | Endpoint /knowledge/ingest-pdf | PDF indexado en FAISS | ALTA |
| RF-28 | Borrado Documentos | DELETE /knowledge/pdf/{doc_id} | doc_id eliminado | MEDIA |
| RF-29 | Source Attribution | Citación de fuentes en respuestas | sources con url | ALTA |
| RF-30 | Anti-Hallucination | System prompt con REGLA DE ORO |No inventa info | CRÍTICA |

### 1.5 mole_report - Reportes PDF

| ID | Nombre | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|------------------------|----------| ---- |
| RF-31 | Generación PDF | Endpoint /reports/generate | PDF generado | ALTA |
| RF-32 | Chart Generation | Gráficos con Chart.js/ReportLab | Visualización de datos | ALTA |
| RF-33 | Historial de Diagnósticos | Consulta por plant_id | Lista de diagnósticos | ALTA |
| RF-34 | Storage S3 | Almacenamiento en MinIO | URL pública/privada | ALTA |
| RF-35 | Download PDF | Endpoint de descarga | Archivo descargable | ALTA |

### 1.6 Core Backend - Base de Conocimiento

| ID | Nombre | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|------------------------|----------| ---- |
| RF-36 | Embeddings Storage | Almacenamiento pgvector (1536 dim) | VectorField | ALTA |
| RF-37 | Semantic Search | Búsqueda semántica similarity | Results relevantes | ALTA |
| RF-38 | Botanical Knowledge CRUD | Create/Read/Update/Delete knowledge | Endpoints REST | ALTA |

---

## 2. Requisitos No Funcionales

### 2.1 Rendimiento

| ID | Nombre | Descripción | Valor Objetivo | Prioridad |
|----|--------|-------------|---------------|----------| ---- |
| RNF-01 | Latencia Diagnóstico | End-to-end visión | ≤1000ms | CRÍTICA |
| RNF-02 | Latencia Chat | Timeout LLM (HF) | ≤30s | CRÍTICA |
| RNF-03 | Latencia Inference TFLite | Timeout inferencia | ≤2s | ALTA |
| RNF-04 | Latencia Health Check | Endpoint /health | ≤100ms | BAJA |
| RNF-05 | Throughput Visión | Requests por segundo | 5 req/s | ALTA |
| RNF-06 | Async I/O | Operaciones redis.asyncio | Todos los adapters async | ALTA |

### 2.2 seguridad

| ID | Nombre | Descripción | Valor Objetivo | Prioridad |
|----|--------|-------------|---------------|----------| ---- |
| RNF-07 | Zero-Trust JWT | Validación local offline | Sin dependencia red | CRÍTICA |
| RNF-08 | PII Hash | Hash SHA-256 en logs | user_id hasheado | CRÍTICA |
| RNF-09 | PII Sanitize Prompt | Sanitización emails/teléfonos | [EMAIL_OCULTO] | CRÍTICA |
| RNF-10 | CORS Config | Orígenes configurables | ORIGEN_PERMITIDO | ALTA |
| RNF-11 | Rate Limiting | Control de tasa | Por endpoint | ALTA |
| RNF-12 | TLS MQTT | Cifrado Mosquitto | Configurado | MEDIO |
| RNF-13 | Redis ACL | Access Control List | Configurado | MEDIO |

### 2.3 Disponibilidad

| ID | Nombre | Descripción | Valor Objetivo | Prioridad |
|----|--------|-------------|---------------|----------| ---- |
| RNF-14 | Health Checks | /health y /healthz | Endpoint público | ALTA |
| RNF-15 | Graceful Degradation | Fallback si servicios fallan | No 500 otomatis | ALTA |
| RNF-16 | Model Pre-loading | Carga TFLite en startup | Al iniciar | ALTA |
| RNF-17 | Redis HA | Sentinel ocluster | Alta disponibilidad | MEDIO |

### 2.4 Compliance (LFPDPPP)

| ID | Nombre | Descripción | Valor Objetivo | Prioridad |
|----|--------|-------------|---------------|----------| ---- |
| RNF-18 | Consent Logs | Registro en BD | data_consent_date | CRÍTICA |
| RNF-19 | No PII Logs | Sin emails/nombres/teléfonos | structlog JSON | CRÍTICA |
| RNF-20 | Legal Disclaimer | Aviso legal en respuestas IA | Campo disclaimer | CRÍTICA |
| RNF-21 | Source Attribution | Citas en RAG | sources con url | ALTA |

### 2.5 Arquitectura

| ID | Nombre | Descripción | Valor Objetivo | Prioridad |
|----|--------|-------------|---------------|----------| ---- |
| RNF-22 | Hexagonal | Puertos y Adaptadores | Capas definidas | ALTA |
| RNF-23 | DI | Inyección en use cases | Dependency injection | ALTA |
| RNF-24 | Environment Config | Variables de entorno | .env file | ALTA |
| RNF-25 | Docker Compose | Orquestación | Redes definidas | ALTA |

---

## 3. Stack Tecnológico por Capa

| Capa | Tecnología | Versión |
|------|-----------|---------|
| **Frontend** | Vanilla JS + Tailwind CSS | - |
| **API Gateway** | Nginx/Traefik | Latest |
| **Backend Web** | Django | 5.0+ |
| **ASGI** | Uvicorn | 0.29.0 |
| **API Services** | FastAPI | 0.110.0 |
| **Base de Datos** | PostgreSQL + pgvector | 16+ |
| **Vector Storage** | pgvector | 0.5+ |
| **Cache/Pub-Sub** | Redis | 7+ |
| **Message Queue** | Celery + RabbitMQ/Redis | Latest |
| **MQTT Broker** | Eclipse Mosquitto | 2 |
| **ML Runtime** | TensorFlow Lite | 2.14.0 |
| **LLM** | HuggingFace (DeepSeek-R1) | - |
| **Auth** | Supabase JWT (ES256) | - |
| **Object Storage** | MinIO (S3) | Latest |
| **ORM** | Django ORM + Pydantic | 2.7+ |
| **Config** | pydantic-settings | 2.0+ |
| **Logging** | structlog | 24.0+ |

---

## 4. Endpoints por Servicio

### 4.1 Django (Puerto 8000)

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | /api/core/sensors/ingest | ⚠️ Por implementar | Ingesta sensores |
| GET | /api/core/sensors/{plant_id} | JWT | Consulta sensores |
| GET | /api/ai_diagnostic/{plant_id} | JWT | Lista diagnósticos |
| POST | /api/ai_diagnostic/analyze | JWT + Celery | Análisis visión async |
| GET | /api/knowledge/search | JWT | Búsqueda semántica |
| POST | /api/knowledge/ | JWT | Crear conocimiento |
| GET | /api/chat/history/{user_id} | JWT | Historial chat |

### 4.2 mole_vision (Puerto 8001)

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | /api/v1/vision/analyze | JWT ES256 | Diagnóstico fitosanitario |
| POST | /api/v1/vision/analyze-ph-strip | JWT ES256 | Análisis tira pH |
| GET | /api/v1/vision/health | Público | Health básico |
| GET | /api/v1/vision/healthz | Público | Health completo |

### 4.3 mole_chat (Puerto 8002)

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | /api/v1/mole-ai/chat | JWT ES256 | Chat RAG+CAG |
| POST | /api/v1/knowledge/ingest-pdf | JWT ES256 | Ingesta PDF |
| DELETE | /api/v1/knowledge/pdf/{doc_id} | JWT ES256 | Borra PDF |
| GET | /api/v1/health | Público | Health check |

### 4.4 mole_report (Puerto 8003)

| Método | Path | Auth | Descripción |
|--------|------|------|------------|
| POST | /api/v1/reports/generate | JWT | Genera PDF async |
| GET | /api/v1/reports/{report_id} | JWT | Consulta reporte |
| GET | /api/v1/reports/download/{report_id} | JWT | Descarga PDF |
| GET | /api/v1/health | Público | Health check |

---

## 5. Variables de Entorno por Servicio

### 5.1 Comunes
| Variable | Default | Descripción |
|----------|---------|-------------|
| SUPABASE_URL | - | URL Supabase |
| SUPABASE_JWT_SECRET | - | JWT Secret |
| POSTGRES_USER | postgres | Usuario BD |
| POSTGRES_PASSWORD | - | Password BD |
| POSTGRES_DB | mole_ai | Nombre BD |
| REDIS_URL | redis://redis:6379/0 | URL Redis |

### 5.2 mole_vision
| Variable | Default | Descripción |
|----------|---------|-------------|
| CNN_MODEL_PATH | /app/models/cnn.tflite | Modelo TFLite |
| CNN_LABELS_PATH | /app/models/labels.json | Labels JSON |
| INFERENCE_TIMEOUT_SECONDS | 2.0 | Timeout |

### 5.3 mole_chat
| Variable | Default | Descripción |
|----------|---------|-------------|
| LLM_MODEL_ID | deepseek-ai/DeepSeek-R1-Distill-Qwen-7B | Modelo HF |
| HUGGINGFACE_API_KEY | - | API Key HF |
| HF_API_TIMEOUT | 30 | Timeout segundos |
| TREFLE_API_TOKEN | - | Token Trefle.io |

### 5.4 mole_report
| Variable | Default | Descripción |
|----------|---------|-------------|
| MS3_S3_ENDPOINT | http://minio:9000 | Endpoint MinIO |
| MS3_S3_BUCKET | reports | Bucket S3 |

---

## 6. Modelo de Datos (Django)

| Modelo | Tabla | Descripción |
|--------|------|------------|
| User | auth_users | Usuarios con Supabase |
| SensorLog | sensor_logs | Lecturas wide-table |
| BotanicalKnowledge | botanical_knowledge | Knowledge + embeddings |
| AIDiagnostic | ai_diagnostics | Resultados diagnósticos |
| ChatHistory | chat_histories | Historial chat |
| Report | reports | Reportes generados |

---

## 7. Diagrama de Flujo Global

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   ESP32   │────▶│  Edge Node │────▶│  Django  │────▶│ Postgres│
│  (MQTT)   │     │  (Python)  │     │  (REST)  │     │pgvector │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
                                            │
                         ┌────────────────────────┼────────────────────────┤
                         ▼                    ▼                    ▼
                   ┌──────────┐        ┌──────────┐        ┌──────────┐
                   │ms1_vision│        │ms2_chat │        │ms3_report│
                   │ (TFLite)│        │ (RAG)   │        │ (PDF)   │
                   └──────────┘        └──────────┘        └──────────┘
                         │                    │                    │
                         ▼                    ▼                    ▼
                   ┌──────────┐        ┌──────────┐        ┌──────────┐
                   │  Redis  │        │  Redis  │        │  MinIO  │
                   │(Pub/Sub)│        │ (CAG)  │        │  (S3)  │
                   └──────────┘        └──────────┘        └──────────┘
```