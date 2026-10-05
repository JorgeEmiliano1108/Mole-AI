# 28: RNF-DB-02: Anonimización en PostgreSQL para reentrenamiento

Status: completed

## Requisito

- **ID:** RNF-DB-02
- **Capa:** Bases de datos
- **Tipo:** RNF
- **Texto:** Los datos almacenados en PostgreSQL utilizados para reentrenar modelos futuros deben ser anonimizados, desvinculando obligatoriamente los registros de plagas de los identificadores personales de los usuarios (LFPDPPP).

## Veredicto

✅ COMPLETADO PARA MVP — Pipeline de anonimización operativo.

## Evidencia

- `AnonymizationService` + `KeyProvider`/`EnvKeyProvider`/`Anonymizer`: `apps/training_data/anonymization.py`.
- Tabla espejo `TrainingDatasetAnon` con `purged` flag: migración `0003_add_anon_purged_flag`.
- Export incremental en `analyze_vision_async` (`apps/ai_models/tasks.py:123-127`).
- Export previo a borrado ARCO en `purge_user_data` (`apps/authentication/erasure.py:61-63`).
- Celery task `export_anonymized_dataset` (`apps/training_data/tasks.py:177-200`).
- Tests: `test_anonymization_wire.py`.
- `uploaded_by` es `SET_NULL` al borrar usuario.

## Delta (matriz ideal vs. estado implementado)

Pipeline funcional; la rotación de clave HMAC sigue pendiente de diseño (ADR-0012 §1.5, issue 33).

## Nota normativa / riesgo

LFPDPPP: los registros de entrenamiento ahora se desvinculan de PII vía HMAC con clave de entorno; los originales se eliminan tras la exportación.

## Siguiente paso sugerido

- Rotación de clave HMAC (KeyProvider con versión + re-derivación).
- Issue 05: backfill controlado de `original_name` y validación final.
