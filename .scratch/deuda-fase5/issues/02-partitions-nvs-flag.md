# Issue 02: Alinear partitions.csv (flag `encrypted` inerte)

Status: ready-for-agent
Sev: P0 · Área: firmware · Fase: A

## Evidencia
- `microservices/esp32_node/partitions.csv:6` partición `nvs … encrypted` + comentario
  "Includes encrypted NVS (Zero-Trust)", pero `sdkconfig.defaults:11-15`
  `# CONFIG_NVS_ENCRYPTION is not set` y la app usa `nvs_flash_init()` plano.

## Problema
Flag sin backend HW = estado incoherente; confunde el threat model y fragiliza el boot.

## Aceptación
- Quitar flag `encrypted` de la partición `nvs`; actualizar comentario (cifrado off,
  path producción = `nvs_flash_secure_init` + eFuse, ver issue 18).
- Conservar partición `nvs_keys` (4 KB) reservada con comentario, sin churn de offsets.
- `idf.py build` esp32 verde; boot sin cambios (verificado en monitor si hay placa).

## Compliance
Honestidad del threat model; sin regresión de seguridad (el cifrado nunca estuvo activo).

## Comments
(none)
