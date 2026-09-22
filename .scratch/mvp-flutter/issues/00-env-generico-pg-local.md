# 00 — Variables genéricas + PostgreSQL local

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Renombrar `.env` a variables genéricas (dominio + tecnicismo neutro en comentarios),
manteniendo legacy como fallback 1 release; migrar a PostgreSQL local
(`postgres:5432/mole_dev` del compose); `EDGE_SYNC_URL` canónico edge-batch (ADR-0002).

## Acceptance criteria

- [x] `.env` genérico (`DB_*, OBJECT_STORAGE_*, IDP_*, LLM_*, EDGE_*`) + backup `.env.bak`
- [x] `.env.production.template` público sin secretos
- [x] `settings.py`: `_env_first` + `_resolve_db_url` (DSN → partes con quote → sqlite)
- [x] MS chat/vision (`AliasChoices`) + report (`from_env`) + `store_forward_daemon` con fallback legacy
- [x] `docker-compose.yml`: postgres ← `DB_*`, healthcheck `$$`, edge → `edge-batch`
- [x] `tests/test_settings_env_generic.py`: 7/7 verde (incluye fix `quote(safe='')` y fail-fast IDP)
- [x] MS: visión 51 passed, chat 115 passed + 10 skipped, report 26 passed + 6 failed pre-existentes
- [x] E2E `tests/system/`: jwt + nom059 + chat en verde
- [x] Django: baseline HEAD = 0 tests (crash `ModuleNotFoundError` en setup); rama = 55 ejecutables

## Blocked by

None - can start immediately

## Comments

- 2026-09-08 (agente): skills `enforce-compliance` (Fase 1-4), `tdd` (RED→GREEN en settings),
  `diagnose` (4 hipótesis verificadas: leakage load_dotenv, fail-fast triple, quote `/`,
  `dj_database_url` con `DATABASE_URL=""`), `improve-codebase-architecture` (seam env único).
- Hallazgos colaterales (pre-existentes, no del slice): `ALLOWED_HOSTS` vs `DJANGO_ALLOWED_HOSTS`
  (corregido con fallback), `DATABASE_URL` placeholder truthy (resuelto con `_resolve_db_url`),
  `useradd` duplicado + `chown` en `mole_report/Dockerfile` (corregido), healthcheck compose
  sin escapar `$$` (corregido), `DJANGO_LTK_ENCRYPTION_KEY` ausente del `.env` (añadida),
  `test_device_revocation` importa `UserPlant` de `apps.core` (pendiente Slice 1),
  `test_otel` en paquete equivocado (pendiente Slice 8), 6 failed `test_api_reports` idénticos en HEAD.
- Riesgo abierto: credencial RDS viva en `.env.bak` → rotar en AWS antes de borrar el backup.
- Pendiente: frontend `vitest` (sin node en este host) y E2E con Django incluido.

## Cierre 2026-09-12 — `.env` único + TLS (skills: enforce-compliance, diagnose, tdd)

- 5 mapeos §4 aplicados con fallback legacy: `EDGE_API_KEY→MOLE_AI_API_KEY`
  (settings + pdf_generator), `API_KEY` alias en chat (verificado `wired-check`),
  `MQTT_BROKER_URI`/`MQTT_TLS_ENABLED` (mqtt_listener, default TLS True),
  `MQTT_FIELD_*` (mqtt_local_subscriber), `AI_SERVICE_URL` (settings).
- `.env`: `MQTT_BROKER_URI=mqtt://mqtt_broker:8883`, `MQTT_TLS_ENABLED=True`;
  muertas eliminadas (`MQTT_BROKER_HOST/PORT`, `FASTAPI_URL`→`AI_SERVICE_URL`).
- TLS local: CA Mole.AI regenerada (misma identidad, 825 días) + `server.key` 600
  (relajado a 644 en dev: el broker corre como `mosquitto`) + `server.crt`
  SAN `mqtt_broker/localhost/127.0.0.1`. `ca.crt.bak` conserva la CA anterior.
- Demostración: unit Django 12/12 (9 env + middleware + health + metrics-gap);
  chat 115 passed + 10 skipped tras el alias; visión 51 passed (sin cambios);
  `openssl s_client` cadena `Verify return code: 0`, broker `2.1.2 running` sin
  errores; `test_8883_with_tls_should_succeed` PASSED en red compose;
  E2E sistema jwt + nom059 + chat en verde.
- Riesgo aceptado y documentado: `1883` plano sigue abierto (tests RED 1 y 3 del
  archivo pendientes a propósito) para la flota ESP32 legacy; cierre fase 2 con
  `allow_anonymous false` + credenciales por dispositivo. `mqtt_broker` queda
  corriendo; stack E2E apagado.
- 2026-09-17 (agente): `.env` único global cerrado. Inventario: solo `.env` es leído
  (compose `env_file: ../.env` ×8, Django/edge `load_dotenv`, MS `from_env()`/AliasChoices;
  cero referencias a `.env.bak` o al template en código). Gaps cerrados:
  `AI_SERVICE_URL` añadida a `.env` (primaria según `settings.py:290`), `FASTAPI_URL`
  documentada LEGACY en template. Barrido: toda var leída en código existe en `.env`
  o tiene default seguro (única excepción `SUPABASE_KEY` → `''` para template web legacy).
  Verificado: `test_settings_env_generic` 9 passed, `MOLE_AI_SERVICE_URL` resuelve
  canónico, gate contrato verde. Pendiente usuario: rotar RDS → confirmar → se borra `.env.bak`.
- 2026-09-17 (agente): `.env` único literal. Eliminados `.env.bak` (tras verificación
  de cero referencias en código; su password RDS viva queda pendiente de rotación en
  AWS por el usuario) y `.env.production.template` (decisión usuario: un solo archivo).
  README actualizado (quickstart sin `cp` de template; onboarding vía secrets manager).
  `clean_secrets.py` sin punteros colgantes. Verificado: env 9 passed, gate contrato
  verde, ruff limpio, `find` confirma único `./.env`.
