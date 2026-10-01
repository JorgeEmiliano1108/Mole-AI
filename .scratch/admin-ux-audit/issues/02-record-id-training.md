# Issue 02 — Campo record_id en listados de training

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — `GET training/documents/` e `images/` devuelven `record_id`; `test_training_upload.py` pasa.
- **Priority:** high
- **Skill:** tdd

## Problema
`GET training/documents/` devuelve el campo `id`, pero `KnowledgeAsset.fromJson` lo lee como `record_id`. Resultado: los items listados muestran `recordId = "null"`.

## Evidencia
- `core_backend/apps/training_data/serializers.py:96-100` (devuelve `id`)
- `mobile/lib/features/admin/admin.dart:197-201` (`record_id`)

## Solución
Exponer `record_id` (alias de `id`) en `TrainingDocumentSerializer` e `TrainingImageSerializer`.

## Tests
- Backend serializer test: el output incluye `record_id` igual a `id`.
- Flutter widget test opcional: lista renderiza IDs correctos.

## Criterio de aceptación
- `GET training/documents/` devuelve `record_id` en cada resultado.
