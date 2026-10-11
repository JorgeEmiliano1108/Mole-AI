# 26: RF-DB-03: Base de datos vectorial FAISS o Chroma

Status: wontfix

## Requisito

- **ID:** RF-DB-03
- **Capa:** Bases de datos
- **Tipo:** RF
- **Texto:** Uso de FAISS o Chroma para indexar y consultar por similitud los embeddings generados por el Web Mining.

## Veredicto

❌ NO IMPLEMENTADO — No hay FAISS/Chroma; vector store real es pgvector.

## Evidencia

- Test skipped: `microservices/mole_report/tests/test_smoke.py:14-18` ('FAISS será reemplazado por pgvector en Fase 2').
- Vector store operativo: `core_backend/apps/core/models.py:17,62` (`VectorField`), `microservices/mole_chat/app/infrastructure/adapters/pgvector_store.py`.
- ADR-0008 y tesis §4.2.1 documentan exclusión de Web Mining/FAISS.

## Delta (matriz ideal vs. estado implementado)

Discrepancia estructural: FAISS/Chroma vs. pgvector.

## Nota normativa / riesgo

Discrepancia de arquitectura/alcance, no normativa.

## Siguiente paso sugerido

Decisión arquitectónica: migrar a FAISS/Chroma o aceptar pgvector como vector store y actualizar la matriz.

## Decision 2026-10-02

Status actualizado a `wontfix` tras directriz ejecutiva: pgvector/Store-and-Forward aprobados o MCP requiere implementación.
