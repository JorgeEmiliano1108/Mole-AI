# PRD — Anonimización criptográfica de datasets de reentrenamiento

**Feature:** `anonimizacion`  
**Fecha:** 2026-10-02  
**Estado:** Aprobado por directriz ejecutiva.  
**Objetivo:** Cumplir LFPDPPP al desvincular criptográficamente los registros de plagas/imágenes/documentos de entrenamiento de los identificadores personales de los usuarios, reemplazando `SET_NULL` + SHA-256 sin sal por HMAC-SHA256 con llave rotable inyectada por env var.

---

## Problem Statement

Actualmente:
- `anonymize_id()` usa SHA-256 **sin sal** (`core_backend/utils/privacy.py`), lo cual es reversible por fuerza bruta para UUIDs de rango acotado.
- `TrainingDocument.uploaded_by` y `TrainingImage.uploaded_by` usan `SET_NULL` al borrar usuario, pero dejan campos PII como `original_name` y permiten reidentificación cruzada con otros datos.
- `purge_user_data()` elimina los training assets del usuario, impidiendo retener un dataset anonimizado para reentrenamiento.
- `AIDiagnostic.user` permanece como FK viva.

Esto viola el principio de anonimización de la LFPDPPP para datos usados en reentrenamiento de modelos.

## Solution

1. Reemplazar `anonymize_id()` por **HMAC-SHA256** con `ANONIMIZACION_KEY` inyectada vía env var (Strategy + KeyProvider inyectable).
2. Crear tabla espejo **`training_dataset_anon`** (materializada o física) que contiene solo pseudónimos y metadata agrotécnica, **sin FK a usuarios vivos**.
3. Pipeline Celery de exportación que transforma datos vivos a la tabla espejo usando HMAC.
4. Modificar `purge_user_data()` para **anonimizar** training assets en lugar de eliminarlos (pseudónimo `purged_<random>`), preservando el dataset de reentrenamiento.
5. Backfill controlado de `original_name` a nombre limpio `{hash_prefix}.{ext}`; para tablas grandes se ejecuta por lotes vía Celery.

## User Stories

1. Como responsable de privacidad, quiero que los datasets de reentrenamiento no contengan identificadores personales reversibles, para cumplir LFPDPPP.
2. Como científico de datos, quiero que los pseudónimos sean deterministas (mismo input → mismo pseudónimo), para poder hacer joins consistentes en el dataset anonimizado.
3. Como usuario, quiero que al ejercer mi derecho de cancelación mis datos se anonimicen y no se usen para identificarme, pero el conocimiento agrotécnico pueda seguir alimentando modelos.
4. Como operador, quiero rotar la llave de anonimización sin perder datasets históricos, mediante re-exportación controlada.

## Implementation Decisions

- **Algoritmo:** `HMAC-SHA256` con llave secreta `ANONIMIZACION_KEY` (std lib `hmac`, `hashlib`).
- **KeyProvider:** interfaz inyectable para facilitar tests con dummy keys.
- **Determinismo:** mismo identificador + misma llave → mismo pseudónimo (necesario para joins).
- **Tabla espejo:** `training_dataset_anon` con campos: `pseudonym`, `asset_type`, `s3_key_hash`, `category`, `label`, `metrics_json`, `created_at_anon`, `purged`.
- **Erasure:** en `purge_user_data`, antes de borrar un training asset se inserta/actualiza su versión anonimizada con pseudónimo `purged_<uuid>`.
- **Backfill:** Celery task `sanitize_original_names` que procesa lotes de 1,000 registros y actualiza `original_name` → `{sha256_prefix}.{ext}`.
- **Patrones:** Strategy (KeyProvider), Repository (`AnonymizedDatasetRepository`), Command (Celery tasks).

## Testing Decisions

- **Unit tests:** `Anonymizer` con llave dummy: determinismo, cambio de llave produce pseudónimos diferentes, PII no filtra.
- **Integration tests:** export pipeline end-to-end con PostgreSQL + S3 stub; verifica que `training_dataset_anon` no contiene user_id/email/original_name.
- **Erasure tests:** tras `purge_user_data`, el dataset espejo existe con pseudónimo `purged_*` y no permite reidentificación.

## Out of Scope

- Anonimización de datos en tránsito (ya cubierto por TLS).
- Reidentificación de imágenes por contenido visual (out of scope; se asume que el asset en S3 no contiene metadatos PII).

## Further Notes

- ADR dedicado documentará el esquema HMAC y la rotación de llaves.
- `ANONIMIZACION_KEY` nunca se versiona; se inyecta vía env var / secret manager.
