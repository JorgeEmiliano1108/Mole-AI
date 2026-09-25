# Issue 12: Job CI para firmware ESP32 + archivar LEGACY

Status: ready-for-agent
Sev: P1 · Área: CI · Fase: D

## Evidencia
- `.github/workflows/system-tests.yml` + `secret-scan.yml`: cero jobs `idf.py`;
  build solo manual (`correr_esp32.md:7`).
- Ambigüedad de target ya mordió una vez (s3 compilado, placa esp32):
  `sdkconfig.old:343-347` TARGET esp32s3 vs `dependencies.lock:31` esp32 vs
  `LEGACY/platformio..ini` (typo doble punto) `esp32dev/arduino`.

## Problema
El firmware nunca se valida en CI; el target depende de la máquina local.

## Aceptación
- Workflow `firmware-build.yml`: `set-target esp32` + `idf.py build` en runner con
  IDF (o docker `espressif/idf`), gate en verde.
- Archivar `sdkconfig.old` y `LEGACY/` fuera del árbol (o `.gitignore` + nota).
- `sdkconfig.defaults` como única fuente versionada de config.

## Compliance
Reproducibilidad del binario de campo.

## Comments
(none)
