# 19: RF-AI-02: Chain-of-Thought (CoT) en el LLM

Status: ready-for-agent

## Requisito

- **ID:** RF-AI-02
- **Capa:** Agentes e IA
- **Tipo:** RF
- **Texto:** El LLM debe emplear la técnica de Chain-of-Thought (CoT) para forzar un desglose lógico de su razonamiento antes de emitir un diagnóstico, fusionando los datos del sensor y el modelo visual.

## Veredicto

❌ NO IMPLEMENTADO — Los prompts no solicitan razonamiento paso a paso.

## Evidencia

- Prompt agrónomo: `microservices/mole_chat/prompts/agronomist.yaml:1-17` (sin CoT).
- Prompt visión: `microservices/mole_vision/app/infrastructure/adapters/nvidia_vision_adapter.py:23-55` (solo JSON estructurado).
- Caso de uso chat: `microservices/mole_chat/app/application/use_cases/chat_usecase.py:15-21` (regla anti-alucinación, no CoT).

## Delta (matriz ideal vs. estado implementado)

El requisito exige desglose lógico explícito previo al diagnóstico. El código genera respuestas directas.

## Nota normativa / riesgo

NIST AI RMF recomienda explicabilidad. Falta de CoT debilita trazabilidad del razonamiento agronómico.

## Siguiente paso sugerido

Actualizar prompts de chat y visión para forzar Chain-of-Thought, o documentar decisión de no usarlo.
