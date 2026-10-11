# 18: RF-AI-01: Arquitectura agéntica con Orquestador, Telemetría y Visión

Status: ready-for-agent

## Requisito

- **ID:** RF-AI-01
- **Capa:** Agentes e IA
- **Tipo:** RF
- **Texto:** La arquitectura agéntica debe incluir un 'Agente Orquestador' que coordine al 'Agente de Telemetría' y al 'Agente de Visión' para consolidar el estado de la planta.

## Veredicto

❌ NO IMPLEMENTADO — No existen agentes nombrados ni orquestador sensor+visión.

## Evidencia

- No se encontraron clases `TelemetryAgent`, `VisionAgent`, `OrchestratorAgent`.
- Fusión parcial sensor→chat: `core_backend/apps/ai_models/services.py:50-89`, `microservices/mole_chat/app/application/use_cases/chat_usecase.py:69-88`.
- Visión aislada: `core_backend/apps/ai_models/tasks.py:60-142`.
- Router LangGraph solo chat: `microservices/mole_chat/app/application/orchestration/graph.py:44-127`.

## Delta (matriz ideal vs. estado implementado)

La orquestación real es monolítica/servicios REST. No hay topología de agentes como describe la matriz.

## Nota normativa / riesgo

NIST AI RMF favorece roles y trazabilidad explícitos. La ausencia dificulta atribuir responsabilidad en diagnósticos multimodales.

## Siguiente paso sugerido

Diseñar e implementar agentes explícitos (orquestador, telemetría, visión) o ajustar la matriz a la arquitectura REST actual.
