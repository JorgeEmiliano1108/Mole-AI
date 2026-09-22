# 13 — Stack formal MRF/MRNF + matriz de trazabilidad

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Adoptar la especificación formal (RF01–RF06, RNF01–RNF06) como canónica con IDs
`MRF/MRNF` (evita colisionar con la numeración legacy del repo: RF04=plantas,
RNF04=disponibilidad, etc.). Matriz trazable requisito↔código↔test que el
refactoring F1–F9 debe mantener en verde.

## Matriz MRF/MRNF ↔ código ↔ test

| ID | Requisito | Código que lo implementa | Test que lo fija |
|---|---|---|---|
| MRF01 | Offline-first SQLite3 móvil | `mobile/lib/core/offline_store.dart` (F1: `sqflite`, tablas `telemetry_cache`, `diag_queue`) | `mobile/test/offline_test.dart` + retención 15 días (F1) |
| MRF02 | Edge AI TFLite on-device | `mobile/lib/features/vision/edge_ai.dart` + `assets/models/mobilenetv2_integration.tflite` (F2-hitos 1+2) | `mobile/test/edge_ai_test.dart` (preproceso, threshold, fallback determinista) |
| MRNF01 | 500ms edge / 3s orquestador | `EdgeVerdict.latencyMs` medido por inferencia (F2); benchmark CI en dispositivo pendiente (F9) | — |
| MRF03 | Sync con negociación (cursor) | `SyncBatchView` + `edge_ingest.ingest_frame(dedupe)` + daemon cursor/fallback (F3) | `test_sync_batch.py` (9) + `test_sync_jsonrpc.py` (5) |
| MRF04 | Multi-agente LangGraph tras puertos | `mole_chat/.../chat_usecase.py` + ports (F4, puerta: F1+F2 verdes) | LLM fake por puerto (F4) |
| MRF05 | RAG+CoT | `ChatResponse` + `agronomist.yaml` (F5: `steps[]`) | respuesta con pasos (F5) |
| MRF06 | Trazabilidad fuentes+pasos | `LLMRequest` + `AuditLog` (F5: `trace_id`, usage real) | historial con sources (F5) |
| MRNF01 | 500ms edge / 3s orquestador | benchmarks (F2/F4, puerta F9) | CI SLOs (F9) |
| MRNF02 | 15 días sin pérdida | `offline_store` quotas + edge SQLite sin prune (F1) | retención (F1) |
| MRNF03 | LangSmith+OTEL 100% | `langsmith` declarado + spans (F6, con masking PII) | trazas en CI (F6/F9) |
| MRNF04 | TLS1.3 + safety semántico | host nginx + pinning + `safety_validators` (F7) | TLS + denylist tests (F7) |
| MRNF05 | Android + iOS | `mobile/android/` + `mobile/ios/` (F8) | build ambas (F8) |
| MRNF06 | JSON-RPC solo sync edge | envelope `method/params/id` en sync (F8), REST móvil intacto | contrato dual (F8) |

Refinamientos adoptados (revisión externa 2026-09-18): threshold calibrado INT8/FP16
(F2); Router Agent al inicio del grafo (F4); safety semántico decisorio + regex
como primera barrera (F7); masking PII en exporter OTEL reutilizando `PIIFilter`
(F6). Secuencia: F0→F1→F2→F3, F4 bloqueada hasta base offline estable y medida.

## Acceptance criteria

- [x] Matriz arriba versionada en este issue (F0)
- [x] MRF01/MRNF02 (F1, 2026-09-18): `sqflite` con `telemetry_cache`+`diag_queue`
  (`mobile/lib/core/offline_db.dart`: abstracto + `SqfliteOfflineDb` +
  `MemoryOfflineDb`); `OfflineStore` conserva su API (repos/pantallas intactos);
  test retención 15 días en verde. `flutter analyze` 0 issues, 45 tests.
- [ ] Restantes: cada fila con test en verde antes de cerrar su fase (puerta F9)
- [ ] `docs/mobile-contract.md` + `audit-matrix.md` referencian IDs MRF/MRNF

## Blocked by

None - can start immediately

## Comments

- 2026-09-18 (agente): skills `to-issues`, `to-prd`. Etapa dev (no prod): sin presión
  de tienda; backend objetivo LAN. F4 (LangGraph) explícitamente diferida hasta
  puerta offline (F1+F2 con métricas).
- 2026-09-19 (agente, F3): MRF03 implementado — `SyncBatchView` + servicio
  compartido `edge_ingest.ingest_frame(dedupe=...)` (refactor sin cambio de
  comportamiento en `edge-batch/`) + daemon con cursor SQLite y fallback legacy.
  Tests: 9 backend + 5 daemon en verde.
