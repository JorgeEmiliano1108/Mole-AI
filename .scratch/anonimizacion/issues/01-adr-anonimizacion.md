# 01: B1: Redactar ADR — Esquema HMAC para datasets de entrenamiento

Status: ready-for-human

## Requisito

Documentar la decisión de usar HMAC-SHA256 con llave rotable, la separación entre DB transaccional y tabla espejo, y el proceso de rotación de llaves.

## Acceptance criteria

- [ ] Archivo `docs/adr/0012-anonimizacion-datasets-entrenamiento.md`.
- [ ] Justificación del cambio de SHA-256 sin sal a HMAC.
- [ ] Procedimiento de rotación de `ANONIMIZACION_KEY`.
- [ ] Aprobación humana.

## Blocked by

None — can start immediately.

## Notas

Status `ready-for-human` porque define el esquema criptográfico.

