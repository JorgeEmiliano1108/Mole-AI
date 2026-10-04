# ADR-0012: Anonimización de datasets de entrenamiento (HMAC-SHA256 + tabla espejo)

- **Fecha:** 2026-10-04
- **Estado:** Aceptado (parcial: esquema + servicio; pipeline de purga pendiente)
- **Contexto:** `.scratch/anonimizacion/PRD.md` y `.scratch/traceabilidad` (RNF-DB-02) exigen que los datos de entrenamiento no conserven PII. El borrado directo destruye valor de entrenamiento; se adopta tabla espejo anonimizada.

## 1. Decisión

1. **Tabla espejo `training_dataset_anon`** (`core_backend/apps/training_data/models.py`, migración `0002_trainingdatasetanon.py`): `record_type`, `source_fingerprint` (HMAC del ID fuente), `subject_hash` (HMAC de `user_id|plant_id`, permite agrupar series sin revelar identidad), `feature_payload` (solo telemetría clínica del diagnóstico: label, confianza, pvu_reason, metadata, fecha), `label`, `status`, `anonymized_at`.
2. **Sin PII por construcción:** sin FK de usuario, sin `image_path`, sin nombres originales. Derivación directa del payload de `AIDiagnostic`.
3. **HMAC-SHA256 con `ANONIMIZACION_KEY` inyectada por entorno** (`core_backend/apps/training_data/anonymization.py::AnonymizationService`); fail-fast (`ImproperlyConfigured`) si falta la clave.
4. **Repository Pattern:** puerto `AnonymizationRepository` + `DjangoAnonymizationRepository` (`core_backend/apps/training_data/repositories.py`); la persistencia es reemplazable sin tocar la lógica.
5. **Alcance explícito pendiente (no parte de esta decisión):** task Celery `export_anonymized_dataset`, `purge_user_data` → anonimizar-en-lugar-de-borrar (`apps/authentication/erasure.py` sigue borrando), `sanitize_original_names`, ADR de key-provider/rotación. La clave legada sin salt (`utils/privacy.py::anonymize_id`, `mole_vision/.../privacy.py`) sigue viva y debe migrarse.

## 2. Consecuencias

- **Positivas:** datasets entrenables sin PII; agrupación temporal por sujeto preservada; contrato testeable (6 tests en `test_anonymization.py`).
- **Negativas / Riesgos:** si `ANONIMIZACION_KEY` se pierde, se rompe la continuidad de `subject_hash` (no es reversible, pero sí estable solo con la misma clave); rotación de clave requiere re-derivación completa — pendiente de diseño.

## 3. Cumplimiento normativo

- **LFPDPPP:** minimización y seudonimización (HMAC con secreto de servidor, no hash reversible ni salt fijo en código). La tabla espejo no contiene datos personales directos.
