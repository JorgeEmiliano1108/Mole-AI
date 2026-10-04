# PRD — Harness empírico de benchmarks críticos

**Feature:** `harness-empirico`  
**Fecha:** 2026-10-02  
**Estado:** Aprobado por directriz ejecutiva.  
**Objetivo:** Medir con precisión científica los umbrales no funcionales críticos que hoy solo están en la matriz: latencia de inferencia Edge <850 ms, drenaje de batería <4.5%/h y tasa de alucinaciones RAG <5%.

---

## Problem Statement

La auditoría de trazabilidad encontró que:
- `edge_ai.dart` mide latencia con `Stopwatch` pero no valida el umbral de 850 ms.
- No existe medición de drenaje de batería.
- No existe gold set ni métrica de alucinaciones para RAG.

Sin evidencia empírica, los RNF cuantitativos no son comprobables ni auditable.

## Solution

Crear tres harness independientes, todos bajo `.scratch/harness-empirico/`:

1. **Edge Latency Harness** (Flutter `integration_test`):
   - Strategy `InstrumentedEdgeInterpreter` que envuelve `TfliteEdgeInterpreter`.
   - Mide preprocess + run + threshold por separado.
   - Reporta P50/P95/P99 y compara contra 850 ms.
   - Se ejecuta en dispositivo real (Samsung SM-A336M como referencia mid-tier y un dispositivo gama baja para worst-case).

2. **Battery Harness** (Flutter + Android platform channel):
   - MethodChannel propio lee `BatteryManager` antes y después de un bucle de inferencias.
   - Calcula `%/h` de drenaje.
   - Documenta que la validación oficial se hace en dispositivo gama baja (MediaTek Helio G35 / Snapdragon 400 series, 3 GB RAM).

3. **RAG Hallucination Harness** (Django command + Python):
   - Gold set de 50 queries híbrido: 40% agroquímicos/dosis, 40% patología, 20% ruido/alucinación forzada.
   - Evaluador LLM-as-judge (NVIDIA NIM en rol evaluador) califica cada respuesta.
   - Métrica: tasa de alucinaciones = respuestas incorrectas o inseguras / total.
   - Fail-under 5% en CI con stub de NIM para evitar costo en tests.

## User Stories

1. Como QA, quiero saber si la inferencia local cumple <850 ms en un dispositivo real, para validar el MVP en campo.
2. Como arquitecto, quiero medir el drenaje de batería en condiciones de peor caso, para no entregar un producto que agote el teléfono del agricultor.
3. Como responsable de seguridad, quiero una tasa medida de alucinaciones del RAG, para demostrar cumplimiento de RNF-AI-01.
4. Como científico de datos, quiero un gold set versionado para reproducir la evaluación en cada release.

## Implementation Decisions

- **Edge latency:** reutilizar `EdgeInterpreter` Strategy; agregar `InstrumentedEdgeInterpreter` que no cambia semántica, solo registra tiempos.
- **Battery:** platform channel Dart ↔ Kotlin sin agregar dependencias de terceros.
- **RAG eval:** comando Django `python manage.py run_rag_eval --gold-set path --output path`.
- **Gold set formato:** JSON con campos `id`, `category`, `query`, `expected_route`, `expected_safety_block`, `reference_answer`, `judge_criteria`.
- **Reportes:** CSV/JSON en `.scratch/harness-empirico/reports/`; no se versionan en git.
- **CI:** solo se ejecuta el harness con stub; el benchmark real es manual en dispositivo.

## Testing Decisions

- **Edge:** tests de integración con `FakeEdgeInterpreter` validan que el harness mide y reporta correctamente.
- **Battery:** tests del MethodChannel con mock de batería.
- **RAG:** tests unitarios del evaluador con respuestas predefinidas; tests de integración con stub de NIM.

## Out of Scope

- Automatizar el benchmark de batería en CI (requiere hardware real).
- Entrenar ni modificar los modelos según resultados.

## Further Notes

- El gold set se genera de forma híbrida: draft automático de 50 queries basado en `agrochemical_limits.json` y `nom059_species.json`, revisado por un humano antes de convertirse en fuente de verdad.
