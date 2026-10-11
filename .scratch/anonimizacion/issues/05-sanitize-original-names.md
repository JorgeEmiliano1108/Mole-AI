# 05: B5: Backfill controlado de `original_name` y validación final

Status: ready-for-agent

## Requisito

Limpiar el campo `original_name` en `TrainingDocument` e `TrainingImage` para evitar filtración de nombres de archivo personales.

## Acceptance criteria

- [ ] Celery task `sanitize_original_names(batch_size=1000)`.
- [ ] Actualiza `original_name` → `{hash_prefix}.{ext}`.
- [ ] Ejecutable por lotes con resumen de progreso.
- [ ] Validación final: query que demuestre que no quedan `original_name` con patrones PII comunes.

## Blocked by

- `04-erasure-anonymize`.

## Notas

Para tablas masivas, el backfill se ejecuta en horario de baja demanda.

