# MICROSERVICES_SPLIT_ARCHITECTURE.md

**Fecha:** 17 de marzo de 2026  
**Versión:** v1.0-draft  
**Estado:** Borrador inicial  
**Autores:** Equipo de Arquitectura Mole-AI

---

## Resumen Ejecutivo

La división del monolito `ai_rag_service/` en tres microservicios independientes (MS-1 Visión, MS-2 RAG Chat, MS-3 Reportes) elimina el cuello de botella de TFLite (`threading.Lock`), habilita el PATCH a Django y permite escalar cada dominio de IA de forma autónoma. Cada microservicio mantiene la arquitectura hexagonal (puertos y adaptadores), desacopla la integración MQTT mediante un puente Redis y garantiza trazabilidad de fuentes y analítica avanzada.

---

## Diagrama General (C4 ASCII)

```
[App]--(img)-->[MS-1:8001]--(PATCH)-->[Django]
   |                                 ^
   |                                 |
   +--(diagnóstico ctx)-->[MS-2:8002]+
   |                                 |
[ESP32]--(MQTT)-->[edge_node]--(batch POST)-->[Django]
   |                                 |
   +--(MQTT)-->[mqtt_bridge]--(Redis)--+--[MS-2:8002]
                                      |
[Django]--(POST)-->[MS-3:8003]--(Celery/Redis)--+
   |                                 |
   +--(Supabase/pgvector)------------+
```

---

## 1. MS-1: Visión CNN & Gatekeeper

- **Responsabilidad:** Procesar imagen, OOD, inferir pH, hacer PATCH a Django.
- **Stack:** FastAPI (8001), Python 3.11, tflite-runtime, httpx.
- **Hexagonal:**
  - `domain/`: modelos de diagnóstico, puertos vision/diagnóstico.
  - `application/`: `CreateDiagnosticUseCase`, `ExplainPhUseCase`.
  - `infrastructure/`: `CNNVisionClient`, `DeepSeekVisionClient`, `SupabaseDiagnosticRepo`, `DjangoPatchClient` (nuevo).
- **API:**
  - `POST /vision/analyze`, `POST /vision/iot-upload`, `POST /vision/explain-ph`, `POST /vision/upload-url`, `GET /vision/health`.
- **PATCH Django:** Llama a `/api/v1/sensor-data/<id>/` con `{ph_level}` usando `X-Hardware-Api-Key`.
- **Forward a MS-2:** Publica contexto diagnóstico a Redis o HTTP POST a MS-2.

---

## 2. MS-2: Agente RAG + CAG Chat & Trazabilidad

- **Responsabilidad:** Chat agrícola en tiempo real, RAG, inyección de telemetría, citación de fuentes.
- **Stack:** FastAPI/LangChain (8002), sentence-transformers, FAISS/pgvector, Redis.
- **Hexagonal:**
  - `domain/`: modelos chat/RAG, puertos embedding/LLM/vector, servicios de dominio.
  - `application/`: `MoleAIChatUseCase`, `IngestKnowledgeUseCase`, `InputGuardrail`.
  - `infrastructure/`: adaptadores embedding/LLM/vector, `RedisSensorCacheAdapter` (nuevo).
- **API:**
  - `POST /mole-ai/chat`, `POST /embeddings`, `POST /knowledge/ingest-pdf`, `GET /knowledge/sources`, `POST /mole-ai/context`, `GET /mole-ai/health`.
- **MQTT→Redis:** Sidecar escribe telemetría en Redis, MS-2 la consume.
- **Citación:** Respuestas incluyen `sources` con metadatos (autor, libro, URL, confianza).

---

## 3. MS-3: Agente RAG + CAG Reportes Asíncronos

- **Responsabilidad:** Minería histórica, analítica avanzada, generación de PDF con insights RAG+CAG.
- **Stack:** FastAPI + Celery (8003), Redis, WeasyPrint, matplotlib.
- **Hexagonal:**
  - `domain/`: modelos de reporte, puertos report/histórico/insight.
  - `application/`: `GenerateReportUseCase`, `GetReportStatusUseCase`.
  - `infrastructure/`: `CeleryWorkerAdapter`, `WeasyPrintReportGenerator`, `SupabaseHistoricalRepo`.
- **API:**
  - `POST /reports/generate`, `GET /reports/{job_id}/status`, `GET /reports/{job_id}/download`, `GET /reports/health`.
- **RAG+CAG:** Inyecta historial completo, cruza con base botánica, genera PDF con citas.

---

## 4. Guía de Migración de Código (Hexagonal)

- **MS-1:**
  - `application/use_cases/create_diagnostic_use_case.py`, `application/use_cases/explain_ph_use_case.py`, `infrastructure/external/cnn_vision_client.py`, `infrastructure/external/deepseek_vision_client.py`, `infrastructure/ai/phi3_reasoning.py`, `infrastructure/database/supabase_diagnostic_repo.py`, `infrastructure/external/supabase_storage.py`, `domain/ports/diagnostic_ports.py`, rutas vision de `routes.py`, DTOs vision de `contracts.py`, **nuevo** `django_patch_client.py`.
- **MS-2:**
  - `application/use_cases/mole_ai_chat_use_case.py`, `application/use_cases/ingest_knowledge_use_case.py`, `application/guardrails/input_guardrail.py`, `infrastructure/ai/embeddings.py`, `infrastructure/ai/llm.py`, `infrastructure/ai/vector_store.py`, `infrastructure/ai/model_manager.py`, `infrastructure/external/botanical_gateway.py`, `infrastructure/database/supabase_knowledge_repo.py`, `infrastructure/database/supabase_botanical_repo.py`, `infrastructure/data/pdf_parser.py`, `infrastructure/api/knowledge_routes.py`, servicios de dominio chat/RAG, rutas chat de `routes.py`, DTOs chat de `contracts.py`, **nuevo** `redis_sensor_cache.py`.
- **MS-3:**
  - Net-new, referencia patrones de consulta y citación de los anteriores.
- **Compartidos:**
  - `domain/models.py`, `domain/interfaces.py`, `domain/services/validator_service.py`, `domain/security/`, `domain/exceptions/`, `app/dependencies.py`, `infrastructure/ai/auth.py`, `infrastructure/ai/audit.py` (copiados, no symlink).

---

## 5. Matriz de Comunicación

| Origen   | Destino | Método      | Auth                |
|----------|---------|-------------|---------------------|
| App      | MS-1    | HTTP POST   | JWT                 |
| MS-1     | Django  | HTTP PATCH  | X-Hardware-Api-Key  |
| MS-1     | MS-2    | Redis/HTTP  | X-API-Key           |
| Django   | MS-2    | HTTP POST   | MOLE_AI_API_KEY     |
| MQTT Br. | Redis   | Directo     | Interno             |
| MS-2     | Redis   | Directo     | Interno             |
| Django   | MS-3    | HTTP POST   | X-API-Key           |
| MS-3     | Supabase| HTTP GET    | Service Role Key    |
| MS-3     | Redis   | Celery      | Interno             |

---

## 6. Verificación y Pruebas

- Cada MS expone `/health`.
- E2E: imagen → MS-1 → PATCH Django → contexto a MS-2 → chat con citas.
- Carga: uploads concurrentes a MS-1 sin Lock.
- MQTT bridge: sensor → Redis → chat incluye telemetría.
- Reporte: job → PDF con insights y citas.
- Rollback: imagen monolito antiguo retenida, DNS switch <5min.

---

**Fin del documento.**
