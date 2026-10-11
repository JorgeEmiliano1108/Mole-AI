# 15: RF-MS-03: Embeddings con Transformers a base de datos vectorial

Status: wontfix

## Requisito

- **ID:** RF-MS-03
- **Capa:** Microservicios y Web Mining
- **Tipo:** RF
- **Texto:** Debe convertir los chunks semánticos en embeddings (vectores) utilizando modelos Transformers y enviarlos a la base de datos vectorial.

## Veredicto

⚠️ PARCIAL — Embeddings y vector store operativos, pero con pgvector y fuente manual/S3.

## Evidencia

- Modelo de embeddings: `microservices/mole_chat/app/core/config.py:73` (`nvidia/nv-embedqa-e5-v5`).
- Generación e inserción: `microservices/mole_chat/app/infrastructure/adapters/pgvector_store.py:137-202`.
- Tabla pgvector: `rag_knowledge_chunks` con `embedding vector(1024)`.

## Delta (matriz ideal vs. estado implementado)

Discrepancia estructural: la matriz exige FAISS/Chroma; el vector store real es PostgreSQL + pgvector. La fuente no es Web Mining.

## Nota normativa / riesgo

Uso de proveedor externo (NVIDIA NIM) traslada gestión del modelo fuera del perímetro; mantener medidas LFPDPPP (sin PII en chunks).

## Siguiente paso sugerido

Decisión arquitectónica: migrar a FAISS/Chroma o aceptar pgvector como vector store y actualizar la matriz.

## Decision 2026-10-02

Status actualizado a `wontfix` tras directriz ejecutiva: pgvector/Store-and-Forward aprobados o MCP requiere implementación.