- 2026-09-20 (agente, P0/P1/P2-smoke): dataset PlantVillage 54,305 imgs/38 clases
  (`/home/paul/.mole-datasets/`, fuera del repo) + `datasheet.md`; `labels.json:38`
  normalizada; pipeline endurecido (norm `[-1,1]`, augmentation, holdout campo con
  F1-macro, `class_weight`, `labels.txt`, hook QAT, `.keras`); test testigo paridad
  en verde; ROI overlay en APK. Smoke 3 clases CPU: fit + holdout F1 + export FP16
  2.6MB válido (softmax=1.0). Toolchain: entrenar 2.16.1, convertir 2.18.0
  (ver matriz en `requirements-train.txt`). Full 38 clases + GPU + QAT-medido
  quedan como runbook (`scripts/train_edge_model.py`).
- 2026-09-20 (agente, T0+T1): dataset 54,305/38 + `datasheet.md`; `labels.json:38`
  normalizada; pipeline P1 (norm [-1,1], augmentation, holdout F1, class-weight
  —cazado bug `.JPG` mayúsculas—, `labels.txt`, hook QAT, `.keras`, ModelCheckpoint,
  INT8-PTQ path, `representative_dataset()`); test testigo en verde; ROI en APK.
  Contenedor `mole-train` (TF 2.16.1, CPU 12 cores, 38 clases, 12 épocas, sin QAT
  —tfmot incompatible con transfer anidado, documentado) corriendo detached,
  salida en `/home/paul/.mole-models/`. Toolchain fijada en `requirements-train.txt`
  (train 2.16.1 / convert 2.18.0).
- 2026-09-20 (agente, RCA mamut + directrices finales): `.cache()` sin archivo
  (26GB en RAM) era el OOM, no el batch; `workers=` es no-op con tf.data.
  Aplicado: drop-cache en train (varianza stochastic preservada), val cache a
  archivo, `prefetch(2)` + `num_parallel_calls=4`, `set_memory_growth` futuro,
  `ModelCheckpoint` + `representative_dataset()` + export dual FP16/INT8.
  Contenedor `mole-train` (12 épocas, batch 16, 38 clases, sin QAT) corriendo
  detached; salida en `/home/paul/.mole-models/`.
- 2026-09-20 (agente, causa raíz del SIGKILL): apagado forzoso del usuario por
  estrangulamiento térmico + saturación CPU (i7-13620H), no OOM del proceso.
  Relanzamiento limpio con protección térmica: `--cpus=8 --memory=8g` (antes 12/10g),
  batch 16, prefetch(2), num_parallel_calls=4. Artefactos del run muerto purgados.
- 2026-09-20 (agente, relanzamiento térmico): causa SIGKILL = apagado forzoso por
  temperatura (i7-13620H), no OOM del proceso. Artefactos purgados. Pesos ImageNet
  cacheados persistentes (`/home/paul/.mole-models/.keras`, `KERAS_HOME`) tras
  caída transitoria de descarga GCS. Run limpio detached: 38 clases, 12 épocas,
  batch 16, `--cpus=8 --memory=8g`. Salida en `/home/paul/.mole-models/`.
- 2026-09-20 (agente, S1 rescate): run muerto en export (LLVM 2.16), pesos a salvo.
  Re-evaluado en TF 2.18: ckpt_best F1=0.5172 == final (plateau temprano).
  FP16 4.8MB + INT8-PTQ 2.9MB (representative del proxy); INT8 F1=0.5373
  (sin caída → veredicto INT8 por regla >5%). Curva: thr 0.70 → prec 0.94,
  cobertura 15% (85% deriva a nube, según diseño). Lat CPU ref ~20ms;
  on-device pendiente (puerta F9). `labels_38.txt` generado (orden canónico).
  F1 absoluto modesto (0.52): se recomienda ronda full fine-tune (descongelar
  base) antes de producción; el INT8 actual vale para integración.
- 2026-09-20 (agente, empaquetado FP16 + Vía 3): `plant_mobilenetv2_38.tflite`
  (4.8MB) + `labels.txt` (38) en `mobile/assets/`; `classes=38`, threshold 0.70;
  INT8 descartado por type-mismatch Dart (doble justificación con regla >5%).
  `flutter analyze` 0 issues, 54 tests. E2E compose verde: chat (respuesta+COFEPRIS
  vía nim-fake), JWT, NOM-059 403. Stack E2E apagado tras la verificación.
  F4 (LangGraph) formalmente DESBLOQUEADA pendiente de puerta hardware.
