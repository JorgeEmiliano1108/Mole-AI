# Issue 14: Healthchecks + depends_on healthy

Status: ready-for-agent
Sev: P2 · Área: infra · Fase: D

## Evidencia
- Sin healthcheck: `redis:145-152`, `mqtt_broker:155-166`, `ms1/2/3:193-241`,
  `prometheus:288-303`; `disable: true` en celery-worker/beat (`:90-91,114-115`)
  y mqtt-listener (`:139-140`).
- `depends_on: service_started` (redis/mqtt) en vez de `healthy`.

## Problema
Arranques con race; fallos silenciosos de dependencias.

## Aceptación
- Healthchecks reales (redis-cli ping, mosquitto_sub, http MS, pg_isready donde falte);
  quitar `disable: true`; `depends_on` con `condition: service_healthy`.
- `compose up` limpio verificado con `verify-staging.sh`.

## Compliance
Disponibilidad del stack local/staging.

## Comments
(none)
