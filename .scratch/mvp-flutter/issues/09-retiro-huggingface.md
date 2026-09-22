# 09 — Retiro HuggingFace (NVIDIA + OpenWeather únicos)

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Eliminar restos HF muertos (`DeepSeekVisionClient`, `consultar_phi_vision`,
`HUGGINGFACE_API_KEY`, defaults deepseek/BAAI, campo `LLM_MODEL_ID` chat);
renombrar `WEATHER_API_KEY` → `OPENWEATHER_API_KEY`; ADR-0004; verificar
bug `mole_ai_redis` en report.

## Acceptance criteria

- [x] `grep huggingface/deepseek/BAAI` en `*.py` = 0 (salvo `clean_secrets.py` escáner y docs históricos)
- [x] `utils.py` conserva solo `safe_serialize`; import muerto `views.py:60` fuera
- [x] Django unit 12/12 (9 env + middleware + health + metrics-gap)
- [x] Chat 115 passed + 10 skipped; visión 51 passed; report 26 passed + 6 failed pre-existentes (idénticos HEAD)
- [x] `test_vision_status_view` 4 failed = pre-existentes (idénticos sin mis cambios, `KeyError: status`)
- [x] Fix `ms3_redis_url`: `REDIS_URL` manda, override explícito gana (verificado ambos)
- [x] ADR-0004 escrita

## Blocked by

None - can start immediately

## Comments

- 2026-09-14 (agente): skills `improve-codebase-architecture` (deletion test),
  `tdd` (cambios mínimos + suites), `diagnose` (baseline stash: vision-status
  falla igual sin mis cambios), `grill-with-docs` (ADR-0004), `enforce-compliance`.
- Alcance de Slice 05 reducido: al retirar el duplicado HF, `diagnostic_view` queda
  como vía única pendiente de consolidar (throttle + validación).
