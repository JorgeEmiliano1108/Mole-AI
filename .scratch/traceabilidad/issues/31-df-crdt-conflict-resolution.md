# 31: RNF-DF-01: CRDTs o marcas de tiempo vectoriales

Status: wontfix

## Requisito

- **ID:** RNF-DF-01
- **Capa:** Flujo de datos y sincronización
- **Tipo:** RNF
- **Texto:** El flujo de sincronización de datos debe implementar Tipos de Datos Replicados Libres de Conflictos (CRDTs) o marcas de tiempo vectoriales para conciliar discrepancias entre la DB local y la nube sin pérdida de información.

## Veredicto

❌ NO IMPLEMENTADO — Store-and-Forward + cursor + deduplicación por timestamp.

## Evidencia

- ADR-0008: 'CRDTs → Store-and-Forward'.
- Cero referencias a `CRDT`, `vector_clock`, `version_vector`.
- Cursor `applied_up_to`: `edge_node/store_forward_daemon.py:196-223`.
- Deduplicación por timestamp: `core_backend/apps/core/services/edge_ingest.py:24-100`.
- Server-wins: `core_backend/apps/core/views.py:293-294`.

## Delta (matriz ideal vs. estado implementado)

Discrepancia estructural: CRDTs/relojes vectoriales vs. Store-and-Forward con resolución server-wins.

## Nota normativa / riesgo

Data Integrity: server-wins puede perder escrituras locales en mismo timestamp. Integridad limitada a anti-replay 300 s, cursor monótono y SQLCipher local.

## Siguiente paso sugerido

Decisión arquitectónica: implementar CRDTs/versionado vectorial o renombrar requisito a Store-and-Forward en la matriz/tesis.

## Decision 2026-10-02

Status actualizado a `wontfix` tras directriz ejecutiva: pgvector/Store-and-Forward aprobados o MCP requiere implementación.
