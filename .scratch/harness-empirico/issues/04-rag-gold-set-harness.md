# 04: C4: Implementar harness de alucinaciones RAG con gold set

Status: completed

## Requisito

Crear gold set de 50 queries y un evaluador LLM-as-judge que mida tasa de alucinaciones.

## Acceptance criteria

- [ ] Archivo `gold-set-v1.json` con 50 queries (40% agroquímicos/dosis, 40% patología, 20% ruido/alucinación forzada).
- [ ] Comando Django `run_rag_eval` que consume el gold set y produce reporte.
- [ ] Evaluador LLM-as-judge con stub para CI.
- [ ] Fail-under 5% configurable.

## Blocked by

- `01-harness-protocol`.

## Notas

El gold set se genera híbridamente (draft automático + revisión humana).

