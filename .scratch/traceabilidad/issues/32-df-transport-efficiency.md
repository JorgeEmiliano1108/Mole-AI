# 32: RNF-DF-02: Eficiencia de transporte y latencia ≤2 s online

Status: ready-for-agent

## Requisito

- **ID:** RNF-DF-02
- **Capa:** Flujo de datos y sincronización
- **Tipo:** RNF
- **Texto:** Las cargas útiles de telemetría deben estar empaquetadas y comprimidas (JSON/Binario). La latencia total del viaje de datos, incluyendo consulta RAG y respuesta del LLM, no debe exceder los 2 segundos en modo online.

## Veredicto

⚠️ PARCIAL — Empaquetado binario/JSON compacto OK; sin compresión HTTP ni SLO ≤2 s verificado.

## Evidencia

- Empaquetado BLE binario 11-31 B: `microservices/esp32_node/main/fee2_frame.c:30-94`.
- JSON compacto edge: `microservices/esp32_node/main/payload_builder.c:13-72`.
- No se encontró compresión HTTP (gzip/deflate/CBOR/Protobuf) en payloads de telemetría.
- Timeouts actuales 30-120 s; sin benchmark de latencia RAG+LLM ≤2 s.

## Delta (matriz ideal vs. estado implementado)

Empaquetado cumple; compresión y latencia total RAG+LLM no implementadas ni medidas.

## Nota normativa / riesgo

TLS intacto en ESP32 (`transport_layer.c:174-175`). BLE no transporta PII/token.

## Siguiente paso sugerido

Agregar compresión en transporte HTTP y definir/verificar SLO de latencia ≤2 s para pipeline online.
