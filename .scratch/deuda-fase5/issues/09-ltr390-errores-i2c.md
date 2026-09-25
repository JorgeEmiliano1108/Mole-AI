# Issue 09: Propagar errores I2C en LTR390

Status: ready-for-agent
Sev: P1 · Área: firmware · Fase: C

## Evidencia
- `components/sensor_ltr390/sensor_ltr390.c:71` `read_reg` ignorado en `read_20bit`;
  `:92` PART_ID ignorado; `:100-101` `write_reg(GAIN/MEAS)` ignorados;
  `:115,119,120,124,127,128` ignorados en init/read (`-1.0f`/basura indistinguible).

## Problema
Fallo I2C silencioso → `lux/uv` fantasma aguas abajo.

## Aceptación
- Cada `read/write_reg` chequea `esp_err_t`; fallo → `ESP_ERR_*` al llamador
  (bits de `ambient_valid` apagados, `dg` real).
- Build esp32 verde; host tests no afectados (driver no cubierto en host).

## Compliance
Integridad del dato (bits de validez honestos).

## Comments
(none)
