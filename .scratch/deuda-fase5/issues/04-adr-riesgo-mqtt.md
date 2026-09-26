# Issue 04: ADR riesgo MQTT + precondiciones Fase 2

Status: ready-for-human
Sev: P0-doc · Área: infra · Fase: B

## Evidencia
- `infrastructure/mosquitto/config/mosquitto.conf:19,29-30` `allow_anonymous true`
  global (cubre 1883 y 8883); comentario documenta Fase 2 (release coordinado
  firmware + `mqtt_local_subscriber.py`).

## Problema
No es fix inmediato (cerrarlo hoy rompe la flota), es riesgo sin acta formal.

## Aceptación
- ADR en `docs/adr/` que autorice el riesgo hasta Fase 2 con precondiciones:
  `password_file` + `allow_anonymous false` por-listener + credenciales en flota.
- Sin cambios de config en este issue.

## Compliance
Guardrail TLS documentado como excepción temporal con dueño y fecha.

## Comments
(none)
