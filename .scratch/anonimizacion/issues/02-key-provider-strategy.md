# 02: B2: Implementar KeyProvider y Anonymizer con HMAC-SHA256

Status: completed

## Requisito

Reemplazar `core_backend/utils/privacy.py::anonymize_id` por una familia de clases HMAC inyectables.

## Acceptance criteria

- [x] Interfaz `KeyProvider` con implementación `EnvKeyProvider`.
- [x] Clase `Anonymizer` con `pseudonymize(value: str) -> str` usando HMAC-SHA256.
- [x] Manejo de error si la llave no está configurada (fail-closed).
- [x] Tests con llave dummy; verificar determinismo y que cambio de llave cambia salida.
- [x] Refactor de `microservices/mole_vision/app/core/privacy.py` para usar HMAC con `ANONIMIZACION_KEY`.

## Blocked by

- `01-adr-anonimizacion`.

## Notas

- 2026-10-04 (agente): `KeyProvider`/`EnvKeyProvider`/`Anonymizer` viven en `apps/training_data/anonymization.py`; `AnonymizationService` los usa. `utils/privacy.py` delega en `Anonymizer`. MS1 `mole_vision/app/core/privacy.py` ahora usa HMAC-SHA256 con la env var (fail-closed si falta). Rotación sigue pendiente (ADR-0012 §1.5).

