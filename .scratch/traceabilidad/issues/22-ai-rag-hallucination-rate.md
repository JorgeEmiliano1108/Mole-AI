# 22: RNF-AI-01: RAG con tasa de alucinaciones <5%

Status: ready-for-agent

## Requisito

- **ID:** RNF-AI-01
- **Capa:** Agentes e IA
- **Tipo:** RNF
- **Texto:** El uso del enfoque Retrieval-Augmented Generation (RAG) debe restringir de forma comprobable la tasa de alucinaciones del LLM a un nivel <5%.

## Veredicto

❌ NO IMPLEMENTADO — No existe gold set ni métrica de alucinaciones.

## Evidencia

- No se encontró harness de evaluación ni tasa documentada.
- Mitigaciones heurísticas: anti-alucinación en prompt (`microservices/mole_chat/app/application/use_cases/chat_usecase.py:15-21`), router retrieval, `SafetyValidator`.
- ADR-0008 lista métricas pendientes.

## Delta (matriz ideal vs. estado implementado)

El requisito exige una cota medida y comprobable. El sistema solo tiene controles heurísticos y de seguridad.

## Nota normativa / riesgo

NIST AI RMF exige evaluación de riesgos y rendimiento. Sin benchmark no se puede demostrar cumplimiento de la cota <5%.

## Siguiente paso sugerido

Construir gold set de evaluación y harness que mida tasa de alucinaciones; definir umbral de aceptación y CI.
