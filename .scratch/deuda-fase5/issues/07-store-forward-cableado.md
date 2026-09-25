# Issue 07: Cablear Store&Forward (offline_buffer_push muerto)

Status: ready-for-agent
Sev: P0-funcional · Área: firmware · Fase: C

## Evidencia
- `state_machine.c:158-163` `act_buffer_sample` solo `buffered_count++`, nunca
  `offline_buffer_push`; el símbolo solo se usa en `tests/test_offline_buffer.c`.
- Eventos `EV_CREDS_SAVED/EV_SENSOR_FAIL/EV_RECONNECT_EXCEEDED/EV_WIFI_RESTORED/
  EV_DEEP_SLEEP_WAKE` sin emisor (`state_machine.c:231` "no lo emite nadie hoy").

## Problema
Viola guardrail AGENTS.md (SQLite/Store&Forward ante fallo); pérdida de datos rural.

## Aceptación
- `act_buffer_sample` → `offline_buffer_push` real + drenado en `act_drain_and_sleep`
  (ya existe) + política de capacidad llena (drop-oldest con contador).
- Tests host del path buffer→drain; build esp32 verde.

## Compliance
Guardrail Store&Forward (AGENTS.md).

## Comments
(none)
