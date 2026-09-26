# ADR-0007: Riesgo MQTT con `allow_anonymous` hasta Fase 2

- **Fecha:** 2026-09-26
- **Estado:** Aceptado (riesgo temporal con dueño y precondiciones)
- **Contexto:** `infrastructure/mosquitto/config/mosquitto.conf:19,29-30` fija `allow_anonymous true`
  global (cubre listener 1883 plano y 8883 TLS). La flota ESP32 y `edge_node/mqtt_local_subscriber.py`
  hablan 1883 anónimo en texto plano. Cerrar/auth hoy rompería la ingesta local sin release
  coordinado de firmware. Viola el guardrail "telemetría solo con TLS" (AGENTS.md) de forma acotada
  a red local de laboratorio.
- **Decisión:** Se autoriza el riesgo hasta Fase 2 con estas precondiciones de cierre (todas o ninguna):
  1. `password_file` + `allow_anonymous false` por-listener (1883 con auth, 8883 con auth+TLS).
  2. Credenciales provisionadas en la flota (vía FEE1/captive, nunca hardcodeadas).
  3. `mqtt_local_subscriber.py` migrado a 8883 con CA.
  Issue de seguimiento: `.scratch/deuda-fase5/issues/04-adr-riesgo-mqtt.md` (este acta lo cierra
  como documentación; el fix vive en Fase 2).
- **Consecuencias:** El broker local sigue sin auth; prohibido exponer 1883/8883 fuera de LAN de
  laboratorio; cualquier staging con red compartida exige adelantar Fase 2.
- **Cumplimiento:** `enforce-compliance` (excepción temporal documentada, no silencio); LFPDPPP: por
  MQTT local solo transita telemetría de nodo (sin PII de usuarios).
