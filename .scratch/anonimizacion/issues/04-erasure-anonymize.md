# 04: B4: Modificar `purge_user_data` para anonimizar en lugar de eliminar

Status: completed

## Requisito

Al ejercerse el derecho de cancelación, los training assets deben anonimizarse (pseudónimo `purged_<uuid>`) en lugar de eliminarse, preservando el conocimiento agrotécnico.

## Acceptance criteria

- [x] `purge_user_data` llama a `export_user_dataset(..., purged=True)` antes de borrar filas vivas.
- [x] Eliminación física de `TrainingDocument`/`TrainingImage` original después del export.
- [x] `AIDiagnostic` se exporta anonimizado y luego se elimina (SET_NULL preserva datos científicos vía `UserPlant`/`Diagnostic` relacionados).
- [x] Tests: tras purga, `TrainingDatasetAnon` contiene registros con `purged=True` y sin PII.

## Blocked by

- `03-mirror-table-pipeline`.

## Notas

- 2026-10-04 (agente): orden crítico respetado (anonimizar → borrar). Se añadió `counts["training_anon_records"]` al retorno de `purge_user_data`.

