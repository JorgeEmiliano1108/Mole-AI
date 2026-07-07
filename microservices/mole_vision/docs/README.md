# Documentación — mole_vision

## Archivos

| Archivo | Contenido |
|---------|-----------|
| [`README.md`](../README.md) | Descripción general, stack, arquitectura, endpoints, tests, estado auditoría |
| [`requisitos.md`](requisitos.md) | Requisitos funcionales (RF) y no funcionales (RNF), ontología `PlantDiagnosis`, deuda técnica |
| [`audit.md`](audit.md) | Auditoría de seguridad y cumplimiento (LFPDPPP, ISO 25000, MoproSoft, NOM-059) |

## Resumen

mole_vision es el microservicio de detección de plagas y enfermedades del ecosistema Mole-AI. Usa **NVIDIA NIM (Llama 3.2 Vision‑Instruct)** como único motor de inferencia. Mock disponible solo en `tests/fakes/` para CI.

- **Motor de visión**: NVIDIA NIM (OpenAI-compatible)
- **Ontología**: `PlantDiagnosis` (15 campos: especie, etapa, plaga, severidad, progresión, recomendaciones)
- **Auth**: JWT HS256 (sin JWKS remoto)
- **Resilience**: tenacity (3 retries, backoff 2-15s)
- **NOM-059**: ✅ Dos capas de protección (prompt LLM + verificación post-inferencia)
- **Pruebas**: 51 tests, 90% cobertura
- **CI/CD**: lint → test (cov≥60) → license gate → build
