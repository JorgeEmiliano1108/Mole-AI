# 21: RF-AI-04: Safety Validators toxicológicos

Status: ready-for-human

## Requisito

- **ID:** RF-AI-04
- **Capa:** Agentes e IA
- **Tipo:** RF
- **Texto:** Integrar validadores toxicológicos (Safety Validators) que actúen como un filtro de salida para evitar que el LLM recomiende formulaciones químicas peligrosas o dosis letales para el cultivo.

## Veredicto

✅ CUMPLE — SafetyValidator determinista y gates post-inferencia implementados.

## Evidencia

- `SafetyValidator`: `core_backend/apps/core/services/safety_validator.py:125-271`.
- Catálogos: `safety_rules.yaml`, `docs/safety/agrochemical_limits.json`, `docs/safety/nom059_species.json`.
- Gate chat sync: `core_backend/apps/core/views.py:651-663`.
- Gate chat async: `core_backend/apps/core/tasks.py:121-136`.
- Gate visión: `core_backend/apps/ai_models/tasks.py:87-104`.
- Auditoría: `core_backend/apps/core/services/safety_audit.py:18-47`.

## Delta (matriz ideal vs. estado implementado)

Cumple fail-closed para NOM-059, COFEPRIS y NIST AI RMF. No modela LD50 explícitamente; usa umbrales regulatorios de dosis/aplicación.

## Nota normativa / riesgo

Cumple guardrails de NOM-059/LGEEPA y COFEPRIS. `AuditLog` append-only refuerza trazabilidad.

## Siguiente paso sugerido

Ninguno; evidencia de auditoría. Cerrar como cumplido tras revisión humana.
