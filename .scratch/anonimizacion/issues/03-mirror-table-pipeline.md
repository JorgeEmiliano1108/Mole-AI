# 03: B3: Crear tabla espejo `training_dataset_anon` y pipeline de exportación

Status: completed

## Requisito

Crear una tabla espejo sin FK a usuarios vivos y un Celery task que exporte datos anonimizados desde `TrainingDocument`, `TrainingImage` y `AIDiagnostic`.

## Acceptance criteria

- [x] Modelo `TrainingDatasetAnon` existente ampliado con campo `purged` (migración `0003_add_anon_purged_flag`).
- [x] Índices en `subject_hash`/`record_type` y `source_fingerprint`.
- [x] `AnonymizationService` con métodos `anonymize_diagnostic/document/image` idempotentes (`find_by_source_fingerprint`).
- [x] Celery task `export_anonymized_dataset` (envuelve `export_user_dataset`).
- [x] El export no incluye `user_id`, `email`, `original_name` ni otros PII.
- [x] Tests de integración con DB de prueba.

## Blocked by

- `02-key-provider-strategy`.

## Notas

- 2026-10-04 (agente): se reutilizó el modelo previo (`record_type`, `source_fingerprint`, `subject_hash`, `feature_payload`, `label`) en lugar de renombrar a los campos del issue; semanticamente equivalente y compatible con tests existentes. La rotación de clave sigue como deuda documentada.

