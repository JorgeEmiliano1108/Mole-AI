# PROTOCOLO-C3 — Corridas manuales Edge/Batería (Track C)

**Estado:** código listo (`edge_benchmark.dart`, `MainActivity.kt`, tests).
**Pendiente:** ejecución en hardware real (tarea humana, esta guía).

## Precondiciones

- Dispositivo mid-tier de referencia (p. ej. Samsung SM-A336M) + gama baja
  (MediaTek Helio G35 / Snapdragon serie 400, 3 GB RAM).
- Batería ≥ 60%, cargador **desconectado**, modo avión con WiFi según matriz
  (ideal: misma condición en ambas corridas), brillo fijo 50%.
- App instalada en modo release:
  `flutter install --release -d <device-id>`
- Modelo `plant_mobilenetv2_38.tflite` empaquetado (ver `assets/models/README.md`).

## Corrida de latencia + batería (por dispositivo)

```bash
# Mid-tier, 200 iteraciones (default):
flutter test integration_test/edge_benchmark_test.dart -d <device-id>
# Gama baja (ventana más corta para no agotar):
flutter test integration_test/edge_benchmark_test.dart -d <device-id> \
  --dart-define=BENCH_ITERS=100
```

El test imprime `EDGE_BENCHMARK_JSON: {...}` y guarda copia en el dir temporal
(`EDGE_BENCHMARK_FILE: ...`; extraer con `adb pull` si se requiere archivo).

## Criterios de aceptación

| Métrica | Umbral RNF | Fuente en el reporte |
|---|---|---|
| Latencia total p95 | < 850 ms | `total_p95_ms` |
| Latencia run p95 (solo inferencia) | < 850 ms | `run_p95_ms` |
| Drenaje batería | < 4.5 %/h | `battery_drain_pct_per_hour` |

**Advertencia metodológica:** con ventanas de minutos, `%Intent.ACTION_BATTERY_CHANGED`/
`BATTERY_PROPERTY_CAPACITY` reporta en pasos de 1%: el `% /h` extrapolado es
ruidoso. Si `battery_start_pct == battery_end_pct`, la corrida solo acota el
drenaje (< 1 % / ventana) y debe repetirse con más iteraciones o workload
continuo de 15+ min. Registrar siempre `elapsed_seconds` junto al drenaje.

## Registro de resultados

Copiar el JSON a `.scratch/harness-empirico/reports/edge_<dispositivo>_<fecha>.json`
(esta carpeta **no** se versiona en git) y volcar el veredicto en el issue 05
(matrix-update). Repetir tras cada cambio de modelo o threshold.
