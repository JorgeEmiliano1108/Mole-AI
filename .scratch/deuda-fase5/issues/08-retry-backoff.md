# Issue 08: Cablear retry/backoff o eliminar config muerta

Status: ready-for-agent
Sev: P1 · Área: firmware · Fase: C

## Evidencia
- `main.c:656-657` `t_cfg.retry_max=3, retry_backoff_base_ms=2000` seteados;
  `transport_layer.c:129-204` jamás lee esos campos (cero lecturas en `.c`).
- `:184-186` `429 → TRANSPORT_ERROR` con comentario "caller should backoff", sin
  `vTaskDelay`/reintento interno.

## Problema
Config defensiva-sin-efecto; riesgo de saturación RF/backend ante 429/5xx.

## Aceptación
- `transport_send/connect` implementa reintentos con backoff+jiitter desde `t_cfg`
  (429/5xx y timeouts), o se eliminan los campos de `transport_config.h:42-43`.
- Build esp32 verde; test host del backoff si se implementa.

## Compliance
Eficiencia RF (IFT-016): no saturar el medio ante errores.

## Comments
(none)
